import pytest
from app.evaluation.phase3_validation import validate_h12_unanswerable_semantics

def create_case(answerability: str, claims: list, evidence: list = None) -> dict:
    if evidence is None:
        evidence = [{"evidence_id": "ev_1", "quote": "something", "span_hash": "hash"}]

    return {
        "answerability": answerability,
        "evidence": evidence,
        "claims": claims
    }

# VALID:

# 1. answerable + supported claim + evidence
def test_answerable_supported():
    case = create_case("answerable", [{"support_status": "supported"}])
    # Should not raise
    validate_h12_unanswerable_semantics(case)

# 2. answerable + contradicted claim + evidence
def test_answerable_contradicted():
    case = create_case("answerable", [{"support_status": "contradicted"}])
    validate_h12_unanswerable_semantics(case)

# 3. answerable + unsupported claim
def test_answerable_unsupported():
    case = create_case("answerable", [{"support_status": "unsupported"}], evidence=[])
    validate_h12_unanswerable_semantics(case)

# 4. unanswerable + not_applicable claim + no evidence
def test_unanswerable_not_applicable_no_evidence():
    case = create_case("unanswerable", [{"support_status": "not_applicable"}], evidence=[])
    validate_h12_unanswerable_semantics(case)

# 5. unanswerable + not_applicable claim + populated evidence
def test_unanswerable_not_applicable_with_evidence():
    case = create_case("unanswerable", [{"support_status": "not_applicable"}])
    validate_h12_unanswerable_semantics(case)

# 6. unanswerable + multiple not_applicable claims
def test_unanswerable_multiple_not_applicable():
    case = create_case("unanswerable", [{"support_status": "not_applicable"}, {"support_status": "not_applicable"}])
    validate_h12_unanswerable_semantics(case)

# INVALID:

# 7. unanswerable + supported claim + evidence
def test_unanswerable_supported():
    case = create_case("unanswerable", [{"support_status": "supported"}])
    with pytest.raises(ValueError, match="H-12 Violation.*supported"):
        validate_h12_unanswerable_semantics(case)

# 8. unanswerable + contradicted claim + evidence
def test_unanswerable_contradicted():
    case = create_case("unanswerable", [{"support_status": "contradicted"}])
    with pytest.raises(ValueError, match="H-12 Violation.*contradicted"):
        validate_h12_unanswerable_semantics(case)

# 9. unanswerable + unsupported claim
def test_unanswerable_unsupported():
    case = create_case("unanswerable", [{"support_status": "unsupported"}])
    with pytest.raises(ValueError, match="H-12 Violation.*unsupported"):
        validate_h12_unanswerable_semantics(case)

# 10. unanswerable + mixed claims where one is not_applicable and another is supported
def test_unanswerable_mixed_supported():
    case = create_case("unanswerable", [{"support_status": "not_applicable"}, {"support_status": "supported"}])
    with pytest.raises(ValueError, match="H-12 Violation.*supported"):
        validate_h12_unanswerable_semantics(case)

# 11. unanswerable + mixed claims where one is not_applicable and another is contradicted
def test_unanswerable_mixed_contradicted():
    case = create_case("unanswerable", [{"support_status": "contradicted"}, {"support_status": "not_applicable"}])
    with pytest.raises(ValueError, match="H-12 Violation.*contradicted"):
        validate_h12_unanswerable_semantics(case)

# 12. unanswerable + mixed claims where one is not_applicable and another is unsupported
def test_unanswerable_mixed_unsupported():
    case = create_case("unanswerable", [{"support_status": "not_applicable"}, {"support_status": "unsupported"}])
    with pytest.raises(ValueError, match="H-12 Violation.*unsupported"):
        validate_h12_unanswerable_semantics(case)
