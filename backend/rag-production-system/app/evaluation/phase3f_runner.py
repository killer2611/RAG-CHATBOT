from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Dict, List

from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
)

from app.core.config import Settings
from app.rag.service import RagService
from app.evaluation.datasets import GoldenCase, GoldenSource
from app.evaluation.judges import build_judge
from app.evaluation.runner import EvaluationRunner, _check_source_match

logger = logging.getLogger(__name__)


class Phase3FRunner:
    """
    Isolated execution/reporting path for Phase 3F evaluation.
    This reuses EvaluationRunner primitives (generate_answer, execute_metrics)
    without routing through the Phase 1/2 success/passed_cases aggregation path.
    """

    def __init__(self, settings: Settings, rag_service: RagService) -> None:
        self.settings = settings
        self.rag_service = rag_service
        self.eval_runner = EvaluationRunner(settings, rag_service)

    async def run(
        self,
        cases: List[Dict[str, Any]],
        stratify_by: List[str] | None = None,
        job_id: str = "3f-run",
    ) -> Dict[str, Any]:
        """
        Direct callable mechanism for Phase 3F test and future callers.
        DO NOT expose via CLI/API until OD #8 is resolved.
        """
        stratify_by = stratify_by or []

        judge = build_judge(self.settings)

        # OD #1 Firewall: use threshold=None specifically to prevent
        # threshold-derived success semantics in DeepEval API.
        metric_pairs = [
            ("Faithfulness", FaithfulnessMetric(threshold=None, model=judge)),
            ("Answer Relevancy", AnswerRelevancyMetric(threshold=None, model=judge)),
            ("Contextual Precision", ContextualPrecisionMetric(threshold=None, model=judge)),
            ("Contextual Recall", ContextualRecallMetric(threshold=None, model=judge)),
        ]
        
        # Extract just the instances for evaluate() later
        metrics = [m for _, m in metric_pairs]

        reports: List[Dict[str, Any]] = []
        test_cases_for_deepeval: List[LLMTestCase] = []
        test_case_to_cid: Dict[int, str] = {}
        metadata_map: Dict[str, Dict[str, Any]] = {}

        # 1. Adapter Layer & Generation
        for index, case_data in enumerate(cases):
            cid = case_data["case_id"]
            ans = case_data["answerability"]

            metadata_map[cid] = {
                "answerability": ans,
                "question_type": case_data.get("question_type"),
                "topics": case_data.get("topics"),
                "document_type": case_data.get("source", {}).get("document_type"),
                "retrieval_profile": case_data.get("retrieval_profile"),
            }

            # Adapter: BenchmarkCase -> GoldenCase fields
            golden = GoldenCase(
                question=case_data["question"],
                expected_output=case_data["expected_answer"],
                source=GoldenSource(
                    source_name=case_data["source"]["source_name"],
                    source_id=case_data["source"]["source_id"],
                ),
            )

            session_id = f"eval-3f-{index}"

            try:
                # Reuse primitive: answer_with_context(..., evaluation=True)
                actual_output, retrieved = await self.eval_runner.generate_answer(
                    session_id, golden.question
                )
            except Exception as e:
                logger.error("Generation failed for case %s: %s", cid, e)
                reports.append(
                    {
                        "case_id": cid,
                        "status": "GENERATION_ERROR",
                        "error_reason": str(e),
                        "actual_output": None,
                        "metrics": {},
                    }
                )
                continue

            # OD #2 Firewall: Abstention Routing
            if ans == "unanswerable":
                reports.append(
                    {
                        "case_id": cid,
                        "status": "PENDING_POLICY",
                        "actual_output": actual_output,
                        "metrics": {
                            m_name: {
                                "score": None,
                                "success": "PENDING_POLICY",
                            }
                            for m_name, _ in metric_pairs
                        },
                    }
                )
                continue

            # Source matching validation (Same logic as Phase 1/2)
            if not _check_source_match(golden.source, retrieved):
                reports.append(
                    {
                        "case_id": cid,
                        "status": "SOURCE_MISMATCH",
                        "actual_output": actual_output,
                        "metrics": {},
                    }
                )
                continue

            # Case is fully answerable, matches source, and has an output.
            llm_tc = LLMTestCase(
                input=golden.question,
                expected_output=golden.expected_output,
                actual_output=actual_output,
                retrieval_context=[item.document.page_content for item in retrieved],
            )
            test_cases_for_deepeval.append(llm_tc)
            test_case_to_cid[id(llm_tc)] = cid

            if self.settings.eval_throttle_seconds > 0 and index < len(cases) - 1:
                await asyncio.sleep(self.settings.eval_throttle_seconds)

        # 2. Metric Execution (using shared primitive)
        deep_results = await self.eval_runner.execute_metrics(test_cases_for_deepeval, metrics)

        # 3. Collect Raw Scores
        for tc, result in zip(test_cases_for_deepeval, deep_results):
            cid = test_case_to_cid[id(tc)]
            metric_scores: Dict[str, Any] = {}

            for m_data in result.metrics_data:
                # metric_success is inherently decoupled by threshold=None
                # but we explicitly mark the internal report success as None/PENDING_OD_1.
                metric_scores[m_data.name] = {
                    "score": m_data.score,
                    "success": "PENDING_OD_1",
                }

            reports.append(
                {
                    "case_id": cid,
                    "status": "EVALUATED",
                    "actual_output": tc.actual_output,
                    "metrics": metric_scores,
                }
            )

        # 4. Stratification Grouping
        groups: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

        for rep in reports:
            cid = rep["case_id"]
            meta = metadata_map[cid]

            if not stratify_by:
                group_key = "ALL"
            else:
                vals = []
                for dim in stratify_by:
                    if dim in meta:
                        vals.append(f"{dim}={meta[dim]}")
                    elif dim.startswith("retrieval_profile."):
                        sub = dim.split(".")[1]
                        rp = meta.get("retrieval_profile") or {}
                        vals.append(f"{dim}={rp.get(sub)}")
                    else:
                        vals.append(f"{dim}=UNKNOWN")
                group_key = " | ".join(vals)

            for m_name, m_val in rep.get("metrics", {}).items():
                score = m_val.get("score")
                if score is not None:
                    groups[group_key][m_name].append(score)

        stratified_stats: Dict[str, Dict[str, Any]] = {}
        for g_key, m_dict in groups.items():
            stratified_stats[g_key] = {}
            for m_name, scores in m_dict.items():
                avg = sum(scores) / len(scores) if scores else 0.0
                stratified_stats[g_key][m_name] = {
                    "average_score": round(avg, 4),
                    "count": len(scores),
                }

        # 5. Internal Deterministic Report (not a production contract)
        internal_report = {
            "job_id": job_id,
            "confidence_interval": "PENDING_OD_3",
            "stratified_statistics": stratified_stats,
            "case_reports": reports,
        }
        return internal_report
