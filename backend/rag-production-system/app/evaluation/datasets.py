from __future__ import annotations

import json
from pathlib import Path

from dataclasses import dataclass

DEFAULT_DATASET = Path("data/golden_qa.json")

@dataclass
class GoldenSource:
    source_name: str
    source_id: str | None = None

@dataclass
class GoldenCase:
    question: str
    expected_output: str
    source: GoldenSource | None = None

def load_golden_cases(path: str | Path = DEFAULT_DATASET) -> list[GoldenCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Golden dataset must be a JSON list")
    cases: list[GoldenCase] = []
    for row in data:
        if not isinstance(row, dict) or not row.get("question") or not row.get("answer"):
            raise ValueError("Each golden row needs non-empty question and answer fields")
        
        source = None
        if "source" in row and isinstance(row["source"], dict):
            src_data = row["source"]
            if "source_name" in src_data:
                source = GoldenSource(
                    source_name=str(src_data["source_name"]),
                    source_id=str(src_data["source_id"]) if "source_id" in src_data else None
                )
        
        cases.append(GoldenCase(
            question=str(row["question"]),
            expected_output=str(row["answer"]),
            source=source
        ))
    return cases
