import pytest
import os
from pathlib import Path
from app.evaluation.finalizer import StructuralValidator, ArtifactWriter

def test_structural_validator_success():
    # We will test the validator with the real schema path
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    validator = StructuralValidator(schema_path=str(schema_path))

    # A valid mock case
    valid_case = {
        "case_id": "test_1",
        "version": {
            "schema_version": "1.0",
            "benchmark_version": "1.0"
        },
        "question": "What?",
        "expected_answer": "That",
        "answerability": "answerable",
        "question_type": "factual",
        "topics": ["test"],
        "source": {
            "source_name": "test_source",
            "source_id": "s1",
            "document_hash": "hash123",
            "document_type": "legal",
            "type_confidence": 0.9
        },
        "retrieval_profile": {
            "evidence_scope": "single_span",
            "corpus_position": "start",
            "distractor_profile": "none",
            "retrieval_risk": "low"
        },
        "evidence": [],
        "claims": [],
        "verification": {
            "verdict": "accepted",
            "primary": {
                "verdict": "accepted",
                "reason": "Because",
                "claims_checked": [],
                "unsupported_claims": []
            }
        }
    }

    # Should not raise
    validator.validate(valid_case)

def test_structural_validator_failure():
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    validator = StructuralValidator(schema_path=str(schema_path))

    # Invalid case (missing required fields like question)
    invalid_case = {
        "case_id": "test_1"
    }

    with pytest.raises(ValueError, match="Schema validation failed"):
        validator.validate(invalid_case)

def test_artifact_writer_success(tmp_path):
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    validator = StructuralValidator(schema_path=str(schema_path))

    # We use tmp_path to ensure a clean directory that does not exist yet
    output_dir = tmp_path / "new_output_dir"
    writer = ArtifactWriter(output_dir=str(output_dir), validator=validator)

    valid_case = {
        "case_id": "test_1",
        "version": {
            "schema_version": "1.0",
            "benchmark_version": "1.0"
        },
        "question": "What?",
        "expected_answer": "That",
        "answerability": "answerable",
        "question_type": "factual",
        "topics": ["test"],
        "source": {
            "source_name": "test_source",
            "source_id": "s1",
            "document_hash": "hash123",
            "document_type": "legal",
            "type_confidence": 0.9
        },
        "retrieval_profile": {
            "evidence_scope": "single_span",
            "corpus_position": "start",
            "distractor_profile": "none",
            "retrieval_risk": "low"
        },
        "evidence": [],
        "claims": [],
        "verification": {
            "verdict": "accepted",
            "primary": {
                "verdict": "accepted",
                "reason": "Because",
                "claims_checked": [],
                "unsupported_claims": []
            }
        }
    }

    import copy
    original_case = copy.deepcopy(valid_case)

    written_path = writer.write_case(valid_case)

    # 1. Output directory is created when absent
    assert output_dir.exists()
    assert output_dir.is_dir()

    # 2. Filename is {case_id}.json
    assert written_path.name == "test_1.json"
    assert written_path.parent == output_dir
    assert written_path.exists()

    # 3. Written artifact is valid JSON
    import json
    with open(written_path, "r", encoding="utf-8") as f:
        loaded_case = json.load(f)

    assert loaded_case == valid_case

    # 4. Input case_dict is not mutated
    assert valid_case == original_case

def test_artifact_writer_failure(tmp_path):
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    validator = StructuralValidator(schema_path=str(schema_path))

    output_dir = tmp_path / "failure_dir"
    writer = ArtifactWriter(output_dir=str(output_dir), validator=validator)

    # Invalid case (missing required fields)
    invalid_case = {
        "case_id": "test_2"
    }

    # 1. Incomplete/invalid case is rejected
    with pytest.raises(ValueError, match="Schema validation failed"):
        writer.write_case(invalid_case)

    # 2. No artifact is created when validation fails
    # 3. DO NOT create output_dir merely as a side effect
    assert not output_dir.exists()
