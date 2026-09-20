import copy
import pytest

from app.evaluation.verifier_v3 import IntermediateVerificationResult
from app.evaluation.exceptions import BenchmarkAdmissionError, UnresolvedPolicyError
from app.evaluation.enrichment import CorpusEnricher
from app.evaluation.aggregator import CaseAggregator

def test_enricher_admission_failure():
    """
    Tests that candidates lacking authoritative structural corpus_position
    hit the explicit BenchmarkAdmissionError boundary.
    """
    result = IntermediateVerificationResult(
        partial_case_dict={
            "case_id": "test-1",
            "retrieval_profile": {} # Missing corpus_position
        },
        claims_checked=["claim1"],
        unsupported_claims=[]
    )
    enricher = CorpusEnricher()

    with pytest.raises(BenchmarkAdmissionError) as exc_info:
        enricher.enrich(result)

    assert "authoritative corpus_position is required" in str(exc_info.value)

def test_enricher_policy_blocked():
    """
    Tests that candidates with authoritative structural corpus_position
    pass admission but hit the UnresolvedPolicyError boundary for distractor
    and risk classification policies.
    """
    original_dict = {
        "case_id": "test-2",
        "retrieval_profile": {"corpus_position": "middle"}
    }
    result = IntermediateVerificationResult(
        partial_case_dict=copy.deepcopy(original_dict),
        claims_checked=["claim1"],
        unsupported_claims=[]
    )
    enricher = CorpusEnricher()

    with pytest.raises(UnresolvedPolicyError) as exc_info:
        enricher.enrich(result)

    assert "Retrieval enrichment policy" in str(exc_info.value)

    # Check enriched partial result
    enriched_result = exc_info.value.partial_result
    assert enriched_result.partial_case_dict["retrieval_profile"]["corpus_position"] == "middle"

    # Confirm no mutation of caller-owned object
    assert result.partial_case_dict == original_dict

@pytest.mark.asyncio
async def test_aggregator_structural_assembly():
    """
    Tests that CaseAggregator structurally assembles the verification.primary
    block mapping claims correctly according to OD #10.
    """
    result = IntermediateVerificationResult(
        partial_case_dict={
            "case_id": "test-3",
            "claims": [
                {"claim_id": "claim1", "support_status": "supported"},
                {"claim_id": "claim2", "support_status": "unsupported"}
            ]
        },
        claims_checked=["claim1", "claim2"],
        unsupported_claims=["claim2"]
    )
    from app.core.config import Settings
    from unittest.mock import AsyncMock
    mock_settings = Settings(
        chat_provider="groq",
        groq_api_key="test",
        eval_deepseek_api_key="test",
        eval_sambanova_api_key="test",
        phase3_unsupported_ratio_threshold=0.5
    )

    mock_secondary = AsyncMock()
    mock_secondary.verify.return_value = "accepted"
    aggregator = CaseAggregator(settings=mock_settings, secondary_verifier=mock_secondary)

    assembled = await aggregator.aggregate(result)

    verif = assembled.partial_case_dict["verification"]

    assert verif["verdict"] == "accepted"
    assert verif["primary"]["verdict"] == "disputed"
    assert verif["primary"]["claims_checked"] == ["claim1", "claim2"]
    assert verif["primary"]["unsupported_claims"] == ["claim2"]
    assert verif["secondary"] is not None
    assert verif["secondary"]["verdict"] == "accepted"
    assert verif["human_review"] is None
