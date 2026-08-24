import json
import jsonschema
from typing import Dict, Any, Optional
from pathlib import Path

class StructuralValidator:
    """
    Final validation gate wrapping jsonschema.validate().
    Establishes structural conformance only.
    """
    def __init__(self, schema_path: Optional[str] = None):
        if schema_path is None:
            self.schema_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
        else:
            self.schema_path = Path(schema_path)
        with open(self.schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate(self, case_dict: Dict[str, Any]) -> None:
        """
        Validate the complete case against the frozen schema.
        Explicitly raises ValueError on validation failure.
        Never silently drops, repairs, coerces, or mutates an invalid case.
        """
        try:
            jsonschema.validate(instance=case_dict, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}") from e


class ArtifactWriter:
    """
    ArtifactWriter:
    - accepts a claimed-complete case_dict
    - independently validates it via StructuralValidator
    - refuses invalid/incomplete cases
    - writes valid JSON using {case_id}.json
    - returns the written path
    - performs zero LLM/API calls
    """
    def __init__(self, output_dir: str, validator: StructuralValidator):
        self.output_dir = Path(output_dir)
        self.validator = validator

    def write_case(self, case_dict: Dict[str, Any]) -> Path:
        """
        Accepts a claimed-complete case_dict, validates it, and writes it to disk.
        Does not mutate the input dictionary.
        """
        # Independently validate before persistence
        self.validator.validate(case_dict)

        # Validation succeeded; persist the artifact
        self.output_dir.mkdir(parents=True, exist_ok=True)

        case_id = case_dict["case_id"]
        output_path = self.output_dir / f"{case_id}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(case_dict, f, indent=2, ensure_ascii=False)

        return output_path
