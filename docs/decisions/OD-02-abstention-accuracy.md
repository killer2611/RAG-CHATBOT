# Decision Record: OD #2 — Abstention Accuracy Formula

## Status

**RESOLVED — v1.0**

Resolved as part of Phase 5e. Supersedes the `PENDING_POLICY` sentinel
in `app/evaluation/phase3f_runner.py` for `answerability == "unanswerable"`
cases.

This record does not resolve any other Open Decision.

---

## Context

Phase 3B generates both answerable and unanswerable benchmark cases.
Unanswerable cases test whether the RAG system correctly declines to
answer when the source document does not contain sufficient information.

`Phase3FRunner` generates a RAG response for every case and routes
answerable cases through DeepEval metrics. For unanswerable cases it
currently records:

```json
"status": "PENDING_POLICY"
"score": null
"success": "PENDING_POLICY"
```

OD #2 governs how `correctly_abstained` is determined and how
Abstention Accuracy is computed.

---

## Discovery

Direct inspection of `app/rag/prompts.py` on current `main` reveals:

```python
GROUNDED_ABSTENTION = (
    "I do not have enough information to answer this "
    "based on the provided documents."
)

QA_SYSTEM = f"""You are a factual RAG assistant.
Answer ONLY using the supplied document context.
...
If the context does not fully support an answer, respond exactly with:
{GROUNDED_ABSTENTION}
..."""
```

**The word "exactly" is load-bearing.** The RAG system was designed to
produce one specific canonical string when it correctly declines to
answer. OD #2 does not require inventing an abstention detection
heuristic — it requires checking whether the RAG system followed its
own stated specification.

---

## Decision

### Rule 1 — Population (denominator)

```
total_unanswerable =
    count of cases where case.answerability == "unanswerable"
```

`total_unanswerable` is counted **before** generation is attempted.
Every unanswerable case belongs in this denominator, including cases
where generation later fails or raises an exception. Generation failure
is an abstention failure — the system did not produce `GROUNDED_ABSTENTION`.

### Rule 2 — Canonical Abstention Check

```python
from app.rag.prompts import GROUNDED_ABSTENTION

correctly_abstained: bool = (
    (actual_output or "").strip() == GROUNDED_ABSTENTION
)
```

`actual_output` is the RAG system's response string. This is a
**case-sensitive exact equality check after stripping leading and
trailing whitespace**. No substring matching, no keyword list, no
semantic similarity, no case folding, no LLM judge.

Why exact equality rather than substring match: the QA system prompt
says "respond *exactly* with" the canonical phrase. An output that
contains `GROUNDED_ABSTENTION` followed by additional content would be
a violation of that instruction, not a correct abstention.

Why import from `app.rag.prompts` rather than hardcode: if
`GROUNDED_ABSTENTION` is ever changed, the formula updates automatically.
Hardcoding creates a second definition that can silently drift from
the system's actual behavior. See Rule 7 for the consequence of
changing the canonical phrase.

### Rule 3 — Per-Case Accounting

| Unanswerable case outcome | `correctly_abstained` | Status | Denominator |
|---|---|---|---|
| `actual_output.strip() == GROUNDED_ABSTENTION` | 1 | `ABSTENTION_EVALUATED` | Yes |
| `actual_output.strip() != GROUNDED_ABSTENTION` | 0 | `ABSTENTION_EVALUATED` | Yes |
| Generation exception / `actual_output` is None | 0 | `GENERATION_ERROR` | Yes |

`total_unanswerable` is incremented for all three outcomes.
`correctly_abstained_count` is incremented only for the first outcome.

### Rule 4 — Abstention Accuracy Formula

```
Abstention Accuracy = correctly_abstained_count / total_unanswerable
```

Result is a float in [0.0, 1.0].

If `total_unanswerable == 0`:
→ `Abstention Accuracy = null`
→ Report as `null` with note: "No unanswerable cases in benchmark population."
→ Do NOT substitute 0.0 or 1.0.

### Rule 5 — Phase 3F Report Shape

Add to the existing Phase 3F internal report as a first-class field:

```json
{
  "abstention": {
    "accuracy": 0.8,
    "correctly_abstained_count": 8,
    "total_unanswerable": 10,
    "formula": "exact_canonical_match"
  }
}
```

Individual case records for unanswerable cases:

```json
{
  "case_id": "...",
  "status": "ABSTENTION_EVALUATED",
  "actual_output": "<the actual RAG response>",
  "correctly_abstained": true,
  "abstention_score": 1.0
}
```

or for generation failure:

```json
{
  "case_id": "...",
  "status": "GENERATION_ERROR",
  "actual_output": null,
  "correctly_abstained": false,
  "abstention_score": 0.0
}
```

**On the `success` field for abstention results:**
Unlike DeepEval metrics, abstention accuracy has no `success` field
dependent on a threshold. The `abstention_score` (1.0 or 0.0) is the
factual result of OD #2. Whether a given Abstention Accuracy constitutes
a "pass" for the benchmark is governed by OD #1, which remains open.
OD #1 may eventually define a threshold for Abstention Accuracy, but
that threshold is not established here. Do NOT emit `"success": "PENDING_OD_1"`
for abstention results — that framing incorrectly implies OD #1 is
needed to determine whether the abstention itself was correct.

### Rule 6 — DeepEval Separation

```
answerable cases:
    → generate answer
    → source match check
    → DeepEval (Faithfulness, Answer Relevancy, Contextual Precision, Recall)
    → score per metric

unanswerable cases:
    → generate answer
    → canonical abstention comparison (Rule 2)
    → abstention_score: 1.0 or 0.0
    → NO DeepEval invocation
```

Abstention detection is zero additional LLM calls and zero additional
API cost.

### Rule 7 — Canonical Phrase Dependency

This formula's correctness depends on the invariant that:

1. The RAG system's `QA_SYSTEM` prompt in `app/rag/prompts.py` instructs
   the model to respond "exactly with" `GROUNDED_ABSTENTION`.
2. The RAG system used for Phase 3F evaluation uses `qa_messages()` from
   the same module.

Both hold on current `main`. If `GROUNDED_ABSTENTION` is ever changed
in `app/rag/prompts.py`, benchmark artifacts generated before the change
are incompatible with the formula applied after it, because historical
`actual_output` values were generated against the old phrase. The
`git_commit` field in `manifest.json` provides the traceability needed
to identify the boundary.

Changing `GROUNDED_ABSTENTION` without regenerating benchmark artifacts
is an architectural integrity violation.

---

## Why Not a Keyword List

Rejected approaches and why:

**Generic keyword detection** ("cannot determine", "not specified", etc.):
- Grounds abstention in invented vocabulary, not system design
- Creates false positives (hedged but confident answers)
- Creates false negatives (exact phrase misses keyword variants)
- Requires ongoing maintenance as language style changes

**Substring match of `GROUNDED_ABSTENTION`**:
- Accepts violations of the system's own "respond exactly with" instruction
- An output like "I do not have enough information... However, X is likely..."
  would count as correct abstention even though the model continued beyond
  the canonical phrase

**LLM judge for abstention**:
- Adds cost, non-determinism, and a second evaluation dependency
- Unnecessary when the system's design defines the answer

---

## Implementation Scope (Phase 5e)

Three files in one PR:

```
docs/decisions/OD-02-abstention-accuracy.md
backend/rag-production-system/app/evaluation/phase3f_runner.py
backend/rag-production-system/tests/test_3f_runner.py
```

No other files change. The existing test suite currently asserts
`PENDING_POLICY` behavior for unanswerable cases; those assertions
must be updated to reflect the resolved OD #2 policy.

The live smoke artifact `case-59e19740` (unanswerable, `abstention`
question type, currently producing `PENDING_POLICY`) is the natural
real-world regression target for the implementation.

---

## Open Decisions Resolved

| OD | Description | Resolution |
|----|-------------|------------|
| OD #2 | Abstention Accuracy formula | Rules 1–7 above |

## Open Decisions Remaining (unchanged)

| OD | Description |
|----|-------------|
| OD #1 | DeepEval metric thresholds (incl. Abstention Accuracy pass/fail gate) |
| OD #3 | Bootstrap / CI methodology |
| OD #4 | Cache implementation |
| OD #5 | Evidence overlap algorithm |
| OD #7 | Human-review interface / disagreement signal |
| OD #8 | CLI/API surface |
| OD #9 | Benchmark versioning convention |
| OD #12 | Candidate determinism policy |
