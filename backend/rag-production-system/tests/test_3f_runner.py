import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, ANY

from app.core.config import get_settings
from app.rag.service import RagService
from app.evaluation.phase3f_runner import Phase3FRunner
from app.evaluation.datasets import GoldenCase

@pytest.fixture
def mock_settings():
    settings = get_settings()
    # Dummy credentials so judge building succeeds
    settings.eval_deepseek_api_key = "dummy"
    settings.eval_sambanova_api_key = "dummy"
    return settings


@pytest.fixture
def dummy_benchmark_cases():
    return [
        {
            "case_id": "test-case-1",
            "question": "What is X?",
            "expected_answer": "X is Y.",
            "answerability": "answerable",
            "question_type": "factual",
            "topics": ["topic1"],
            "source": {
                "source_name": "doc1.pdf",
                "source_id": "doc1",
                "document_hash": "hash1",
                "document_type": "general",
                "type_confidence": 1.0
            },
            "retrieval_profile": {
                "evidence_scope": "single_span",
                "corpus_position": "start",
                "distractor_profile": "none",
                "retrieval_risk": "low"
            },
            "evidence": [],
            "claims": [],
            "verification": {"verdict": "accepted", "primary": {"verdict": "accepted", "claims_checked": []}},
            "version": {"schema_version": "v1", "benchmark_version": "v1"}
        },
        {
            "case_id": "test-case-unanswerable",
            "question": "What is Z?",
            "expected_answer": "I don't know.",
            "answerability": "unanswerable",
            "question_type": "abstention",
            "topics": [],
            "source": {
                "source_name": "doc1.pdf",
                "source_id": "doc1",
                "document_hash": "hash1",
                "document_type": "general",
                "type_confidence": 1.0
            },
            "retrieval_profile": {
                "evidence_scope": "single_span",
                "corpus_position": "start",
                "distractor_profile": "none",
                "retrieval_risk": "high"
            },
            "evidence": [],
            "claims": [],
            "verification": {"verdict": "accepted", "primary": {"verdict": "accepted", "claims_checked": []}},
            "version": {"schema_version": "v1", "benchmark_version": "v1"}
        }
    ]

@pytest.mark.asyncio
async def test_3f_runner_generates_and_evaluates(mock_settings, dummy_benchmark_cases):
    mock_rag = AsyncMock(spec=RagService)
    
    class DummyDoc:
        def __init__(self, name):
            self.metadata = {"source_name": name, "source_id": "doc1"}
            self.page_content = "content"
            
    class DummyItem:
        def __init__(self, name):
            self.document = DummyDoc(name)
            
    # Always return actual_output and matched source
    mock_rag.answer_with_context.return_value = ("Generated Answer", [DummyItem("doc1.pdf")])

    runner = Phase3FRunner(mock_settings, mock_rag)
    
    # We patch evaluate to avoid live calls.
    with patch("app.evaluation.runner.evaluate") as mock_eval:
        mock_result = MagicMock()
        
        # Test case 1 is answerable, so it gets deep-eval'ed.
        # Test case 2 is unanswerable, so it gets PENDING_POLICY immediately without DeepEval.
        res1 = MagicMock()
        res1.input = "What is X?"
        res1.expected_output = "X is Y."
        res1.actual_output = "Generated Answer"
        res1.success = None # OD #1 threshold=None causes success=None
        
        # Mock metrics data
        m1 = MagicMock()
        m1.name = "Faithfulness"
        m1.score = 0.95
        m1.success = None
        
        m2 = MagicMock()
        m2.name = "Answer Relevancy"
        m2.score = 0.8
        m2.success = None
        
        res1.metrics_data = [m1, m2]
        mock_result.test_results = [res1]
        mock_eval.return_value = mock_result
        
        report = await runner.run(dummy_benchmark_cases, stratify_by=["question_type"])
        
        # Verifications
        assert report["job_id"] == "3f-run"
        assert report["confidence_interval"] == "PENDING_OD_3"
        
        cases = report["case_reports"]
        assert len(cases) == 2
        
        # Case 1 (answerable)
        c1 = next(c for c in cases if c["case_id"] == "test-case-1")
        assert c1["status"] == "EVALUATED"
        assert c1["metrics"]["Faithfulness"]["score"] == 0.95
        assert c1["metrics"]["Faithfulness"]["success"] == "PENDING_OD_1"
        
        # Case 2 (unanswerable)
        c2 = next(c for c in cases if c["case_id"] == "test-case-unanswerable")
        assert c2["status"] == "PENDING_POLICY"
        assert c2["metrics"]["Faithfulness"]["score"] is None
        assert c2["metrics"]["Faithfulness"]["success"] == "PENDING_POLICY"
        
        # Stratification grouping
        stats = report["stratified_statistics"]
        assert "question_type=factual" in stats
        assert "question_type=abstention" not in stats
        
        # Factual has Faithfulness score 0.95
        assert stats["question_type=factual"]["Faithfulness"]["average_score"] == 0.95
        
        # Test custom job_id
        custom_report = await runner.run(
            dummy_benchmark_cases,
            stratify_by=["question_type"],
            job_id="smoke-2026-09-08"
        )
        assert custom_report["job_id"] == "smoke-2026-09-08"
            
    # Verify exact threshold=None passed to metrics
    with patch("app.evaluation.phase3f_runner.FaithfulnessMetric") as mock_fm:
        # Just mock one to ensure it's called with None
        mock_instance = MagicMock()
        mock_fm.return_value = mock_instance
        with patch("app.evaluation.runner.evaluate") as mock_eval_2:
            mock_eval_2.return_value.test_results = []
            await runner.run(dummy_benchmark_cases, stratify_by=[])
        mock_fm.assert_called_with(threshold=None, model=ANY)

@pytest.mark.asyncio
async def test_3f_unanswerable_real_metrics(mock_settings):
    """
    Focused regression test using REAL instantiated DeepEval metric objects.
    Proves that an unanswerable case reaches OD #2 branch, RAG response is preserved,
    DeepEval is NOT invoked, and all real metric names are present with PENDING_POLICY.
    """
    mock_rag = AsyncMock(spec=RagService)
    
    class DummyDoc:
        def __init__(self, name):
            self.metadata = {"source_name": name, "source_id": "doc1"}
            self.page_content = "content"
            
    class DummyItem:
        def __init__(self, name):
            self.document = DummyDoc(name)
            
    # RAG response is preserved
    mock_rag.answer_with_context.return_value = ("I cannot answer this.", [DummyItem("doc1.pdf")])

    runner = Phase3FRunner(mock_settings, mock_rag)
    
    unanswerable_case = [{
        "case_id": "real-unanswerable",
        "question": "What is Z?",
        "expected_answer": "I don't know.",
        "answerability": "unanswerable",
        "question_type": "abstention",
        "topics": [],
        "source": {
            "source_name": "doc1.pdf",
            "source_id": "doc1",
            "document_hash": "hash1",
            "document_type": "general",
            "type_confidence": 1.0
        },
        "retrieval_profile": {
            "evidence_scope": "single_span",
            "corpus_position": "start",
            "distractor_profile": "none",
            "retrieval_risk": "high"
        },
        "evidence": [],
        "claims": [],
        "verification": {"verdict": "accepted", "primary": {"verdict": "accepted", "claims_checked": []}},
        "version": {"schema_version": "v1", "benchmark_version": "v1"}
    }]

    with patch("app.evaluation.runner.evaluate") as mock_eval:
        report = await runner.run(unanswerable_case, stratify_by=[])
        
        # DeepEval evaluation is NOT invoked
        mock_eval.assert_not_called()
        
        cases = report["case_reports"]
        assert len(cases) == 1
        c1 = cases[0]
        
        assert c1["case_id"] == "real-unanswerable"
        assert c1["status"] == "PENDING_POLICY"
        assert c1["actual_output"] == "I cannot answer this."
        
        # Verify all four actual metric names
        metrics_dict = c1["metrics"]
        expected_names = [
            "Faithfulness",
            "Answer Relevancy",
            "Contextual Precision",
            "Contextual Recall"
        ]
        
        for name in expected_names:
            assert name in metrics_dict, f"Metric name '{name}' not found in report"
            assert metrics_dict[name]["score"] is None
            assert metrics_dict[name]["success"] == "PENDING_POLICY"

