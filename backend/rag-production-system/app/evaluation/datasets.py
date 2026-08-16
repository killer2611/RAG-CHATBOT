from __future__ import annotations

import json
from pathlib import Path

DEFAULT_DATASET = Path("data/golden_qa.json")


def load_golden_pairs(path: str | Path = DEFAULT_DATASET) -> list[tuple[str, str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Golden dataset must be a JSON list")
    pairs: list[tuple[str, str]] = []
    for row in data:
        if not isinstance(row, dict) or not row.get("question") or not row.get("answer"):
            raise ValueError("Each golden row needs non-empty question and answer fields")
        pairs.append((str(row["question"]), str(row["answer"])))
    return pairs
