import copy
import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.language_models.chat_models import BaseChatModel
from app.evaluation.exceptions import UnresolvedPolicyError, BenchmarkAdmissionError
from app.evaluation.verifier_v3 import (
    Phase3CVerifier,
    IntermediateVerificationResult,
    VerificationBatchOutput,
    ClaimVerification,
    SupportStatus
)
from app.evaluation.enrichment import CorpusEnricher
from app.evaluation.aggregator import CaseAggregator
from app.evaluation.orchestrator import Phase3DOrchestrator
from app.core.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        chat_provider="groq",
        groq_api_key="test",
        eval_deepseek_api_key="test",
        eval_sambanova_api_key="test",
        phase3_unsupported_ratio_threshold=0.5
    )

@pytest.mark.asyncio
async def test_3d_orchestrator_wiring(mock_settings):
    """
    Test the Phase 3D orchestrator pipeline wiring using the actual 3C Verifier.
    Must prove:
    1. A valid mocked PartialBenchmarkCandidate can enter the pipeline.
    2. No real LLM/API call occurs (the structured_llm boundary is mocked).
    3. The existing 3C verifier boundary is respected and executed.
    4. UnresolvedPolicyError is caught correctly from verifier.
    5. IntermediateVerificationResult is extracted correctly.
    6. The result reaches CaseAggregator.
    7. The CaseAggregator applies OD #10 policy and returns the completed result.
    8. The original candidate is not silently mutated.
    """
    candidate = {
        "case_id": "test_case",
        "question": "test question",
        "answerability": "answerable",
        "expected_answer": "test expected",
        "verification": {
            "verdict": None,
            "verified_by": [],
            "unsupported_claims": [],
            "contradictions": [],
            "reason": None
        },
        "retrieval_profile": {
            "evidence_scope": "single_span",
            "corpus_position": "start"
        },
        "claims": [
            {
                "claim_id": "c1",
                "claim": "The sky is blue",
                "evidence_ids": ["e1"]
            }
        ],
        "evidence": [
            {
                "evidence_id": "e1",
                "quote": "The sky is indeed blue."
            }
        ]
    }

    original_candidate = copy.deepcopy(candidate)

    mock_llm = MagicMock(spec=BaseChatModel)
    verifier = Phase3CVerifier(llm=mock_llm)

    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = VerificationBatchOutput(
        results=[
            ClaimVerification(
                claim_id="c1",
                support_status=SupportStatus.SUPPORTED,
                reason="Because the evidence says so."
            )
        ]
    )
    verifier.structured_llm = mock_structured_llm

    aggregator = CaseAggregator(settings=mock_settings, secondary_verifier=AsyncMock())

    enricher = CorpusEnricher()
    orchestrator = Phase3DOrchestrator(verifier=verifier, enricher=enricher, aggregator=aggregator)

    result = await orchestrator.run_pipeline(candidate)

    assert isinstance(result, IntermediateVerificationResult)
    verification = result.partial_case_dict["verification"]
    assert verification["verdict"] == "accepted"
    assert verification["primary"]["verdict"] == "accepted"
    assert verification["primary"]["claims_checked"] == ["c1"]

    assert candidate == original_candidate
    mock_structured_llm.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_3d_orchestrator_verifier_returns_normally(mock_settings):
    """
    Test that if the verifier returns normally, the orchestrator raises a RuntimeError.
    """
    mock_verifier = MagicMock(spec=Phase3CVerifier)

    async def mock_verify(c):
        return None

    mock_verifier.verify_candidate = mock_verify

    enricher = CorpusEnricher()
    aggregator = CaseAggregator(settings=mock_settings, secondary_verifier=AsyncMock())
    orchestrator = Phase3DOrchestrator(verifier=mock_verifier, enricher=enricher, aggregator=aggregator)

    with pytest.raises(RuntimeError, match="Verifier returned normally"):
        await orchestrator.run_pipeline({})

@pytest.mark.asyncio
async def test_3d_orchestrator_verifier_raises_without_partial_result(mock_settings):
    """
    Test that if UnresolvedPolicyError is raised without a partial_result, it is caught and wrapped.
    """
    mock_verifier = MagicMock(spec=Phase3CVerifier)

    async def mock_verify(c):
        raise UnresolvedPolicyError("Mocked error without partial_result")

    mock_verifier.verify_candidate = mock_verify

    enricher = CorpusEnricher()
    aggregator = CaseAggregator(settings=mock_settings, secondary_verifier=AsyncMock())
    orchestrator = Phase3DOrchestrator(verifier=mock_verifier, enricher=enricher, aggregator=aggregator)

    with pytest.raises(RuntimeError, match="UnresolvedPolicyError did not contain IntermediateVerificationResult"):
        await orchestrator.run_pipeline({})

@pytest.mark.asyncio
async def test_3d_orchestrator_handoff(mock_settings):
    """
    Proves the exact handoff chain:
    Phase3CVerifier -> CorpusEnricher -> CaseAggregator.
    Proves the intermediate result reaching CaseAggregator is the one produced by the enricher.
    """
    candidate = {"case_id": "handoff_test"}

    initial_result = IntermediateVerificationResult(
        partial_case_dict=candidate, claims_checked=["c1"], unsupported_claims=[]
    )
    mock_verifier = MagicMock(spec=Phase3CVerifier)
    async def mock_verify(c):
        raise UnresolvedPolicyError("From verifier", partial_result=initial_result)
    mock_verifier.verify_candidate = mock_verify

    enriched_result = IntermediateVerificationResult(
        partial_case_dict={"case_id": "handoff_test", "enriched": True},
        claims_checked=["c1"], unsupported_claims=[]
    )
    mock_enricher = MagicMock(spec=CorpusEnricher)
    def mock_enrich(res):
        assert res is initial_result # Proves Verifier output reaches Enricher
        raise UnresolvedPolicyError("From enricher", partial_result=enriched_result)
    mock_enricher.enrich = MagicMock(side_effect=mock_enrich)

    mock_aggregator = MagicMock(spec=CaseAggregator)
    async def mock_aggregate(res):
        assert res is enriched_result # Proves Enricher output reaches Aggregator
        return "Final Result"
    mock_aggregator.aggregate = AsyncMock(side_effect=mock_aggregate)

    orchestrator = Phase3DOrchestrator(
        verifier=mock_verifier, enricher=mock_enricher, aggregator=mock_aggregator
    )

    result = await orchestrator.run_pipeline(candidate)

    assert result == "Final Result"
    mock_enricher.enrich.assert_called_once_with(initial_result)
    mock_aggregator.aggregate.assert_called_once_with(enriched_result)

@pytest.mark.asyncio
async def test_3d_orchestrator_benchmark_admission_error_propagation(mock_settings):
    """
    Proves that a candidate without authoritative corpus_position causes
    BenchmarkAdmissionError to propagate out of run_pipeline().
    Proves CaseAggregator is NOT invoked.
    Proves the exception reaches the caller unchanged.
    """
    candidate = {"case_id": "admission_test"}
    initial_result = IntermediateVerificationResult(
        partial_case_dict=candidate, claims_checked=["c1"], unsupported_claims=[]
    )

    mock_verifier = MagicMock(spec=Phase3CVerifier)
    async def mock_verify(c):
        raise UnresolvedPolicyError("From verifier", partial_result=initial_result)
    mock_verifier.verify_candidate = mock_verify

    mock_enricher = MagicMock(spec=CorpusEnricher)
    mock_enricher.enrich.side_effect = BenchmarkAdmissionError("Missing corpus_position")

    mock_aggregator = MagicMock(spec=CaseAggregator)

    orchestrator = Phase3DOrchestrator(
        verifier=mock_verifier, enricher=mock_enricher, aggregator=mock_aggregator
    )

    with pytest.raises(BenchmarkAdmissionError, match="Missing corpus_position"):
        await orchestrator.run_pipeline(candidate)

    mock_enricher.enrich.assert_called_once_with(initial_result)
    mock_aggregator.aggregate.assert_not_called()
