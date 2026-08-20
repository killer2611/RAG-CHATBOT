# Phase 3C Reconnaissance / Integration Plan

## 1. Executive Summary
This document outlines the reconnaissance and integration plan for Phase 3C: Adversarial Semantic Verification. It is strictly based on the current repository state, examining the exact output of the 3B generator and the downstream frozen schema. It establishes the rigid boundary between 3B (which emits a structurally valid partial candidate with a hollow verification stub) and 3C (which is responsible for performing claim-level semantic verification). This pass introduces no implementation changes and preserves all protected open decisions.

## 2. Repository State
**OBSERVED:**
- **Files Inspected:** `app/evaluation/candidates.py`, `app/evaluation/generator_v3.py`, `app/evaluation/provenance.py`, `app/evaluation/judges.py`, `app/evaluation/runner.py`, `docs/Phase 3/benchmark_case.schema.json`, `docs/Phase 3/3b_implementation_plan.md`, `docs/Phase 3/3b_3_integration_plan.md`.
- **Current 3B Status:** 3B-1, 3B-2, and 3B-3 are locked. 3B produces a `PartialBenchmarkCandidate` containing source-local retrieval fields and a hollow verification stub.
- **Existing 3C Infrastructure:** No dedicated Phase 3C verification logic exists.
- **Git State:** OBSERVED: The working tree contains the pre-existing Phase 3 configuration modification in `app/core/config.py` plus the Phase 3 implementation/test/plan artifacts. No new tracked modifications were introduced by this reconnaissance pass. All legacy Phase 1/2 systems are completely unmodified.

## 3. 3B → 3C Handoff Contract
**OBSERVED** `app/evaluation/candidates.py::PartialBenchmarkCandidate`
- The handoff object is a `PartialBenchmarkCandidate`, serialized via `to_dict()`.
- **Present:** `case_id`, `question`, `expected_answer`, `answerability`, `question_type`, `topics`, `source`, `evidence`, `claims`, `version`, and `verification` (as a hollow stub).
- **Conditionally Absent:** `corpus_position` (within `retrieval_profile`) is absent when position is mathematically underivable from the document (e.g., TXT files).
- **Intentionally Absent:** `distractor_profile` and `retrieval_risk` are absent from the `retrieval_profile` block since 3B lacks corpus-global context.
- **Preserved:** Identity fields must pass through unmodified.

## 4. PartialBenchmarkCandidate Actual Shape
**OBSERVED** `app/evaluation/candidates.py::PartialBenchmarkCandidate.to_dict()`
The actual structure emitted by 3B is structurally a partial `BenchmarkCase`. It must NOT be passed to the final frozen JSON Schema validator. The verification block is present but structurally hollow (all semantic verdicts are `None` or `[]`).

## 5. Verification Stub → Semantic Verification Lifecycle
**OBSERVED** `app/evaluation/candidates.py::HollowVerificationStub`
- **3B Responsibility:** Emits the structure (`verdict=None`, empty lists for `verified_by`, `unsupported_claims`, `contradictions`, and `reason=None`). 3B performs ZERO claim-support or semantic evaluation.
- **3C Responsibility:** Consumes the stub and populates the missing semantic evaluations based on the claims and evidence, yielding a semantically populated verification block.

Lifecycle:
`hollow verification stub` → `3C semantic evaluation` → `semantically populated verification` → `final completed BenchmarkCase`

## 6. Provenance vs Semantic Support Boundary
**OBSERVED** `app/evaluation/provenance.py::ProvenanceResolver`
- 3B establishes **Provenance Existence**: "Does the proposed quote exist exactly in the original document?"
- 3C must establish **Semantic Support**: "Does the exact quote semantically support the generated claim?"
- **INFERRED:** 3C receives canonical evidence and claim lists. 3C must independently verify semantic entailment. The presence of evidence does NOT automatically imply claim support.

## 7. Claim-Level Verification Model
**OBSERVED** `docs/Phase 3/benchmark_case.schema.json`
- Verification occurs per case but evaluates claims. The `primary` verification block requires a `verdict`, `claims_checked` (array of claim IDs), and `unsupported_claims`.
- The case-level verdict evaluates to `accepted`, `rejected`, `disputed`, or `human_review`.
- **INFERRED:** 3C must iterate over claims, assessing each claim against its mapped `evidence_ids`.
- **UNKNOWN:** The final policy for mixed cases (e.g., 1 supported, 1 unsupported claim) leading to final `rejected` or `accepted` status.

3C MUST NOT invent case-level verdict aggregation semantics for mixed claim outcomes. For example, it must not arbitrarily implement 'any unsupported claim => rejected' or 'any supported claim => accepted' unless that behavior is explicitly established by the frozen contract or an approved decision.

3C may establish and record claim-level semantic verification results, but the mapping from mixed claim-level outcomes to the case-level verification verdict must remain explicitly unresolved unless the repository/frozen contract already defines it.

This preserves the distinction between claim-level semantic evidence and final benchmark acceptance policy.

## 8. Retrieval Profile / Deferred corpus_position
**OBSERVED** `app/evaluation/candidates.py::PartialBenchmarkCandidate.to_dict()`
- `retrieval_profile.evidence_scope` is populated.
- `retrieval_profile.corpus_position` is conditionally omitted if the source document lacks physical page structure and string-offset calculations fail.
- **INFERRED:** 3C must explicitly recognize that a missing `corpus_position` is a **deferred** state, not a structural validation failure. 3C must NOT fail the candidate for lacking this key.

## 9. Staged Validation Architecture
**INFERRED** Based on the handoff shape:
- **Stage A (Partial-Candidate Validation):** 3C structural checks. Ensures `case_id`, claims, and evidence exist. Ensures the hollow verification stub is present. Missing `corpus_position`, `distractor_profile`, and `retrieval_risk` are permitted.
- **Stage B (Final Complete-Case Validation):** Executed only after 3C verification and Corpus-Global Enrichment are complete. Executes `jsonschema.validate(case, frozen_schema)`.

## 10. Primary / Secondary Verification
**OBSERVED** `docs/Phase 3/benchmark_case.schema.json`
- The schema defines `primary` (required) and `secondary` (optional) verifier results.
- **INFERRED:** Secondary verification is invoked when the primary verification verdict is `disputed`.
- **UNKNOWN / OPEN DECISION:** Which model performs secondary verification remains unresolved (Open Decision #6).

## 11. Existing DeepEval / Judge Infrastructure
**OBSERVED** `app/evaluation/runner.py` and `app/evaluation/judges.py`
- DeepEval is currently integrated in `runner.py` for legacy Phase 1/2 evaluation. It evaluates generated outputs against golden expectations using metrics like Faithfulness and AnswerRelevancy.
- Judges are configured via `build_judge` returning `deepeval.models.GPTModel` (which throws a deprecation warning, untouched).
- **INFERRED:** Existing metrics do not natively map to Phase 3C semantic claim verification. 3C requires a custom evaluation step to check claim/evidence support.

## 12. Cost and LLM Call Boundary
**INFERRED:**
- INFERRED: Semantic verification will require one or more bounded verifier LLM invocations, potentially batched, subject to the approved verification cost model.
- Secondary verifier calls should only occur if the primary result is `disputed`.
- The exact verification cost model must follow: Cheap/Local Structural Checks → Semantic LLM Primary Call → Secondary Call (Only if needed).

Before any LLM call, 3C MUST perform all cheap/local/deterministic checks available from the partial candidate.

The implementation must NOT create an unbounded per-claim, per-evidence, or per-retry LLM call loop.

In particular:
- no automatic LLM call per claim unless explicitly justified and bounded by the approved verification cost model;
- no LLM call per evidence span;
- no compensating generation/verification calls merely because a local filter rejects an item;
- malformed structured verifier output must use a bounded, explicitly tested retry policy rather than an unbounded loop;
- secondary verification must occur only under its explicitly defined trigger and must remain bounded.

The eventual 3C implementation must include tests that make its LLM invocation boundaries observable and prove that cheap/local checks occur before semantic LLM verification.

## 13. Failure and Fallback Behavior
**INFERRED:**
- **Local Structural Failure:** Dropped immediately (e.g., invalid partial candidate).
- **Semantic Verification Failure:** Documented in the verification block (e.g., unsupported claims → rejected).
- **Infrastructure Failure:** LLM API timeouts or malformed JSON should bubble up as exceptions or trigger bounded retries, distinct from semantic rejection.

## 14. Identity Continuity
**OBSERVED** `app/evaluation/candidates.py`
- `case_id`, `evidence_id`, and `claim_id` are passed through untouched from 3B.
- **INFERRED:** 3C consumes these IDs to map claims to evidence. 3C must NEVER regenerate these IDs.
- Candidate determinism remains unresolved (Open Decision #12).

## 15. Verification Output Contract
**OBSERVED** `docs/Phase 3/benchmark_case.schema.json`
The semantically populated verification block after 3C must match the frozen schema.
Illustrative 3C intermediate output — NOT a final schema-complete BenchmarkCase:
```json
{
  "case_id": "...",
  "question": "...",
  "answerability": "answerable",
  "expected_answer": "...",
  "source": {
    "source_name": "...",
    "source_id": "...",
    "document_hash": "...",
    "document_type": "legal",
    "type_confidence": 0.95
  },
  "evidence": [...],
  "claims": [...],
  "verification": {
    "verdict": "accepted",
    "primary": {
      "verdict": "accepted",
      "claims_checked": ["claim_1"],
      "unsupported_claims": [],
      "reason": "All claims strongly supported."
    },
    "secondary": null,
    "human_review": null
  },
  "retrieval_profile": {
    "evidence_scope": "multi_span"
  },
  "version": {
    "schema_version": "...",
    "benchmark_version": "..."
  }
}
```
**Important:** 3B populates the verification structure's shape but leaves all semantic verdict fields empty/null. 3C is responsible for populating semantic verification results. If 3B were to populate a semantic verdict, it would violate the 3B/3C boundary and constitute self-grading.
Also explicitly document that `corpus_position` itself may be absent when the current 3B source-local derivation cannot legitimately determine it. That absence MUST NOT be treated as candidate rejection.

Explicitly:
- evidence_scope may already be populated by 3B;
- corpus_position may be absent/deferred;
- distractor_profile and retrieval_risk remain deferred because they require corpus-global context;
- the example must NOT be interpreted as passing final frozen-schema validation.

Final frozen-schema validation occurs only after all required retrieval_profile fields have been populated by the appropriate corpus-aware enrichment stage and 3C semantic verification is complete.

## 16. Corpus-Global Enrichment Ownership
**INFERRED** from `docs/Phase 3/3b_3_integration_plan.md`
- `distractor_profile` and `retrieval_risk` require corpus-wide context.
- 3C focuses purely on semantic verification of the single case and its local evidence.
- INFERRED: `distractor_profile` and `retrieval_risk` require corpus-global context unavailable to 3B. A later corpus-aware enrichment stage is therefore required. Whether that stage is formally designated Phase 3D remains an architectural sequencing decision and is NOT resolved by this reconnaissance pass.

## 17. Human Review Boundary
**OBSERVED** `docs/Phase 3/benchmark_case.schema.json`
- `human_review` is an optional block in the `verification` object. A verdict can be `human_review`.
- **UNKNOWN / OPEN DECISION:** What triggers human review and the interface to handle it remain unresolved (Open Decision #7).

## 18. Acceptance / Filtering Boundary
**INFERRED:**
- 3C emits the semantically verified case.
- A final acceptance gate must eventually decide which cases are formally admitted to the final benchmark.
- **UNKNOWN / OPEN DECISION:** The final acceptance thresholds and filtered counts remain unresolved (Open Decisions #10, #11).

## 19. Protected Open Decisions
ALL TWELVE decisions remain OPEN DECISION — NOT RESOLVED:
1. Exact DeepEval thresholds
2. Abstention Accuracy
3. Bootstrap Methodology
4. Cache Implementation
5. Evidence Overlap / Normalization
6. Secondary Verifier Model
7. Human-Review Interface
8. CLI/API Surface
9. Benchmark Versioning
10. Phase 3 Acceptance Thresholds
11. Accepted-Case Count After Filtering
12. Candidate Determinism

## 20. Risks / Unknowns
- **UNKNOWN:** The exact prompt structure needed to instruct the primary LLM to reliably map claims to evidence.
- **UNKNOWN:** The exact algorithm for mapping claim `evidence_ids` against multiple distinct evidence spans during the LLM evaluation.

## 21. Recommended 3C Implementation Sequence
1. Implement Stage A structural validation (ignoring deferred corpus fields).
2. Create the Primary Semantic Verifier module isolated from Phase 1/2.
3. Map claims to evidence and invoke the primary verifier.
4. Populate the semantically rich `verification` block.
5. Defer final `jsonschema.validate` until corpus enrichment.

*Implementation Constraint*: 3C MUST NOT invent case-level verdict aggregation semantics for mixed claim outcomes. Before any LLM call, 3C MUST perform all cheap/local/deterministic checks available from the partial candidate. The implementation must NOT create an unbounded per-claim, per-evidence, or per-retry LLM call loop.

3C may iterate over claims locally to construct and validate the claim-to-evidence mapping. This does NOT imply one LLM call per claim.

The default implementation should construct a bounded verification input containing the case's claims and their mapped canonical evidence, and perform semantic verification according to the approved verification cost model.

No per-claim or per-evidence LLM call pattern may be introduced merely because claims are processed individually in local code.

## 22. Definition of Done
- [x] Inspected actual current 3B implementation
- [x] Inspected actual PartialBenchmarkCandidate serialization
- [x] Inspected actual frozen schema
- [x] Inspected actual verification structure
- [x] Inspected actual provenance boundary
- [x] Inspected actual existing DeepEval/judge infrastructure
- [x] Defined the 3B → 3C handoff
- [x] Explicitly handled missing corpus_position
- [x] Distinguished provenance existence from semantic support
- [x] Defined the intended claim-level verification boundary
- [x] Described primary vs secondary verification
- [x] Identified cost/call boundaries
- [x] Described failure modes
- [x] Preserved identity continuity
- [x] Defined staged validation
- [x] Identified corpus-global enrichment ownership
- [x] Preserved all 12 protected open decisions
- [x] Preserved Phase 1/2 safety
- [x] Preserved frozen-schema safety
- [x] Created docs/Phase 3/3c_reconnaissance_plan.md
- [x] Made no implementation changes
- [x] Made no schema changes
- [x] Made no live API calls
- [x] Generated no candidates

## 23. Explicit STOP Condition
Reconnaissance is complete. Implementation of 3C MUST NOT begin until explicit human review and approval is granted.
