from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows legacy console fix: DeepEval uses Rich which tries to print emoji
# (e.g. ✨) via LegacyWindowsTerm. On cp1252 terminals this raises
# UnicodeEncodeError. Forcing utf-8 stdout encoding and disabling Rich color
# prevents the crash without affecting evaluation logic.
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("NO_COLOR", "1")

import pandas as pd

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig, ErrorConfig
from deepeval.evaluate.configs import CacheConfig
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

from app.core.config import Settings
from app.evaluation.datasets import load_golden_cases
from app.evaluation.judges import build_judge
from app.rag.service import RagService

logger = logging.getLogger(__name__)

# Hard safety cap for benchmark usage.
MAX_EVALUATION_CASES = 5


def parse_evaluation_report(report_path: Path, job_id: str) -> dict:
    df = pd.read_csv(report_path)
    total_cases = len(df)

    passed_cases = int(df["success"].sum()) if "success" in df.columns else 0

    score_cols = [col for col in df.columns if col.endswith("_score")]
    avg_scores: dict[str, float] = {}

    for col in score_cols:
        metric_name = col[:-6]
        valid_scores = df[col].dropna()
        avg_scores[metric_name] = (
            round(float(valid_scores.mean()), 4)
            if not valid_scores.empty
            else 0.0
        )

    test_cases = []

    for _, row in df.iterrows():
        tc_metrics = {}

        for col in score_cols:
            metric_name = col[:-6]
            score_val = row.get(col)
            passed_val = row.get(f"{metric_name}_passed")
            reason_val = row.get(f"{metric_name}_reason")
            error_val = row.get(f"{metric_name}_error")

            tc_metrics[metric_name] = {
                "name": metric_name,
                "score": float(score_val) if pd.notna(score_val) else None,
                "passed": bool(passed_val) if pd.notna(passed_val) else None,
                "reason": str(reason_val) if pd.notna(reason_val) else None,
                "error": str(error_val) if pd.notna(error_val) else None,
            }

        test_cases.append(
            {
                "question": str(row.get("question", "")),
                "expected_output": (
                    str(row.get("expected_output"))
                    if pd.notna(row.get("expected_output"))
                    else None
                ),
                "actual_output": (
                    str(row.get("actual_output"))
                    if pd.notna(row.get("actual_output"))
                    else None
                ),
                "success": bool(row.get("success", False)),
                "source_match_status": (
                    str(row.get("source_match_status"))
                    if "source_match_status" in row and pd.notna(row.get("source_match_status"))
                    else None
                ),
                "error_type": (
                    str(row.get("error_type"))
                    if "error_type" in row and pd.notna(row.get("error_type"))
                    else None
                ),
                "metrics": tc_metrics,
            }
        )

    return {
        "job_id": job_id,
        "status": "completed",
        "summary": {
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "average_scores": avg_scores,
        },
        "test_cases": test_cases,
    }


class EvaluationRunner:
    def __init__(self, settings: Settings, rag_service: RagService) -> None:
        self.settings = settings
        self.rag_service = rag_service

    async def run(
        self,
        job_id: str,
        judge_override: str | None = None,
        test_file: str | None = None,
        case_limit: int = 5,
    ) -> Path:

        # 1. Load dataset and bound limit.
        all_golden = await asyncio.to_thread(
            load_golden_cases,
            test_file or "data/golden_qa.json",
        )
        limit = max(1, min(case_limit, len(all_golden)))
        golden = all_golden[:limit]

        logger.info(
            "Evaluation benchmark limited to %d test case(s) out of %d.",
            len(golden),
            len(all_golden),
        )

        # 2. Build the DeepEval judge.
        judge = build_judge(self.settings, judge_override)

        metrics = [
            FaithfulnessMetric(
                threshold=self.settings.eval_threshold,
                model=judge,
            ),
            AnswerRelevancyMetric(
                threshold=self.settings.eval_threshold,
                model=judge,
            ),
            ContextualPrecisionMetric(
                threshold=self.settings.eval_threshold,
                model=judge,
            ),
            ContextualRecallMetric(
                threshold=self.settings.eval_threshold,
                model=judge,
            ),
        ]

        # 3. Evaluation answer generation uses DeepSeek via the explicit
        #    evaluation=True path in RagService.answer_with_context().
        #    This path calls _get_evaluation_llm() internally, which is
        #    always DeepSeek — completely independent of self.rag_service.llm
        #    (the normal Groq/Gemini/Ollama chat model).
        #
        #    We do NOT mutate self.rag_service.llm here. That would create
        #    unsafe model-state coupling. The separation is enforced inside
        #    service.py by design.
        test_cases: list[LLMTestCase] = []
        bypassed_cases: list[dict] = []

        for index, case in enumerate(golden):
            session_id = f"eval-{job_id}-{index}"
            logger.info("Generating evaluation answer %d/%d with DeepSeek", index + 1, len(golden))

            try:
                actual_output, retrieved = await self.rag_service.answer_with_context(
                    session_id, case.question, evaluation=True
                )
            except Exception as e:
                logger.error("Generation failed for case %d: %s", index, e)
                bypassed_cases.append({
                    "question": case.question,
                    "expected_output": case.expected_output,
                    "actual_output": None,
                    "success": False,
                    "error_type": "GENERATION_ERROR",
                    "error_reason": str(e)
                })
                continue

            # Source metadata validation
            if case.source:
                matched = False
                for item in retrieved:
                    doc_src = item.document.metadata.get("source_name")
                    doc_id = item.document.metadata.get("source_id")
                    if case.source.source_name and doc_src == case.source.source_name:
                        matched = True
                        break
                    if case.source.source_id and doc_id == case.source.source_id:
                        matched = True
                        break
                
                if not matched:
                    logger.warning("Source mismatch for case %d. Bypassing DeepEval.", index)
                    bypassed_cases.append({
                        "question": case.question,
                        "expected_output": case.expected_output,
                        "actual_output": actual_output,
                        "success": False,
                        "source_match_status": "SOURCE_MISMATCH"
                    })
                    continue

            test_cases.append(
                LLMTestCase(
                    input=case.question,
                    expected_output=case.expected_output,
                    actual_output=actual_output,
                    retrieval_context=[item.document.page_content for item in retrieved],
                )
            )

            if self.settings.eval_throttle_seconds > 0 and index < len(golden) - 1:
                await asyncio.sleep(self.settings.eval_throttle_seconds)

        # 4. Run DeepEval conservatively: one case/metric workload at a time.
        async_config = AsyncConfig(
            run_async=True,
            max_concurrent=1,
            throttle_value=max(
                1,
                int(self.settings.eval_throttle_seconds),
            ),
        )

        logger.info(
            "Running DeepEval on %d test case(s) with max_concurrent=1.",
            len(test_cases),
        )

        if test_cases:
            results = await asyncio.to_thread(
                evaluate,
                test_cases,
                metrics,
                cache_config=CacheConfig(write_cache=False, use_cache=False),
                async_config=async_config,
                error_config=ErrorConfig(ignore_errors=True),
            )
            deep_results = results.test_results
        else:
            deep_results = []

        # 5. Write CSV report.
        records = []

        for result in deep_results:
            row = {
                "question": result.input,
                "expected_output": result.expected_output,
                "actual_output": result.actual_output,
                "success": result.success,
            }
            for metric in result.metrics_data:
                row[f"{metric.name}_score"] = metric.score
                row[f"{metric.name}_passed"] = metric.success
                row[f"{metric.name}_reason"] = metric.reason
                row[f"{metric.name}_error"] = metric.error
            records.append(row)
            
        for bypassed in bypassed_cases:
            records.append(bypassed)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_csv = self.settings.eval_report_dir / f"eval_{timestamp}_{job_id}.csv"
        out_meta = self.settings.eval_report_dir / f"eval_{timestamp}_{job_id}_meta.json"

        pd.DataFrame(records).to_csv(out_csv, index=False)
        
        import json
        meta_data = {
            "job_id": job_id,
            "dataset": test_file or "data/golden_qa.json",
            "cases_evaluated": len(records),
            "generation_model": self.settings.eval_generation_model,
            "judge_model": self.settings.eval_judge,
            "timestamp": timestamp,
        }
        out_meta.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")

        logger.info("Evaluation completed successfully: %s", out_csv)
        return out_csv
