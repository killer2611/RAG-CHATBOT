import pytest
from unittest.mock import AsyncMock

from app.core.config import Settings
from app.evaluation.aggregator import CaseAggregator
from app.evaluation.verifier_v3 import IntermediateVerificationResult
from app.evaluation.exceptions import StructuralValidationError

@pytest.fixture
def mock_secondary():
    return AsyncMock()

@pytest.fixture
def aggregator(mock_secondary):
    settings = Settings(
        chat_provider="groq",
        groq_api_key="test",
        eval_deepseek_api_key="test",
        eval_sambanova_api_key="test",
        phase3_unsupported_ratio_threshold=0.5
    )
    return CaseAggregator(settings=settings, secondary_verifier=mock_secondary)

def make_result(answerability="answerable", claims=None, evidence=None, expected_answer=""):
    if claims is None:
        claims = []
    if evidence is None:
        evidence = []

    claims_checked = [c["claim_id"] for c in claims if c["support_status"] != "not_applicable"]
    unsupported_claims = [c["claim_id"] for c in claims if c["support_status"] == "unsupported"]

    return IntermediateVerificationResult(
        partial_case_dict={
            "case_id": "test",
            "question": "Q?",
            "expected_answer": expected_answer,
            "answerability": answerability,
            "claims": claims,
            "evidence": evidence
        },
        claims_checked=claims_checked,
        unsupported_claims=unsupported_claims
    )

@pytest.mark.asyncio
async def test_rule_1_unanswerable(aggregator, mock_secondary):
    """
    unanswerable -> accepted -> secondary not called
    """
    result = make_result("unanswerable")

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["verdict"] == "accepted"
    assert verif["primary"]["verdict"] == "accepted"
    assert verif["secondary"] is None
    mock_secondary.verify.assert_not_called()

@pytest.mark.asyncio
async def test_rule_0_zero_eligible_claims(aggregator, mock_secondary):
    """
    answerable + zero eligible claims -> StructuralValidationError -> secondary not called
    """
    result = make_result("answerable", claims=[
        {"claim_id": "c1", "support_status": "not_applicable"}
    ])

    with pytest.raises(StructuralValidationError, match="zero eligible claims"):
        await aggregator.aggregate(result)

    mock_secondary.verify.assert_not_called()

@pytest.mark.asyncio
async def test_rule_2_contradiction_present(aggregator, mock_secondary):
    """
    contradiction present -> rejected -> secondary not called -> threshold not consulted
    """
    result = make_result("answerable", claims=[
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "contradicted"}
    ])

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["verdict"] == "rejected"
    assert verif["primary"]["verdict"] == "rejected"
    # Contradictions are not required by schema on verification object.
    assert "contradictions" not in verif
    assert verif["secondary"] is None
    mock_secondary.verify.assert_not_called()

@pytest.mark.asyncio
async def test_rule_3_unsupported_ratio_greater_than_threshold(aggregator, mock_secondary):
    """
    unsupported_ratio > threshold -> rejected -> secondary not called
    """
    result = make_result("answerable", claims=[
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported"},
        {"claim_id": "c3", "support_status": "unsupported"}
    ])

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["verdict"] == "rejected"
    assert verif["primary"]["verdict"] == "rejected"
    assert verif["secondary"] is None
    mock_secondary.verify.assert_not_called()

@pytest.mark.asyncio
async def test_rule_4_unsupported_ratio_less_than_or_equal_to_threshold_accepted(aggregator, mock_secondary):
    """
    unsupported_ratio <= threshold -> primary disputed -> secondary accepted -> final accepted
    """
    claims = [
        {"claim_id": "c1", "support_status": "supported", "claim": "supported claim", "evidence_ids": ["e1"]},
        {"claim_id": "c2", "support_status": "unsupported", "claim": "unsupported claim", "evidence_ids": ["e2", "e3"]}
    ]
    evidence = [
        {"evidence_id": "e1", "quote": "quote 1", "span_hash": "h1"},
        {"evidence_id": "e2", "quote": "quote 2", "span_hash": "h2"},
        {"evidence_id": "e3", "quote": "quote 3", "span_hash": "h3"}
    ]
    result = make_result("answerable", claims=claims, evidence=evidence, expected_answer="expected")
    mock_secondary.verify.return_value = "accepted"

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["primary"]["verdict"] == "disputed"
    assert verif["verdict"] == "accepted"
    assert verif["secondary"]["verdict"] == "accepted"
    assert verif["secondary"]["claims_checked"] == ["c2"]

    # Assert normalized payload is passed
    mock_secondary.verify.assert_called_once_with(
        question="Q?",
        expected_answer="expected",
        disputed_claims=[
            {
                "claim_id": "c2",
                "text": "unsupported claim",
                "evidence_quotes": ["quote 2", "quote 3"]
            }
        ]
    )

    # Prove "claim" does not exist at boundary
    called_args = mock_secondary.verify.call_args.kwargs
    disputed_claims = called_args["disputed_claims"]
    assert "text" in disputed_claims[0]
    assert "claim" not in disputed_claims[0]

@pytest.mark.asyncio
async def test_rule_4_unsupported_ratio_less_than_threshold_rejected(aggregator, mock_secondary):
    """
    unsupported_ratio <= threshold -> primary disputed -> secondary rejected -> final rejected
    """
    claims = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "supported"},
        {"claim_id": "c3", "support_status": "unsupported", "claim": "unsupported claim", "evidence_ids": []}
    ]
    result = make_result("answerable", claims=claims)
    mock_secondary.verify.return_value = "rejected"

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["primary"]["verdict"] == "disputed"
    assert verif["verdict"] == "rejected"
    assert verif["secondary"]["verdict"] == "rejected"
    mock_secondary.verify.assert_called_once_with(
        question="Q?",
        expected_answer="",
        disputed_claims=[
            {
                "claim_id": "c3",
                "text": "unsupported claim",
                "evidence_quotes": []
            }
        ]
    )

@pytest.mark.asyncio
async def test_rule_4_unsupported_ratio_less_than_threshold_error(aggregator, mock_secondary):
    """
    unsupported_ratio <= threshold -> primary disputed -> secondary error -> final disputed
    (Replaces the old human_review test)
    """
    result = make_result("answerable", claims=[
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported", "claim": "claim text", "evidence_ids": []}
    ])
    mock_secondary.verify.return_value = "error"

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["primary"]["verdict"] == "disputed"
    assert verif["verdict"] == "disputed"
    assert verif["secondary"] is None
    assert verif["human_review"] is None
    mock_secondary.verify.assert_called_once()

@pytest.mark.asyncio
async def test_rule_5_all_eligible_claims_supported(aggregator, mock_secondary):
    """
    all eligible claims supported -> accepted -> secondary not called
    """
    result = make_result("answerable", claims=[
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "supported"}
    ])

    final = await aggregator.aggregate(result)

    verif = final.partial_case_dict["verification"]
    assert verif["verdict"] == "accepted"
    assert verif["primary"]["verdict"] == "accepted"
    assert verif["secondary"] is None
    mock_secondary.verify.assert_not_called()

@pytest.mark.asyncio
async def test_evidence_resolution(aggregator, mock_secondary):
    """
    Test explicitly that evidence_ids resolve correctly to canonical evidence quotes.
    And that unresolvable evidence_ids are silently ignored or handled gracefully.
    """
    claims = [
        {
            "claim_id": "c0",
            "support_status": "supported",
            "claim": "supported",
            "evidence_ids": ["e1"]
        },
        {
            "claim_id": "c1",
            "support_status": "unsupported",
            "claim": "claim with multiple evidence",
            "evidence_ids": ["e1", "e3", "missing_e"]
        }
    ]
    evidence = [
        {"evidence_id": "e1", "quote": "Actual quote e1"},
        {"evidence_id": "e2", "quote": "Actual quote e2"},
        {"evidence_id": "e3", "quote": "Actual quote e3"}
    ]

    result = make_result("answerable", claims=claims, evidence=evidence, expected_answer="answer")
    mock_secondary.verify.return_value = "accepted"

    await aggregator.aggregate(result)

    # Prove evidence quote resolution
    called_args = mock_secondary.verify.call_args.kwargs
    disputed_claims = called_args["disputed_claims"]

    assert len(disputed_claims) == 1
    c1 = disputed_claims[0]
    assert c1["claim_id"] == "c1"
    assert c1["text"] == "claim with multiple evidence"
    # "e2" is not in evidence_ids, "missing_e" is not in canonical evidence.
    assert c1["evidence_quotes"] == ["Actual quote e1", "Actual quote e3"]
