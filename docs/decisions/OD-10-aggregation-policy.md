# Decision Record: OD #10 — Case-Level Verdict Aggregation Policy

## Status

**RESOLVED**

This record resolves two tightly coupled Open Decisions through a single
coupled decision:

- **OD #10** — Case-level verdict aggregation policy
- **OD #6** — Secondary verifier model selection (Rule 4 cannot be specified
  without naming the secondary model; they are inseparable)

Supersedes the `UnresolvedPolicyError` stub in `app/evaluation/aggregator.py`,
which must be replaced during Phase 5b implementation.

All other Open Decisions remain unchanged. This record does not resolve any
OD other than #6 and #10.

---

## Context

Phase 3C (adversarial claim-level verification) produces per-claim verdicts:
`supported`, `unsupported`, `contradicted`, or `not_applicable`. These live
in `IntermediateVerificationResult.partial_case_dict["claims"][*]["support_status"]`.

Phase 3D's `CaseAggregator` must translate this set of claim-level verdicts
into a single case-level `verification.verdict` drawn from the frozen
`BenchmarkCase` schema vocabulary:

```
accepted | rejected | disputed | human_review
```

Until this decision, `CaseAggregator.aggregate()` raised
`UnresolvedPolicyError` on every invocation, blocking end-to-end pipeline
completion and preventing `ArtifactWriter` from writing any benchmark artifact.

The frozen schema also defines a nested `verification.primary` block
(a `verifier_result` object) and an optional `verification.secondary` block.
This decision specifies how both are populated and when secondary is invoked.

---

## Definitions

**eligible_claims:** All claims in the case whose `support_status` is not
`not_applicable`. Formally:

```
eligible_claims = [c for c in case.claims if c.support_status != "not_applicable"]
```

**unsupported_ratio:** The fraction of eligible claims that are unsupported:

```
unsupported_ratio =
    count(c in eligible_claims where c.support_status == "unsupported")
    /
    count(eligible_claims)
```

This ratio is only computed when `count(eligible_claims) > 0`. See Rule 0
for the zero-denominator case.

**unsupported_ratio_threshold:** A configurable float parameter, part of
OD #10, with a default of `0.5`. Stored as
`Settings.phase3_unsupported_ratio_threshold`.

**IMPORTANT:** `unsupported_ratio_threshold` is an OD #10 parameter governing
benchmark construction. It is NOT an evaluation metric threshold and is NOT
governed by OD #1 (DeepEval metric thresholds). These are distinct concepts
at different pipeline layers. OD #1 remains open and unaffected by this
decision.

---

## Decision

The case-level verdict is determined by applying the following rules in
strict precedence order. Rules are mutually exclusive. The first matching
rule terminates the decision.

### Rule 0 — Structural Guard: Zero Eligible Claims

If `answerability == "answerable"` AND `count(eligible_claims) == 0`:

The case is **structurally invalid**. An answerable case must have at least
one claim whose truth value can be assessed. This condition indicates a
generation or verification defect upstream.

Policy: raise `StructuralValidationError`. The case MUST NOT be admitted.
It MUST NOT be silently treated as accepted (which would misrepresent
0 unsupported / 0 total as a passing case).

### Rule 1 — Unanswerable Cases

If `answerability == "unanswerable"`:

Every claim must carry `support_status == "not_applicable"` (invariant H-12,
enforced by `phase3_validation.py`). This means `eligible_claims` is empty.
Rule 0 does not apply because the case is unanswerable by declaration.

Policy: set `verification.verdict = "accepted"`.

Rationale: an unanswerable benchmark case is a valid, well-formed test
artifact. Its verdict reflects the integrity of the case construction, not
the correctness of the RAG response to it. The RAG response to an unanswerable
case is evaluated separately by the abstention metric (OD #2, which remains
open).

### Rule 2 — Contradiction Check (Highest Priority for Answerable Cases)

If `answerability == "answerable"` AND any claim has
`support_status == "contradicted"`:

Policy: set `verification.verdict = "rejected"`.

The implementation MUST NOT compute `unsupported_ratio` for this case.
The implementation MUST NOT invoke the secondary verifier for this case.
The implementation MUST NOT apply any threshold check.
Rejection is immediate and deterministic.

Rationale: a contradiction means the source document explicitly refutes a
claim in the expected answer. This is a hard faithfulness violation. No
threshold or secondary opinion is appropriate.

### Rule 3 — Unsupported Ratio Rejection

If `answerability == "answerable"` AND no claim is `contradicted` AND
`unsupported_ratio > unsupported_ratio_threshold`:

Policy: set `verification.verdict = "rejected"`.

The implementation MUST NOT invoke the secondary verifier for this case.

Rationale: when a majority of answerable claims cannot be verified from
source evidence, secondary verification adds cost without changing the
outcome. A case failing this threshold is not a borderline case.

### Rule 4 — Secondary Verification (Disputed Cases)

If `answerability == "answerable"` AND no claim is `contradicted` AND
at least one claim is `unsupported` AND
`unsupported_ratio ≤ unsupported_ratio_threshold`:

Policy: set `verification.primary.verdict = "disputed"`. Invoke the
secondary verifier.

**IMPORTANT: `disputed` is a transient intermediate state produced by the
primary verifier. It is NOT a canonical final case verdict. The implementation
MUST NOT write an artifact with `verification.verdict = "disputed"` after
the secondary verifier has been invoked. The final case verdict is resolved
only after secondary produces its outcome (see below).**

**Secondary verifier (OD #6 — resolved simultaneously with OD #10):**
Model: `Meta-Llama-3.3-70B-Instruct` via SambaNova, accessed using
`settings.eval_sambanova_api_key` and `settings.eval_sambanova_base_url`.

The secondary verifier re-evaluates disputed claims against source evidence.
It returns only `accepted` or `rejected` — never `disputed`. This is
enforced structurally in the frozen schema (secondary verdict enum is
restricted to `accepted | rejected` only by `$defs/secondary_verifier_result`).

Secondary resolution:
- Secondary returns `accepted` → `verification.verdict = "accepted"`
- Secondary returns `rejected` → `verification.verdict = "rejected"`
- Secondary unavailable, times out, or errors → `verification.verdict = "human_review"`

**Note on `human_review`:** This case-level state signals that a human must
review the case before it can be admitted. The actual human-review interface,
reviewer workflow, disagreement signal, and persistence UX are governed by
OD #7, which remains open and is not specified here.

### Rule 5 — Clean Acceptance

If `answerability == "answerable"` AND no claim is `contradicted` AND
no claim is `unsupported` (all eligible claims are `supported`):

Policy: set `verification.verdict = "accepted"`.

---

## Truth Table

| answerability | contradicted? | unsupported_ratio | eligible_claims | Final verdict | Secondary invoked? |
|---|---|---|---|---|---|
| unanswerable | N/A | N/A | 0 (all N/A) | accepted | No |
| answerable | Yes (any) | N/A | any | rejected | No |
| answerable | No | N/A | 0 | ERROR (Rule 0) | No |
| answerable | No | > threshold | > 0 | rejected | No |
| answerable | No | ≤ threshold, >0 unsupported | > 0 | accepted / rejected / human_review | Yes |
| answerable | No | 0.0 (none unsupported) | > 0 | accepted | No |

Where secondary is invoked, the final verdict depends on secondary outcome:
`accepted`, `rejected`, or `human_review` (never `disputed`).

---

## Formal State Machine

```
answerability == "unanswerable"
    → verdict = "accepted"   [Rule 1]

answerability == "answerable"
    │
    ├── eligible_claims == 0
    │       → StructuralValidationError   [Rule 0]
    │
    ├── any claim contradicted?
    │       YES → verdict = "rejected"   [Rule 2]
    │             (no ratio, no secondary, deterministic)
    │
    ├── unsupported_ratio > threshold?
    │       YES → verdict = "rejected"   [Rule 3]
    │             (no secondary)
    │
    ├── unsupported_ratio ≤ threshold AND ≥1 claim unsupported?
    │       YES → primary.verdict = "disputed"
    │             invoke secondary   [Rule 4]
    │               │
    │               ├── secondary accepted → verdict = "accepted"
    │               ├── secondary rejected → verdict = "rejected"
    │               └── secondary unavailable/error → verdict = "human_review"
    │
    └── all eligible claims supported (ratio = 0.0)
            → verdict = "accepted"   [Rule 5]
```

---

## Verification Block Construction

The `CaseAggregator` must produce a schema-compliant `verification` block
replacing the `HollowVerificationStub` from Phase 3B.

Schema-compliant structure:

```json
{
  "verdict": "<accepted|rejected|human_review>",
  "primary": {
    "verdict": "<accepted|rejected|disputed>",
    "claims_checked": ["<claim_id>", "..."],
    "unsupported_claims": ["<claim_id>", "..."],
    "reason": "<string or null>"
  },
  "secondary": null,
  "human_review": null,
  "unsupported_claims": ["<claim_id>", "..."],
  "contradictions": ["<claim_id>", "..."],
  "reason": "<string or null>"
}
```

Population rules:

1. `verification.primary` MUST always be populated for answerable cases.
2. `verification.secondary` MUST be `null` when secondary verification is
   not invoked. An empty object (`{}`) MUST NOT be emitted.
3. When secondary is invoked, `verification.secondary` is populated with
   the secondary verifier's output.
4. `verification.human_review` MUST be `null` in all cases governed by this
   decision. OD #7 governs any future change to this field.
5. The case-level `verification.verdict` must satisfy the allOf constraints
   in the frozen schema (established during Phase 3 schema hardening and
   tested by the 20-state matrix in `test_schema.py`).
6. `disputed` MUST NOT appear as the final `verification.verdict` in any
   artifact written by `ArtifactWriter`. It is only valid as
   `verification.primary.verdict` when secondary is in progress.

---

## Compatibility with Phase 3 Hardening Invariants

This decision is compatible with all invariants H-1 through H-12 established
in `docs/Phase 3/phase3_contract_hardening.md`. Specifically:

- **H-12 (Unanswerable claim semantics):** Rule 1 of this decision is the
  case-level expression of H-12. Unanswerable cases have all claims as
  `not_applicable`, and the case-level verdict is `accepted` (valid
  benchmark case, not a measure of RAG correctness).
- **H-5/H-7 (Verification state machine):** The state machine in this
  decision is the policy-level implementation of the structural state machine
  established in Phase 3 schema hardening. The allOf constraints in the
  frozen schema enforce structural consistency; this document specifies the
  semantic policy that drives transitions.

Refer to `docs/Phase 3/phase3_contract_hardening.md` for the full H-x
invariant list. This document does not repeat them.

---

## New Configuration Parameter

One new configurable parameter is introduced by this decision:

```python
# In Settings (app/core/config.py)
phase3_unsupported_ratio_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
```

This parameter is part of OD #10. It is NOT an evaluation metric threshold
and is NOT governed by OD #1 (DeepEval metric thresholds). Changing this
value adjusts when a disputed case goes to secondary versus immediate
rejection. The default of 0.5 means: if more than half of eligible claims
are unsupported, reject immediately without secondary.

---

## Consequences

### What changes during Phase 5b implementation

- `CaseAggregator.aggregate()` is implemented according to the rules above
  and no longer raises `UnresolvedPolicyError` in normal operation.
- `Phase3DOrchestrator.run_pipeline()` can produce complete `BenchmarkCase`
  artifacts for the first time.
- `ArtifactWriter.write_case()` can write admitted cases to disk.
- `Phase3FRunner.run()` can evaluate real pipeline-produced cases.
- `Settings.phase3_unsupported_ratio_threshold` is added to `config.py`.

### What does not change

- The frozen schema (`benchmark_case.schema.json`) — unchanged.
- Phase 1/2 evaluation runner — unchanged.
- `Phase3CVerifier` — unchanged.
- **OD #1** (DeepEval metric thresholds) — remains open.
- **OD #2** (Abstention Accuracy formula) — remains open.
- **OD #3** (Bootstrap/CI methodology) — remains open.
- **OD #4, #5, #7, #8, #9, #11, #12** — all remain open.

---

## Alternatives Considered

**All-or-nothing acceptance:** Every claim must be `supported`; any `unsupported`
triggers immediate rejection without secondary. Rejected: too brittle for
multi-claim cases. One unverifiable minor claim should not fail an otherwise
well-supported case.

**Secondary on all non-accepted cases:** Invoke secondary whenever primary
is not immediately accepted. Rejected: makes secondary the default path,
defeating cost-control principles. Secondary must be a targeted exception
on genuinely borderline cases.

**Threshold as part of OD #1:** Rejected explicitly. OD #1 governs DeepEval
faithfulness/relevancy/precision/recall thresholds applied at evaluation time.
The aggregation ratio threshold is applied at benchmark construction time.
These are different pipeline layers and must not be conflated.

**Separate ADRs for OD #10 and OD #6:** Rejected. Rule 4 cannot be fully
specified without naming a concrete secondary model. Artificially separating
them would create an internally incomplete policy document.

---

## Open Decisions Resolved by This Record

| OD | Description | Resolution |
|----|-------------|------------|
| OD #10 | Case-level verdict aggregation policy | Rules 0–5 above |
| OD #6 | Secondary verifier model | SambaNova Meta-Llama-3.3-70B-Instruct via existing `eval_sambanova_*` settings |

## Open Decisions Unaffected by This Record

| OD | Description | Status |
|----|-------------|--------|
| OD #1 | DeepEval metric thresholds | OPEN |
| OD #2 | Abstention Accuracy formula | OPEN |
| OD #3 | Bootstrap / CI methodology | OPEN |
| OD #4 | Cache implementation | OPEN |
| OD #5 | Evidence overlap algorithm | OPEN |
| OD #7 | Human-review interface/disagreement signal | OPEN |
| OD #8 | CLI/API surface | OPEN |
| OD #9 | Benchmark versioning convention | OPEN |
| OD #11 | Accepted-case count / benchmark population floor | OPEN |
| OD #12 | Candidate determinism policy | OPEN |

---

## Phase 5 Boundary

This document is the only deliverable of Phase 5a.

Phase 5b implements `CaseAggregator` against this decision. No implementation
begins until this document is committed to `docs/decisions/` on `main`.

The `docs/decisions/` directory is created by the commit that adds this file.

---

## Schema-Conformance Amendment

This amendment clarifies the schema-conformance interpretation of the OD-10 implementation behavior and supersedes any conflicting illustrative text in the original decision.

### A. Frozen Schema Authority
The schema defined in `docs/Phase 3/benchmark_case.schema.json` is authoritative for the serialized benchmark case verification structure and remains strictly frozen. This ADR does not authorize the addition of serialized properties that the frozen schema does not permit.

### B. Correction of Illustrative Example
The original ADR's illustrative verification block included top-level fields such as `unsupported_claims`, `contradictions`, and `reason`. These fields are NOT permitted as top-level properties of the `verification` object under the frozen schema. The previous example is purely illustrative and MUST NOT be interpreted as permission to add schema-forbidden properties.

### C. Secondary Failure / Unavailable / Timeout
The earlier wording describing secondary failure as resulting in `human_review` is explicitly corrected. The authoritative Phase 5b implementation behavior for secondary failure (unavailable, timeout, exception, or an exact accepted/rejected response parsing failure) is:
- `primary.verdict = "disputed"`
- `secondary = null`
- `verification.verdict = "disputed"`

### D. Human Review
`human_review` remains `null` for this OD-10 automated aggregation path. Future human-review behavior remains governed by the relevant unresolved Open Decision (OD #7) and is NOT resolved by this amendment.

### E. Transient / Final Semantics
The meaning of the `disputed` verdict is clarified as follows:
- Primary `disputed` means the primary verifier found an unsupported-claim case eligible for secondary adjudication.
- While the secondary verifier is running, `disputed` is the transient primary state.
- If the secondary verifier succeeds, the final case verdict becomes `accepted` or `rejected`.
- If the secondary verifier fails, is unavailable, times out, or returns an invalid response, the final automated case verdict remains `disputed`.
- Such disputed cases must follow the existing population/admission rules and must NOT be silently treated as accepted or rejected.

### F. Schema-Compliant Secondary Object
When secondary verification succeeds, the populated `secondary` object must conform exactly to the frozen schema and may only contain fields explicitly allowed by that schema.

### G. No Other OD Changes
This amendment changes only the schema-conformance interpretation of OD-10 implementation behavior and does not resolve or modify any other Open Decisions.

---

## Approval

Reviewed and approved prior to Phase 5b implementation.
