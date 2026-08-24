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

@pytest.mark.asyncio
async def test_3d_orchestrator_wiring():
    """
    Test the Phase 3D orchestrator pipeline wiring using the actual 3C Verifier.
    Must prove:
    1. A valid mocked PartialBenchmarkCandidate can enter the pipeline.
    2. No real LLM/API call occurs (the structured_llm boundary is mocked).
    3. The existing 3C verifier boundary is respected and executed.
    4. UnresolvedPolicyError is caught correctly.
    5. IntermediateVerificationResult is extracted correctly.
    6. The result reaches CaseAggregator.
    7. The default CaseAggregator raises UnresolvedPolicyError.
    8. No fabricated case-level verdict is produced.
    9. The original candidate is not silently mutated.
    10. The pipeline does not persist an incomplete BenchmarkCase.
    """
    # 1. Valid mocked PartialBenchmarkCandidate
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

    # Store a copy to check for mutation
    original_candidate = copy.deepcopy(candidate)

    # 2. Use real Phase3CVerifier, but mock the LLM boundary
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

    # 3. Create CaseAggregator
    aggregator = CaseAggregator()

    # 4. Create Enricher and Orchestrator
    enricher = CorpusEnricher()
    orchestrator = Phase3DOrchestrator(verifier=verifier, enricher=enricher, aggregator=aggregator)

    # 5. Execute pipeline and assert it raises UnresolvedPolicyError from the aggregator
    with pytest.raises(UnresolvedPolicyError) as exc_info:
        await orchestrator.run_pipeline(candidate)

    # 6. Verify the exception came from CaseAggregator (OD #10)
    assert "Case-level aggregation policy remains unresolved" in str(exc_info.value)

    # Prove the intermediate result was populated by the real 3C verifier
    partial_result = exc_info.value.partial_result
    assert partial_result is not None
    assert partial_result.claims_checked == ["c1"]
    assert partial_result.unsupported_claims == []
    assert partial_result.partial_case_dict["claims"][0]["support_status"] == "supported"

    # 7. Verify the original candidate was not mutated
    assert candidate == original_candidate

    # 8. COST FIREWALL ASSERTION: Prove exactly ONE LLM invocation occurred
    mock_structured_llm.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_3d_orchestrator_verifier_returns_normally():
    """
    Test that if the verifier returns normally, the orchestrator raises a RuntimeError.
    """
    mock_verifier = MagicMock(spec=Phase3CVerifier)

    async def mock_verify(c):
        return None

    mock_verifier.verify_candidate = mock_verify

    enricher = CorpusEnricher()
    aggregator = CaseAggregator()
    orchestrator = Phase3DOrchestrator(verifier=mock_verifier, enricher=enricher, aggregator=aggregator)

    with pytest.raises(RuntimeError, match="Verifier returned normally"):
        await orchestrator.run_pipeline({})

@pytest.mark.asyncio
async def test_3d_orchestrator_verifier_raises_without_partial_result():
    """
    Test that if UnresolvedPolicyError is raised without a partial_result, it is caught and wrapped.
    """
    mock_verifier = MagicMock(spec=Phase3CVerifier)

    async def mock_verify(c):
        raise UnresolvedPolicyError("Mocked error without partial_result")

    mock_verifier.verify_candidate = mock_verify

    enricher = CorpusEnricher()
    aggregator = CaseAggregator()
    orchestrator = Phase3DOrchestrator(verifier=mock_verifier, enricher=enricher, aggregator=aggregator)

    with pytest.raises(RuntimeError, match="UnresolvedPolicyError did not contain IntermediateVerificationResult"):
        await orchestrator.run_pipeline({})

@pytest.mark.asyncio
async def test_3d_orchestrator_handoff():
    """
    Proves the exact handoff chain:
    Phase3CVerifier -> CorpusEnricher -> UnresolvedPolicyError -> CaseAggregator -> UnresolvedPolicyError.
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
    def mock_aggregate(res):
        assert res is enriched_result # Proves Enricher output reaches Aggregator
        raise UnresolvedPolicyError("From aggregator", partial_result=res)
    mock_aggregator.aggregate = MagicMock(side_effect=mock_aggregate)

    orchestrator = Phase3DOrchestrator(
        verifier=mock_verifier, enricher=mock_enricher, aggregator=mock_aggregator
    )

    with pytest.raises(UnresolvedPolicyError) as exc_info:
        await orchestrator.run_pipeline(candidate)

    assert "From aggregator" in str(exc_info.value)
    assert exc_info.value.partial_result is enriched_result

    # Assert call sequence counts
    mock_enricher.enrich.assert_called_once_with(initial_result)
    mock_aggregator.aggregate.assert_called_once_with(enriched_result)

@pytest.mark.asyncio
async def test_3d_orchestrator_benchmark_admission_error_propagation():
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

    # We must ensure no persistence layer is invoked. The orchestrator doesn't have the finalizer injected yet,
    # but the aggregator being skipped proves the boundary.
    orchestrator = Phase3DOrchestrator(
        verifier=mock_verifier, enricher=mock_enricher, aggregator=mock_aggregator
    )

    with pytest.raises(BenchmarkAdmissionError, match="Missing corpus_position"):
        await orchestrator.run_pipeline(candidate)

    mock_enricher.enrich.assert_called_once_with(initial_result)
    mock_aggregator.aggregate.assert_not_called()
