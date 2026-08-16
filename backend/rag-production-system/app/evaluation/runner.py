from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

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
from app.evaluation.datasets import load_golden_pairs
from app.evaluation.judges import build_judge
from app.rag.service import RagService

logger = logging.getLogger(__name__)


def parse_evaluation_report(report_path: Path, job_id: str) -> dict:
    df = pd.read_csv(report_path)
    total_cases = len(df)
    passed_cases = int(df["success"].sum()) if "success" in df.columns else 0

    score_cols = [col for col in df.columns if col.endswith("_score")]
    avg_scores: dict[str, float] = {}
    for col in score_cols:
        metric_name = col[:-6]
        valid_scores = df[col].dropna()
        avg_scores[metric_name] = round(float(valid_scores.mean()), 4) if not valid_scores.empty else 0.0

    test_cases = []
    for _, row in df.iterrows():
        tc_metrics = {}
        for col in score_cols:
            m_name = col[:-6]
            score_val = row.get(col)
            passed_val = row.get(f"{m_name}_passed")
            reason_val = row.get(f"{m_name}_reason")
            error_val = row.get(f"{m_name}_error")
            tc_metrics[m_name] = {
                "name": m_name,
                "score": float(score_val) if pd.notna(score_val) else None,
                "passed": bool(passed_val) if pd.notna(passed_val) else None,
                "reason": str(reason_val) if pd.notna(reason_val) else None,
                "error": str(error_val) if pd.notna(error_val) else None,
            }
        test_cases.append({
            "question": str(row.get("question", "")),
            "expected_output": str(row.get("expected_output", "")) if pd.notna(row.get("expected_output")) else None,
            "actual_output": str(row.get("actual_output", "")) if pd.notna(row.get("actual_output")) else None,
            "success": bool(row.get("success", False)),
            "metrics": tc_metrics,
        })

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

    async def run(self, job_id: str, judge_override: str | None = None, test_file: str | None = None) -> Path:
        golden = await asyncio.to_thread(load_golden_pairs, test_file or "data/golden_qa.json")
        judge = build_judge(self.settings, judge_override)
        metrics = [
            FaithfulnessMetric(threshold=self.settings.eval_threshold, model=judge),
            AnswerRelevancyMetric(threshold=self.settings.eval_threshold, model=judge),
            ContextualPrecisionMetric(threshold=self.settings.eval_threshold, model=judge),
            ContextualRecallMetric(threshold=self.settings.eval_threshold, model=judge),
        ]

        test_cases: list[LLMTestCase] = []
        for index, (question, expected) in enumerate(golden):
            session_id = f"eval-{job_id}-{index}"
            actual_output, retrieved = await self.rag_service.answer_with_context(session_id, question)
            test_cases.append(
                LLMTestCase(
                    input=question,
                    expected_output=expected,
                    actual_output=actual_output,
                    retrieval_context=[item.document.page_content for item in retrieved],
                )
            )

        # DeepEval's throttle only applies when run_async=True. Setting concurrency to one
        # plus a delay is intentionally conservative for Gemini quotas and local Ollama RAM.
        async_config = AsyncConfig(
            run_async=True,
            max_concurrent=self.settings.eval_max_concurrent,
            throttle_value=int(self.settings.eval_throttle_seconds),
        )
        results = await asyncio.to_thread(
            evaluate,
            test_cases,
            metrics,
            cache_config=CacheConfig(write_cache=False, use_cache=False),
            async_config=async_config,
            error_config=ErrorConfig(ignore_errors=False),
        )

        records = []
        for result in results.test_results:
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

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = self.settings.eval_report_dir / f"eval_{timestamp}_{job_id}.csv"
        pd.DataFrame(records).to_csv(out, index=False)
        return out
