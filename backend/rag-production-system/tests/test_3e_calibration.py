import copy
import pytest
from app.evaluation.calibration import CalibrationEngine, DuplicateClaimError

def get_base_mock_case():
    return {
        "case_id": "case-123",
        "question": "Q?",
        "expected_answer": "A",
        "answerability": "answerable",
        "question_type": "factual",
        "topics": [],
        "source": {
            "source_name": "name",
            "source_id": "id",
            "document_hash": "hash",
            "document_type": "legal",
            "type_confidence": 1.0
        },
        "evidence": [],
        "version": {
            "schema_version": "1.0",
            "benchmark_version": "1.0"
        },
        "claims": []
    }

def test_calibration_all_matching_claims_agree():
    # 1. All matching claims agree -> correct per-claim results and aggregate 1.0
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported"}
    ]
    ref = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported"}
    ]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 1.0
    assert result.per_claim_agreement == {"c1": True, "c2": True}
    assert len(result.unmatched_automated) == 0
    assert len(result.unmatched_reference) == 0

def test_calibration_partial_disagreement():
    # 2. Partial disagreement -> correct per-claim results and aggregate
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported"}
    ]
    ref = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "supported"} # Disagrees
    ]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 0.5
    assert result.per_claim_agreement == {"c1": True, "c2": False}

def test_calibration_all_matched_claims_disagree():
    # 3. All matched claims disagree -> aggregate 0.0
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"}
    ]
    ref = [
        {"claim_id": "c1", "support_status": "unsupported"}
    ]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 0.0
    assert result.per_claim_agreement == {"c1": False}

def test_calibration_unmatched_claims_detected():
    # 4. Automated unmatched claim is detected
    # 5. Reference unmatched claim is detected
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c_auto_only", "support_status": "supported"}
    ]
    ref = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c_ref_only", "support_status": "supported"}
    ]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 1.0 # Excludes unmatched from denominator
    assert "c_auto_only" in result.unmatched_automated
    assert "c_ref_only" in result.unmatched_reference

def test_calibration_duplicate_automated_claim_rejected():
    # 6. Duplicate automated claim_id is rejected
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c1", "support_status": "unsupported"}
    ]
    ref = [{"claim_id": "c1", "support_status": "supported"}]

    engine = CalibrationEngine()
    with pytest.raises(DuplicateClaimError, match="Duplicate automated claim_id"):
        engine.calibrate(case, ref)

def test_calibration_duplicate_reference_claim_rejected():
    # 7. Duplicate reference claim_id is rejected
    case = get_base_mock_case()
    case["claims"] = [{"claim_id": "c1", "support_status": "supported"}]
    ref = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c1", "support_status": "unsupported"}
    ]

    engine = CalibrationEngine()
    with pytest.raises(DuplicateClaimError, match="Duplicate reference claim_id"):
        engine.calibrate(case, ref)

def test_calibration_ordering_differences():
    # 8. Ordering differences do not affect matching
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "support_status": "supported"},
        {"claim_id": "c2", "support_status": "unsupported"}
    ]
    ref = [
        {"claim_id": "c2", "support_status": "unsupported"},
        {"claim_id": "c1", "support_status": "supported"}
    ]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 1.0

def test_calibration_zero_matched_claims_undefined():
    # 9. Zero matched claims produces UNDEFINED aggregate, not 0
    case = get_base_mock_case()
    case["claims"] = [{"claim_id": "c_auto", "support_status": "supported"}]
    ref = [{"claim_id": "c_ref", "support_status": "supported"}]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement is None

def test_calibration_does_not_mutate_input():
    # 11. Input BenchmarkCase is not mutated
    case = get_base_mock_case()
    case["claims"] = [{"claim_id": "c1", "support_status": "supported"}]
    ref = [{"claim_id": "c1", "support_status": "supported"}]

    case_copy = copy.deepcopy(case)

    engine = CalibrationEngine()
    engine.calibrate(case, ref)

    assert case == case_copy

def test_calibration_accepts_synthetic_schema_valid_fixture():
    # 13. Synthetic schema-valid fixture is accepted as intended
    # 12. The mechanism does not inspect or calibrate case-level verdict
    case = get_base_mock_case()
    case["claims"] = [
        {"claim_id": "c1", "claim": "text", "support_status": "supported", "evidence_ids": ["e1"]}
    ]
    case["verification"] = {
        "verdict": "accepted",
        "primary": {
            "verdict": "accepted",
            "claims_checked": ["c1"],
            "unsupported_claims": [],
            "reason": "..."
        },
        "secondary": None,
        "human_review": None
    }
    case["retrieval_profile"] = {
        "evidence_scope": "single_span",
        "corpus_position": "start",
        "distractor_profile": "none",
        "retrieval_risk": "low"
    }

    # 1. Independently validate against frozen schema
    import json, jsonschema
    from pathlib import Path
    schema_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(case, schema)

    ref = [{"claim_id": "c1", "support_status": "supported"}]

    engine = CalibrationEngine()
    result = engine.calibrate(case, ref)

    assert result.aggregate_agreement == 1.0

def test_calibration_zero_api_calls():
    # 2. Explicitly prove zero LLM/API calls
    case = get_base_mock_case()
    case["claims"] = [{"claim_id": "c1", "support_status": "supported"}]
    ref = [{"claim_id": "c1", "support_status": "supported"}]

    engine = CalibrationEngine()

    import socket
    from unittest.mock import patch
    with patch.object(socket, "socket") as mock_socket:
        engine.calibrate(case, ref)
        mock_socket.assert_not_called()

def test_calibration_missing_claim_id_rejected():
    # 3. Harden claim-id contract: missing claim_id
    case = get_base_mock_case()
    case["claims"] = [{"support_status": "supported"}]
    ref = [{"claim_id": "c1", "support_status": "supported"}]

    engine = CalibrationEngine()
    with pytest.raises(ValueError, match="Automated claim is missing required 'claim_id' field"):
        engine.calibrate(case, ref)

    case["claims"] = [{"claim_id": "c1", "support_status": "supported"}]
    ref = [{"support_status": "supported"}]
    with pytest.raises(ValueError, match="Reference claim is missing required 'claim_id' field"):
        engine.calibrate(case, ref)

def test_calibration_missing_support_status_rejected():
    # 4. Make reference input contract explicit: missing support_status
    case = get_base_mock_case()
    case["claims"] = [{"claim_id": "c1"}]
    ref = [{"claim_id": "c1", "support_status": "supported"}]

    engine = CalibrationEngine()
    with pytest.raises(ValueError, match="Automated claim is missing required 'support_status' field"):
        engine.calibrate(case, ref)

    case["claims"] = [{"claim_id": "c1", "support_status": "supported"}]
    ref = [{"claim_id": "c1"}]
    with pytest.raises(ValueError, match="Reference claim is missing required 'support_status' field"):
        engine.calibrate(case, ref)