import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, ANY

from app.core.config import get_settings
from app.rag.service import RagService
from app.evaluation.phase3f_runner import Phase3FRunner
from app.evaluation.datasets import GoldenCase
from app.rag.prompts import GROUNDED_ABSTENTION

@pytest.fixture
def mock_settings():
    settings = get_settings()
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
async def test_3f_runner_generates_and_evaluates_incorrect_abstention(mock_settings, dummy_benchmark_cases):
    # Tests G (Answerable Regression) and B (Incorrect Abstention)
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

    with patch("app.evaluation.runner.evaluate") as mock_eval:
        mock_result = MagicMock()

        # Test case 1 is answerable, so it gets deep-eval'ed.
        res1 = MagicMock()
        res1.input = "What is X?"
        res1.expected_output = "X is Y."
        res1.actual_output = "Generated Answer"
        res1.success = None

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

        # Case 1 (answerable) - Answerable Regression
        c1 = next(c for c in cases if c["case_id"] == "test-case-1")
        assert c1["status"] == "EVALUATED"
        assert c1["metrics"]["Faithfulness"]["score"] == 0.95
        assert c1["metrics"]["Faithfulness"]["success"] == "PENDING_OD_1"

        # Case 2 (unanswerable) - Incorrect Abstention
        c2 = next(c for c in cases if c["case_id"] == "test-case-unanswerable")
        assert c2["status"] == "ABSTENTION_EVALUATED"
        assert c2["correctly_abstained"] is False
        assert c2["abstention_score"] == 0.0
        assert "metrics" not in c2 or len(c2.get("metrics", {})) == 0

        # Stratification grouping
        stats = report["stratified_statistics"]
        assert "question_type=factual" in stats
        assert "question_type=abstention" not in stats

        # Factual has Faithfulness score 0.95
        assert stats["question_type=factual"]["Faithfulness"]["average_score"] == 0.95

        # Check Abstention Report
        abstention = report["abstention"]
        assert abstention["total_unanswerable"] == 1
        assert abstention["correctly_abstained_count"] == 0
        assert abstention["accuracy"] == 0.0
        assert abstention["formula"] == "exact_canonical_match"


@pytest.mark.asyncio
async def test_3f_unanswerable_correct_abstention_and_whitespace(mock_settings, dummy_benchmark_cases):
    # Tests A (Correct Abstention), E (Whitespace Behavior), F (No DeepEval)
    mock_rag = AsyncMock(spec=RagService)

    class DummyDoc:
        def __init__(self, name):
            self.metadata = {"source_name": name, "source_id": "doc1"}
            self.page_content = "content"

    class DummyItem:
        def __init__(self, name):
            self.document = DummyDoc(name)

    # RAG response is preserved, with whitespace (TEST E)
    mock_rag.answer_with_context.return_value = (f"  \n\t{GROUNDED_ABSTENTION}  ", [DummyItem("doc1.pdf")])

    runner = Phase3FRunner(mock_settings, mock_rag)

    # Just the unanswerable case
    unanswerable_case = [dummy_benchmark_cases[1]]

    with patch("app.evaluation.runner.evaluate") as mock_eval:
        report = await runner.run(unanswerable_case, stratify_by=[])

        # DeepEval evaluation is NOT invoked (TEST F)
        mock_eval.assert_not_called()

        cases = report["case_reports"]
        assert len(cases) == 1
        c1 = cases[0]

        assert c1["case_id"] == "test-case-unanswerable"
        assert c1["status"] == "ABSTENTION_EVALUATED"
        assert c1["actual_output"] == f"  \n\t{GROUNDED_ABSTENTION}  "
        assert c1["correctly_abstained"] is True
        assert c1["abstention_score"] == 1.0

        # Check Abstention Report
        abstention = report["abstention"]
        assert abstention["total_unanswerable"] == 1
        assert abstention["correctly_abstained_count"] == 1
        assert abstention["accuracy"] == 1.0


@pytest.mark.asyncio
async def test_3f_unanswerable_generation_failure(mock_settings, dummy_benchmark_cases):
    # Tests C (Generation Failure)
    mock_rag = AsyncMock(spec=RagService)

    # Exception during generation
    mock_rag.answer_with_context.side_effect = Exception("Test Exception")

    runner = Phase3FRunner(mock_settings, mock_rag)

    unanswerable_case = [dummy_benchmark_cases[1]]

    with patch("app.evaluation.runner.evaluate") as mock_eval:
        report = await runner.run(unanswerable_case, stratify_by=[])

        mock_eval.assert_not_called()

        cases = report["case_reports"]
        assert len(cases) == 1
        c1 = cases[0]

        assert c1["case_id"] == "test-case-unanswerable"
        assert c1["status"] == "GENERATION_ERROR"
        assert c1["actual_output"] is None
        assert c1["correctly_abstained"] is False
        assert c1["abstention_score"] == 0.0

        abstention = report["abstention"]
        assert abstention["total_unanswerable"] == 1
        assert abstention["correctly_abstained_count"] == 0
        assert abstention["accuracy"] == 0.0


@pytest.mark.asyncio
async def test_3f_runner_zero_denominator(mock_settings, dummy_benchmark_cases):
    # Tests D (Zero Denominator)
    mock_rag = AsyncMock(spec=RagService)

    class DummyDoc:
        def __init__(self, name):
            self.metadata = {"source_name": name, "source_id": "doc1"}
            self.page_content = "content"

    class DummyItem:
        def __init__(self, name):
            self.document = DummyDoc(name)

    mock_rag.answer_with_context.return_value = ("Generated Answer", [DummyItem("doc1.pdf")])

    runner = Phase3FRunner(mock_settings, mock_rag)

    # Just the answerable case
    answerable_case = [dummy_benchmark_cases[0]]

    with patch("app.evaluation.runner.evaluate") as mock_eval:
        mock_result = MagicMock()
        res1 = MagicMock()
        res1.input = "What is X?"
        res1.expected_output = "X is Y."
        res1.actual_output = "Generated Answer"
        res1.success = None
        res1.metrics_data = []
        mock_result.test_results = [res1]
        mock_eval.return_value = mock_result

        report = await runner.run(answerable_case, stratify_by=[])

        cases = report["case_reports"]
        assert len(cases) == 1

        abstention = report["abstention"]
        assert abstention["total_unanswerable"] == 0
        assert abstention["correctly_abstained_count"] == 0
        assert abstention["accuracy"] is None
        assert abstention["formula"] == "exact_canonical_match"
