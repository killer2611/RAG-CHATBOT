# Phase 3D-3 Architecture Audit
## Independent R&D / Benchmark Infrastructure Hostile Review

**Audit Date:** 2026-08-24
**Auditor Role:** Independent Senior R&D / Benchmark Infrastructure Reviewer
**Repository HEAD:** `5ba033a feat: implement Phase 3D-2 enrichment boundaries` (OBSERVED)
**Working Tree:** Clean (OBSERVED — only `3d3_reconnaissance_plan.md` and this audit document are untracked)
**Audit Subject:** `docs/Phase 3/3d3_reconnaissance_plan.md`
**Standard:** Is the proposed 3D-3 scope architecturally correct, repository-supported, minimal, safe, mechanism/policy separated, and appropriate for production-grade benchmark infrastructure?

---

## 1. Executive Verdict

> **YELLOW**

The reconnaissance plan is **partially correct** but contains **one architectural proposal that must be rejected** and **one dangerous implicit assumption** that, if enacted, would normalize a semantically incorrect validation boundary.

The plan correctly identifies what remains blocked by open decisions, correctly locates the persistence boundary, and correctly acknowledges the `ArtifactWriter` gap. These are genuine contributions.

However, the plan's "smallest production-grade mechanism" answer (Section 23 Critical Design Question) proposes to:

> "execute `StructuralValidator` against `IntermediateVerificationResult.partial_case_dict` extracted from the final `UnresolvedPolicyError`"

This is **wrong**. Running the frozen schema validator against a known-incomplete intermediate object — and designing tests whose only purpose is to prove it fails — is not a useful production-grade mechanism. It conflates three fundamentally different states: schema-invalid, policy-blocked, and benchmark-inadmissible. It would produce a test that proves nothing except "incomplete objects fail the schema," which is true by construction and provides zero trust boundary value.

Furthermore, the exception-transport audit question (Section 6 of the recon plan: "UNKNOWN: How the pipeline catches the final UnresolvedPolicyError to route to a final validation/persistence boundary without blurring the error semantics") is the most important open question in the 3D-3 design space. The plan correctly identifies it as UNKNOWN — but then proposes an implementation that answers it badly without acknowledging the contradiction.

The correct 3D-3 scope is: implement `ArtifactWriter` as a named, tested, production-quality mechanism — **not** a `NotImplementedError` stub — so that it proves the persistence invariant directly and creates the correct 3E handoff surface. Do not wire `StructuralValidator` to the intermediate object. Do not add it to the orchestrator's exception handler.

Required corrections are minor in implementation effort but significant in architectural clarity. They can be applied before implementation begins.

---

## 2. Repository Evidence

All claims below are tagged with their evidence classification. The following files were directly inspected.

| File | Role | Location |
|------|------|----------|
| `orchestrator.py` | 3D pipeline orchestrator | `app/evaluation/orchestrator.py` |
| `aggregator.py` | CaseAggregator (3D-2) | `app/evaluation/aggregator.py` |
| `enrichment.py` | CorpusEnricher (3D-2) | `app/evaluation/enrichment.py` |
| `exceptions.py` | Exceptions taxonomy | `app/evaluation/exceptions.py` |
| `finalizer.py` | StructuralValidator + ArtifactWriter | `app/evaluation/finalizer.py` |
| `verifier_v3.py` | Phase 3C verifier + IntermediateVerificationResult | `app/evaluation/verifier_v3.py` |
| `candidates.py` | PartialBenchmarkCandidate | `app/evaluation/candidates.py` |
| `generator_v3.py` | 3B candidate generator | `app/evaluation/generator_v3.py` |
| `provenance.py` | Provenance resolver | `app/evaluation/provenance.py` |
| `config.py` | Settings | `app/core/config.py` |
| `test_3d_orchestrator.py` | Orchestrator tests | `tests/test_3d_orchestrator.py` |
| `test_3d2_enrichment.py` | Enrichment tests | `tests/test_3d2_enrichment.py` |
| `test_3d_finalizer.py` | Finalizer tests | `tests/test_3d_finalizer.py` |
| `benchmark_case.schema.json` | Frozen schema | `docs/Phase 3/benchmark_case.schema.json` |
| `3d3_reconnaissance_plan.md` | Audit subject | `docs/Phase 3/3d3_reconnaissance_plan.md` |
| `3d_reconnaissance_plan.md` | Locked 3D recon plan | `docs/Phase 3/3d_reconnaissance_plan.md` |
| `3d1_architecture_audit.md` | Prior audit | `docs/Phase 3/3d1_architecture_audit.md` |
| `phase3_contract_hardening.md` | Semantic invariants | `docs/Phase 3/phase3_contract_hardening.md` |

**Git state (OBSERVED):**

```
5ba033a feat: implement Phase 3D-2 enrichment boundaries
98838f8 fix: harden Phase 3D-1 after architecture audit
d919f24 feat: establish Phase 3D-1 pipeline infrastructure
75e21b3 feat: complete Phase 3B and 3C benchmark pipeline
dbfcb3f feat: production-grade evaluation infrastructure
9adb2f4 feat: complete flagship RAG platform
```

**3D-2 commit scope (OBSERVED):** 7 files changed — `aggregator.py`, `enrichment.py`, `exceptions.py`, `orchestrator.py`, `verifier_v3.py`, `test_3d2_enrichment.py`, `test_3d_orchestrator.py`. Zero Phase 1/2 files modified.

---

## 3. Reconnaissance Claims Verified

| Claim | Source in Plan | Evidence | Verdict |
|-------|---------------|---------|---------|
| HEAD is `5ba033a` | Sec 2 | `git log` [OBSERVED] | VERIFIED |
| Working tree is clean | Sec 2 | `git status` [OBSERVED] | VERIFIED |
| 3D-2 preserved all 12 ODs | Sec 2 | No OD resolution in `5ba033a` commit scope [OBSERVED] | VERIFIED |
| BenchmarkAdmissionError raised when corpus_position missing | Sec 3 | `enrichment.py` lines 39-43 [OBSERVED] | VERIFIED |
| UnresolvedPolicyError raised after corpus_position check | Sec 3 | `enrichment.py` lines 55-59 [OBSERVED] | VERIFIED |
| verification.primary.claims_checked assembled by 3D-2 | Sec 3 | `aggregator.py` line 33 [OBSERVED] | VERIFIED |
| verification.primary.unsupported_claims assembled by 3D-2 | Sec 3 | `aggregator.py` line 34 [OBSERVED] | VERIFIED |
| verification.verdict remains None | Sec 3 | `aggregator.py` line 30 [OBSERVED] | VERIFIED |
| verification.primary.verdict remains None | Sec 3 | `aggregator.py` line 32 [OBSERVED] | VERIFIED |
| verification.primary.reason remains None | Sec 3 | `aggregator.py` line 35 [OBSERVED] | VERIFIED |
| distractor_profile absent — policy blocked | Sec 3 | `enrichment.py` lines 52-59 [OBSERVED] | VERIFIED |
| retrieval_risk absent — policy blocked | Sec 3 | `enrichment.py` lines 52-59 [OBSERVED] | VERIFIED |
| verification.secondary is Optional (schema) | Sec 4 | Schema lines 238-257: `anyOf: [ref, null]` [OBSERVED] | VERIFIED |
| verification.human_review is Optional (schema) | Sec 4 | Schema lines 248-257: `anyOf: [ref, null]` [OBSERVED] | VERIFIED |
| ArtifactWriter raises NotImplementedError | Sec 11 | `finalizer.py` lines 43-44 [OBSERVED] | VERIFIED |
| StructuralValidator exists | Sec 11 | `finalizer.py` lines 6-28 [OBSERVED] | VERIFIED |
| Cost model: zero new LLM/API calls required | Sec 12 | No LLM imports in `finalizer.py` [OBSERVED] | VERIFIED |
| CorpusEnricher raises UnresolvedPolicyError for distractor/risk | Sec 5 | `enrichment.py` lines 55-59 [OBSERVED] | VERIFIED |
| Finalizer schema path uses absolute resolution | Sec 11 | `finalizer.py` lines 11-17 (uses `Path(__file__).resolve()...`) [OBSERVED] | VERIFIED (3D-1 audit finding remediated) |
| ArtifactWriter docstring references "3D-1" | Sec 11 | `finalizer.py` lines 40-43 [OBSERVED] | VERIFIED AS STALE (see Rejected Claims) |

---

## 4. Reconnaissance Claims Rejected

### Rejection #1 — Proposed Wiring of StructuralValidator to partial_case_dict Is Semantically Wrong

**Plan claim (Sec 23 Critical Design Question):** "The smallest production-grade mechanism is to wire `StructuralValidator` into `Phase3DOrchestrator` so that it formally executes against the `IntermediateVerificationResult.partial_case_dict` extracted from the final `UnresolvedPolicyError`."

**Rejection:** Running the final frozen schema validator against a known-incomplete intermediate object is not a production-grade invariant; it is a demonstration. The `IntermediateVerificationResult.partial_case_dict` is, by design, incomplete: it lacks `distractor_profile`, `retrieval_risk`, `verification.verdict`, and `verification.primary.verdict`. Validating it against the frozen schema will always produce a validation failure — not because the data is wrong, but because policies are blocked by open decisions.

This conflates three fundamentally different states:

- **Schema-invalid**: The data violates the schema structure.
- **Policy-blocked**: The data is structurally consistent but cannot be completed until OD resolutions.
- **Benchmark-inadmissible**: The case fails a semantic admission invariant.

Mixing these into a single `ValueError` from `StructuralValidator.validate()` teaches future callers nothing useful. `StructuralValidator.validate()` contract is: "this is a complete, assembled case — does it satisfy the frozen schema?" Feeding it a partial case by design is wrong usage. [INFERRED — supported by `candidates.py` lines 15-20 explicitly prohibiting frozen schema validation on partial candidates]

**Corrected position:** `StructuralValidator` must only be called when a case is claimed to be complete. See Audit 7.

### Rejection #2 — ArtifactWriter NotImplementedError Stub Is No Longer Appropriate

**Plan claim (Sec 11):** "3D-3 owns the implementation of the persistence mechanism" — but the proposed scope seems to treat `ArtifactWriter` as remaining a stub.

**Rejection:** The `ArtifactWriter.write_case()` docstring still says "Persistence is blocked until Phase 3D-2 establishes complete case policies" — which is now stale since 3D-2 is complete. [OBSERVED — `finalizer.py` lines 40-43] 3D-3 should implement `ArtifactWriter` as a real mechanism (accepting a `case_dict`, validating it independently, and writing to disk) with a clear contractual precondition: only complete, schema-valid cases may be passed. This is implementing the persistence **mechanism**, not the policy.

### Rejection #3 — Recon Plan Section 17 OD #9 Blocking Claim Is Incorrect

**Plan claim (Sec 17):** "OD #9 — UNRESOLVED — Yes (Prevents `benchmark_version` resolution)"

**Rejection:** `benchmark_version` is already populated. [OBSERVED — `generator_v3.py` line 335: `"benchmark_version": get_settings().phase3_benchmark_version`; `config.py` line 83: `phase3_benchmark_version: str = "3b-candidate"`]. OD #9 is about the semantic versioning *convention*, not whether the field can be populated. Schema validation will not fail on this field. 3D-3 is not blocked by OD #9 for any mechanism.

### Rejection #4 — Recon Plan Section 18 Dependency Graph Embeds the Rejected Wiring

**Plan claim (Sec 18):** `CaseAggregator → UnresolvedPolicyError / IntermediateVerificationResult → (Need to catch/route) → StructuralValidator → ArtifactWriter`

**Rejection:** This graph routes from `UnresolvedPolicyError` directly to `StructuralValidator`. This is the rejected Rejection #1 expressed as a dataflow diagram. The correct graph shows `StructuralValidator` only after complete policy resolution and normal case assembly — not as a post-exception handler. See Audit 7 and Section 16 (Safe Scope).

### Rejection #5 — ArtifactWriter Docstring Is Stale (Pre-existing, Inheritable in 3D-3)

**OBSERVED:** `finalizer.py` lines 40-43 references "3D-1 cannot produce a schema-complete BenchmarkCase." This was written during 3D-1 and not updated in 3D-2. 3D-3 must update this docstring to accurately describe the current contract.

---

## 5. Exception / Data Transport Audit (Audit 1)

### The current pipeline topology

**OBSERVED:**

```
Phase3CVerifier.verify_candidate(candidate)
    -> always raises UnresolvedPolicyError(partial_result=IntermediateVerificationResult)

Phase3DOrchestrator.run_pipeline() [annotated -> NoReturn]:
    catches UnresolvedPolicyError from verifier
    calls enricher.enrich(e.partial_result)
        -> BenchmarkAdmissionError (if corpus_position missing) — hard stop
        -> UnresolvedPolicyError(partial_result=enriched_result) — policy blocked
    catches UnresolvedPolicyError from enricher
    calls aggregator.aggregate(enrich_e.partial_result)
        -> UnresolvedPolicyError(partial_result=assembled_result) — OD #10 blocked
    return self.aggregator.aggregate(...)    <- returns NoReturn (always raises)
```

### A. Is `UnresolvedPolicyError` semantically an error?

**INFERRED — NO, not in the current pipeline context.**

`UnresolvedPolicyError` is used simultaneously as: (1) a signal that a policy has not been decided, (2) a carrier for a valid intermediate computation result, and (3) the primary control-flow mechanism of the 3D pipeline. Semantically, it is NOT an error in the traditional exception sense — it is a successful computation halted at a policy boundary. Using exception semantics is a design compromise explicitly acknowledged in `orchestrator.py` lines 27-34 ("TRANSITIONAL CONTROL FLOW" docstring). [OBSERVED]

### B. Is `IntermediateVerificationResult` a valid intermediate product?

**OBSERVED — YES, unambiguously.** It is a properly typed `@dataclass` (`verifier_v3.py` lines 16-24) carrying `partial_case_dict`, `claims_checked`, and `unsupported_claims`. The `CaseAggregator` further assembles `verification.primary` before re-raising — producing a genuinely richer intermediate state. [OBSERVED — `aggregator.py` lines 28-45]

### C. Is it correct to transport a successful intermediate computation inside an exception?

**INFERRED — Not ideal, but explicitly documented as transitional and functionally safe in the current phase.** The 3D-1 hardening commit (`98838f8`) added the "TRANSITIONAL CONTROL FLOW" docstring to `orchestrator.py`. [OBSERVED]

The mechanism is correct because: the exception is always caught by the orchestrator (never propagates to uncaught territory), the `partial_result` is always inspected before re-raising, and the `NoReturn` annotation correctly communicates that the orchestrator never returns normally.

When OD #10 resolves, `aggregate()` will return a completed `case_dict` normally. The orchestrator's `return self.aggregator.aggregate(...)` would then return to the caller, who would call `StructuralValidator.validate()` and `ArtifactWriter.write_case()` on the **return value** — not on an exception's payload.

### D. Does catching the final exception and treating `partial_case_dict` as normal data blur semantics?

**INFERRED — YES, if StructuralValidator is called inside the exception handler.**

If 3D-3 adds `StructuralValidator.validate(partial_case_dict)` inside the `except UnresolvedPolicyError` block, the pipeline's final observable state becomes ambiguous. The caller sees `ValueError("Schema validation failed: 'distractor_profile' is a required property")`. The caller CANNOT distinguish:
- "schema validation failed because data is corrupt"
- "schema validation failed because policies are blocked by ODs"

This would make the exception transport mechanism actively harmful to future debugging.

### E. Would a cleaner mechanism separate the intermediate state transport from the persistence boundary?

**INFERRED — YES.** The orchestrator should expose the final `UnresolvedPolicyError` (carrying the assembled intermediate result) as the output to a caller. The caller (a future pipeline driver) is responsible for the routing decision: if policies are resolved, assemble the complete case and call `StructuralValidator` + `ArtifactWriter`; if not, log the intermediate state and advance.

**3D-3 recommendation:** Do NOT refactor the exception transport in 3D-3. It is explicitly transitional and correctly documented. Extend the "TRANSITIONAL CONTROL FLOW" docstring to name what the future non-transitional path looks like. This is documentation-level work, not implementation.

---

## 6. ArtifactWriter Audit (Audit 2)

### 1. What does ArtifactWriter need to do?

**INFERRED:** Accept a `case_dict` that has passed `StructuralValidator.validate()`, then write it to persistent storage. JSON format, one file per case, named by `case_id`.

### 2. Does its existence provide value before a complete case can legally exist?

**YES.** The mechanism proves: persistence is gated behind validation, the output format is decided, future callers cannot bypass validation to reach disk.

### 3. Could implementing it accidentally normalize persistence of incomplete cases?

**YES — if the implementation does not independently validate.** `ArtifactWriter.write_case()` MUST call `self.validator.validate(case_dict)` itself before writing. It must never trust that the caller has already validated.

### 4. What exact invariant must ArtifactWriter enforce?

> A case that reaches the write method and passes validation is structurally complete. A case that reaches the write method and fails validation produces an explicit `ValueError`. No case can be written to disk without passing schema validation.

### 5. Should ArtifactWriter accept only a schema-validated BenchmarkCase?

**YES — and it must independently validate rather than assuming the caller did so.**

### 6. Should it be completely inert until the final policy boundary exists?

**NO.** The mechanism should be implemented correctly now. It will simply not be reached in normal pipeline execution (since no complete case can currently be produced) — but it must exist in working state, not as a `NotImplementedError` stub.

### 7. Is 3D-3 the right phase to implement it?

**YES.** It is the final infrastructure phase. If `ArtifactWriter` is not implemented in 3D-3, the 3D infrastructure is not complete.

### Correct ArtifactWriter design for 3D-3

```python
class ArtifactWriter:
    def __init__(self, output_dir: str, validator: StructuralValidator):
        self.output_dir = Path(output_dir)
        self.validator = validator  # Injected — not hardcoded

    def write_case(self, case_dict: Dict[str, Any]) -> Path:
        """
        Persists a schema-validated BenchmarkCase to disk.

        Independently validates before writing. Never silently writes an invalid case.
        Raises ValueError if schema validation fails (from StructuralValidator).
        Creates output_dir if it does not exist.

        Returns the Path of the written file.
        """
        self.validator.validate(case_dict)   # Independent gate
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / f"{case_dict['case_id']}.json"
        out_path.write_text(json.dumps(case_dict, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path
```

---

## 7. StructuralValidator Semantics Audit (Audit 3)

### Is `partial_case_dict` intended to represent a final BenchmarkCase?

**OBSERVED — NO.** `candidates.py` module header (lines 15): "MUST NOT be passed to the final frozen BenchmarkCase schema validator." The `partial_case_dict` inside `IntermediateVerificationResult` is the serialized form of this partial object. Validating it against the frozen schema is explicitly prohibited by the established contract.

### Is schema validation of an intentionally incomplete intermediate object useful?

**INFERRED — NO, in the form proposed.** Running `StructuralValidator.validate(partial_case_dict)` when `partial_case_dict` is known to be incomplete will always fail because `distractor_profile` is absent, `retrieval_risk` is absent, `verification.verdict` is `None`, and `verification.primary.verdict` is `None`. The schema requires all of these. The validation will raise `ValueError: Schema validation failed: 'distractor_profile' is a required property`.

### Does this test prove anything beyond "incomplete objects fail the schema"?

**INFERRED — NO.** True by construction. A test asserting this is a tautology.

### Could this conflate schema-invalid with policy-blocked with benchmark-inadmissible?

**INFERRED — YES.** A caller catching `ValueError` from this validation cannot determine whether the failure means the data is structurally corrupt, or it is waiting for OD resolution, or it failed a semantic invariant. All three produce the same `ValueError`.

### What is the strongest useful invariant 3D-3 can actually prove?

> "`ArtifactWriter.write_case()` independently validates before writing. Any case that reaches the write method and passes validation is structurally complete. Any case that reaches the write method and fails validation is explicitly classified as such."

This is testable, meaningful, and does not require running the validator on a known-partial object. Drop the proposed validator wiring from the orchestrator. Test through `ArtifactWriter` instead.

---

## 8. Frozen Schema Field Inventory (Audit 4)

### Top-Level Required Fields — Status

| Field | Producer | Status | Policy Dep? | 3D-3 Action |
|-------|----------|--------|-------------|-------------|
| `case_id` | `generator_v3.py` (UUID) | Populated [OBSERVED] | No | None |
| `question` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `expected_answer` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `answerability` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `question_type` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `topics` | `generator_v3.py` | Populated (array or null) [OBSERVED] | No | None |
| `source` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `evidence` | `generator_v3.py` | Populated [OBSERVED] | No | None |
| `claims` | `generator_v3.py` + 3C | Populated with `support_status` [OBSERVED] | No | None |
| `verification` | `aggregator.py` | Structurally assembled; verdicts null [OBSERVED] | YES (OD #10) | None (blocked) |
| `retrieval_profile` | `generator_v3.py` (partial) | Partial; `distractor_profile` / `retrieval_risk` absent [OBSERVED] | YES | None (blocked) |
| `version` | `generator_v3.py` | Populated from config [OBSERVED] | Partial (OD #9 = semantic convention only) | None |

### verification Sub-Fields

| Field | Schema Req | Current Value | Policy Dep? | Schema will fail? |
|-------|-----------|--------------|-------------|------------------|
| `verification.verdict` | required enum | `None` [OBSERVED aggregator.py:30] | YES — OD #10 | **YES** — None is not a valid enum value |
| `verification.primary.verdict` | required enum | `None` [OBSERVED aggregator.py:32] | YES — OD #10 | **YES** |
| `verification.primary.claims_checked` | required array | Populated [OBSERVED aggregator.py:33] | No | No |
| `verification.primary.unsupported_claims` | optional array | Populated [OBSERVED aggregator.py:34] | No | No |
| `verification.primary.reason` | optional string/null | `None` [OBSERVED aggregator.py:35] | YES — OD #10 | No (null is allowed) |
| `verification.secondary` | optional anyOf[object, null] | `None` [OBSERVED aggregator.py:37] | YES — OD #6, #10 | No (null is allowed) |
| `verification.human_review` | optional anyOf[object, null] | `None` [OBSERVED aggregator.py:38] | YES — OD #7, #8 | No (null is allowed) |

**Critical finding:** `verification.verdict` (required, enum) and `verification.primary.verdict` (required within `verifier_result`) being `None` means any assembled case dict will ALWAYS fail `StructuralValidator`. This confirms the tautological nature of the proposed 3D-3 wiring. [OBSERVED — schema lines 221-237, 421-428]

### retrieval_profile Sub-Fields

| Field | Schema Req | Current Value | Policy Dep? | Schema will fail? |
|-------|-----------|--------------|-------------|------------------|
| `evidence_scope` | required enum | Populated by 3B [OBSERVED candidates.py:41] | No | No |
| `corpus_position` | required enum | Populated when derivable; enforced by CorpusEnricher [OBSERVED] | No (Option A locked) | No (for admitted cases) |
| `distractor_profile` | required enum | **ABSENT** [OBSERVED candidates.py:43] | YES | **YES** — `'distractor_profile' is a required property` |
| `retrieval_risk` | required enum | **ABSENT** [OBSERVED candidates.py:44] | YES | **YES** |

**Note:** `distractor_profile` and `retrieval_risk` are not null — they are **absent** from the dict entirely. Schema uses `additionalProperties: false` and marks them `required`. An absent required field produces a different error from a null value. [OBSERVED — schema lines 518-556]

### version Sub-Fields

| Field | Schema Req | Current Value | OD #9 Blocks? |
|-------|-----------|--------------|--------------|
| `schema_version` | required string | From config [OBSERVED] | No |
| `benchmark_version` | required string | `"3b-candidate"` from config [OBSERVED — config.py:83, generator_v3.py:335] | **No — field is populated** |
| `generator_prompt_version` | optional | From config [OBSERVED] | Semantic only |
| `verifier_prompt_version` | optional | From config [OBSERVED] | Semantic only |

**Recon plan correction confirmed:** OD #9 does NOT prevent `benchmark_version` from being populated. [OBSERVED]

---

## 9. Open Decision Audit (Audit 5)

All 12 ODs individually audited. No OD is resolved.

| OD | Decision | Code Evidence | Blocks 3D-3 Mechanism? | Status |
|----|----------|--------------|----------------------|--------|
| #1 | DeepEval thresholds | No references in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #2 | Abstention Accuracy | No references in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #3 | Bootstrap Methodology | No references in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #4 | Cache Implementation | No references in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #5 | Evidence overlap/normalization | `provenance.py` line 111 acknowledges [OBSERVED] | No | **UNRESOLVED** |
| #6 | Secondary verifier model | `aggregator.py` sets `secondary: None` [OBSERVED]; no implementation | No | **UNRESOLVED** |
| #7 | Human-review interface | `aggregator.py` sets `human_review: None` [OBSERVED]; no implementation | No | **UNRESOLVED** |
| #8 | CLI/API surface | Not referenced in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #9 | Benchmark versioning convention | `benchmark_version` populated from config [OBSERVED] | **No — field is populated** | **UNRESOLVED** (convention only) |
| #10 | Phase 3 acceptance thresholds | `aggregator.py` blocks explicitly [OBSERVED]; `verdict = None` | YES — no complete case can be produced | **UNRESOLVED** |
| #11 | Accepted-case count | Not referenced in 3D code [OBSERVED] | No | **UNRESOLVED** |
| #12 | Candidate determinism | UUID generation flagged in code [OBSERVED] | No | **UNRESOLVED** |

**VERDICT: All 12 ODs remain UNRESOLVED.** [CONFIRMED]

**OD #9 correction:** Recon plan Sec 17 claims OD #9 blocks 3D-3. This is wrong. `benchmark_version` is already populated. OD #9 does not prevent any 3D-3 mechanism from proceeding. [OBSERVED — see Rejection #3]

---

## 10. Persistence Trust Boundary (Audit 6)

### Required invariants for a case to reach persistence

| Invariant | Enforceable in 3D-3? | Mechanism | Notes |
|-----------|---------------------|-----------|-------|
| 1. Structural schema validation passes | YES | `StructuralValidator.validate()` inside `ArtifactWriter.write_case()` | Gate must be inside the writer |
| 2. Benchmark admission passes | YES (existing) | `CorpusEnricher.enrich()` enforces `corpus_position` required [OBSERVED enrichment.py:39-43] | Already enforced in 3D-2 |
| 3. Policy-dependent fields legitimately resolved | NO — OD #10 unresolved | Cannot be enforced until OD #10 resolves | `verdict` and `primary.verdict` currently `None` |
| 4. Provenance requirements satisfied | YES (existing 3B/3C mechanism) | `document_hash`, `span_hash`, `quote` populated by 3B [OBSERVED candidates.py] | No 3D-3 work needed |
| 5. No unresolved policy boundary remains | NO — multiple ODs unresolved | Schema validation fails if attempted on incomplete case | Why ArtifactWriter currently raises NotImplementedError |

**Current state:** Persistence is blocked by the absence of any code path that reaches `ArtifactWriter.write_case()`. This is incidental protection (no caller exists) rather than a formal gate. 3D-3 must make the gate formal by implementing `write_case()` with independent validation. The gate will correctly reject incomplete cases while providing a known-correct mechanism for when policies resolve.

---

## 11. Cost Firewall Audit (Audit 8)

| 3D-3 Component | New LLM calls | New embeddings | New API calls | New candidate generation | Verdict |
|---------------|--------------|--------------|--------------|-------------------------|---------|
| `ArtifactWriter.write_case()` | 0 | 0 | 0 | 0 | SAFE [INFERRED] |
| `StructuralValidator` inside `ArtifactWriter` | 0 | 0 | 0 | 0 | SAFE [OBSERVED] |
| Tests | 0 | 0 | 0 | 0 | SAFE [INFERRED] |

**VERDICT:** 3D-3 introduces zero new LLM/API/embedding calls. [INFERRED — confirmed by scope analysis]

---

## 12. 3D to 3E Contract Audit (Audit 11)

**Repository evidence for 3E:** None. Phase 3E is not defined anywhere in the repository. [OBSERVED]

**What 3D-3 should establish for 3E (minimum, not invented):**

| 3E Likely Need | 3D-3 Provides? | Status |
|----------------|----------------|--------|
| Persisted BenchmarkCase JSON artifacts | YES — `ArtifactWriter` writes `{case_id}.json` | 3D-3 mechanism |
| Consistent file naming convention | YES — by `case_id` | 3D-3 defines |
| Output directory configuration | YES — `output_dir` parameter | 3D-3 mechanism |
| Schema-validated complete case | Mechanism YES; actual cases NO until ODs resolve | 3D-3 gates; cannot produce yet |
| Per-claim reasoning traces | NO — not in `IntermediateVerificationResult` | Pre-existing gap; not 3D-3 scope |
| Case-level verdict | NO — OD #10 | Not 3D-3 scope |

**VERDICT:** 3D-3 should establish the `ArtifactWriter` persistence mechanism as the 3E handoff surface. 3E can reliably consume files from the output directory. No 3E contract should be invented beyond what the mechanism naturally defines.

---

## 13. Minimality Analysis (Audit 9)

### Scope A: Only formal validation wiring (Rejected)

Implement `StructuralValidator` into the orchestrator's exception handler.

**Assessment: REJECTED.** Semantically wrong (Audits 1, 3). Produces no useful production invariant. Conflates policy-blocked with schema-invalid. Not production-grade.

### Scope B: ArtifactWriter mechanism + tests (CORRECT)

Implement `ArtifactWriter.write_case()` with independent validation. Tests prove complete cases write, invalid cases are rejected, no bypass possible, zero LLM calls.

**Assessment: CORRECT MINIMAL SCOPE.** Smallest addition that proves a meaningful new invariant and creates the 3E handoff surface. Completes 3D infrastructure. Does not resolve any OD.

### Scope C: ArtifactWriter + exception/control-flow refactor (Out of Scope)

Refactor the exception-based transport to use a `Result` type or explicit intermediate state object.

**Assessment: OUT OF SCOPE FOR 3D-3.** Non-trivial refactor touching orchestrator, aggregator, enrichment, verifier, and tests. The exception transport is explicitly transitional and documented. Refactoring it belongs to the post-OD-10-resolution implementation phase, not 3D-3 infrastructure.

### Scope D: ArtifactWriter + persistence + broader pipeline redesign (Forbidden)

**Assessment: FORBIDDEN.** No complete case can be produced until OD #10 resolves. Pipeline redesign is not the 3D-3 mandate.

### Verdict: Scope B only.

---

## 14. Test Adequacy (Audit 10)

### Recon plan's proposed tests — assessment

| Proposed Test | Valuable? | Reason |
|--------------|-----------|--------|
| "Prove Phase3DOrchestrator routes to StructuralValidator" | **NO — REJECTED** | Based on the rejected Scope A wiring. Orchestrator must NOT call StructuralValidator. |
| "Prove that an unresolved case fails StructuralValidator" | **NO — TAUTOLOGICAL** | Always true by construction. Proves nothing about the trust boundary. |
| "Prove zero live LLM calls" | **YES** | Valid cost firewall invariant. |

### Minimum high-value test set for 3D-3

| Test | What It Proves | Priority |
|------|----------------|---------|
| `test_artifact_writer_writes_valid_case` | Complete, schema-valid case is written to disk; file exists and is valid JSON | P0 |
| `test_artifact_writer_rejects_incomplete_case` | Incomplete case (null verdicts) raises `ValueError` before any write | P0 |
| `test_artifact_writer_rejects_missing_required_field` | Case missing `distractor_profile` raises `ValueError("Schema validation failed")` | P0 |
| `test_artifact_writer_no_write_on_validation_failure` | After validation failure, no file is written to `output_dir` | P0 |
| `test_artifact_writer_creates_output_dir` | If `output_dir` does not exist, it is created | P1 |
| `test_artifact_writer_filename_is_case_id` | Output file is named `{case_id}.json` | P1 |
| `test_artifact_writer_accepts_validator_injection` | `ArtifactWriter` accepts `StructuralValidator` by injection | P1 |
| `test_artifact_writer_zero_llm_calls` | No LLM/API invocation during write | P1 |
| `test_artifact_writer_does_not_mutate_input` | Input `case_dict` is not mutated during write or validation | P1 |
| Preserve `test_structural_validator_success` | Schema validator still works on complete cases | Keep |
| Preserve `test_structural_validator_failure` | Schema validator still rejects incomplete cases when called directly | Keep |
| Remove `test_artifact_writer_stub` | Superseded by real implementation tests | Remove |

---

## 15. Required Corrections

Ordered by priority. P0 must be resolved before implementation begins.

### Correction 1 [P0 — Must Fix Before Implementation]

**Drop the proposed StructuralValidator-in-exception-handler wiring.**

The Critical Design Question (Sec 23) answer is wrong. Do not wire `StructuralValidator` to `IntermediateVerificationResult.partial_case_dict` extracted from `UnresolvedPolicyError`. Replace with: implement `ArtifactWriter.write_case()` with internal independent validation.

### Correction 2 [P0 — Must Fix Before Implementation]

**Correct the OD #9 blocking claim in Section 17.**

`benchmark_version` is already populated from config. Remove or amend: "OD #9 concerns the semantic meaning of version strings and does not prevent `benchmark_version` from being populated as a non-empty string. 3D-3 is not blocked by OD #9."

### Correction 3 [P0 — Must Fix Before Implementation]

**Correct the Dependency Graph in Section 18.**

Remove `StructuralValidator` from the exception-catch routing chain. Correct graph: `StructuralValidator` appears only inside `ArtifactWriter.write_case()`, invoked only on a claimed-complete case after OD resolution.

### Correction 4 [P1 — Should Fix Before Implementation]

**Update `ArtifactWriter.write_case()` docstring.**

Remove the reference to "3D-1 cannot produce..." This was written during 3D-1 and is now stale. The new docstring should describe the 3D-3 contract: accepts a complete, claimed-valid case; independently validates; writes to disk; returns written path.

### Correction 5 [P1 — Should Fix Before Implementation]

**Add `StructuralValidator` injection to `ArtifactWriter.__init__()`.**

The current `ArtifactWriter` accepts only `output_dir`. For independent validation inside `write_case()`, it must accept a `StructuralValidator` instance. This keeps schema path configuration in one place and makes the dependency explicit.

### Correction 6 [P2 — Document Before Implementation]

**Extend `orchestrator.py`'s "TRANSITIONAL CONTROL FLOW" docstring.**

Add to the existing docstring: when OD #10 resolves, `aggregate()` will return a completed case dict normally. The caller of `run_pipeline()` must then invoke `StructuralValidator.validate()` and `ArtifactWriter.write_case()` on the returned case dict. This names the future correct routing and removes ambiguity for 3D-4/OD-resolution implementation.

---

## 16. Safe-to-Implement Scope

### File: `app/evaluation/finalizer.py`

1. Update `ArtifactWriter.__init__(output_dir, validator: StructuralValidator)` to accept injected validator
2. Implement `ArtifactWriter.write_case(case_dict)`: call `self.validator.validate(case_dict)`, create output_dir, write JSON, return path
3. Update docstring to describe 3D-3 contract
4. No changes to `StructuralValidator` itself

### File: `tests/test_3d_finalizer.py`

1. Remove `test_artifact_writer_stub`
2. Add minimum high-value test set from Section 14
3. Preserve `test_structural_validator_success` and `test_structural_validator_failure`

### Files explicitly unchanged

| File | Reason |
|------|--------|
| `orchestrator.py` | Do NOT add StructuralValidator call in exception handler (apply Correction 6 as documentation only) |
| `aggregator.py` | Complete for 3D-2; OD #10 correctly blocks it |
| `enrichment.py` | Complete for 3D-2 |
| `exceptions.py` | Complete |
| `verifier_v3.py` | 3C boundary unchanged |
| `candidates.py` | 3B handoff unchanged |
| `generator_v3.py` | 3B unchanged |
| `provenance.py` | Unchanged |
| `benchmark_case.schema.json` | Frozen — must not be touched |
| All Phase 1/2 files | Must not be touched |
| `test_3d_orchestrator.py` | Existing tests pass; no changes needed |
| `test_3d2_enrichment.py` | Existing tests pass; no changes needed |

---

## 17. Explicitly Forbidden Scope

| Forbidden Action | Reason |
|-----------------|--------|
| Wire `StructuralValidator` to `partial_case_dict` in orchestrator exception handler | Semantically wrong — conflates policy-blocked with schema-invalid |
| Call `StructuralValidator.validate()` on any partial/intermediate object | For complete cases only |
| Resolve OD #10 (verdict assignment logic) | OD #10 remains unresolved |
| Invent `distractor_profile` or `retrieval_risk` values | OD-blocked; no classification logic may be added |
| Invent verdict rules | OD #10 |
| Refactor exception-based control flow | Transitional and documented; not 3D-3 scope |
| Modify the frozen schema | Frozen |
| Modify Phase 1/2 code | Protected |
| Make live LLM/API calls | Cost firewall |
| Generate benchmark candidates | Out of scope |
| Persist any incomplete benchmark case | Core invariant |
| Reintroduce string-index corpus_position fallback | Locked — Option A only |
| Add `distractor_profile: "none"` or `retrieval_risk: "low"` as defaults | Silent policy invention |
| Add verdict defaulting logic of any kind | Would silently encode OD #10 policy |

---

## 18. Final Verdict

> **YELLOW**

**Why not RED:** The plan does not invent policy, does not invent thresholds, does not fabricate verdicts, and correctly identifies `ArtifactWriter` as 3D-3 scope. The baseline inventory facts are accurate and verified.

**Why not GREEN:** The plan's "smallest production-grade mechanism" answer proposes a semantically incorrect validation wiring that conflates distinct failure modes, violates the established contract on partial candidates, and produces only tautological tests.

**Why YELLOW and not RED-YELLOW border:** The corrections are well-defined and can be applied before implementation begins without requiring a redesign. The incorrect wiring is a scope error (don't implement the orchestrator wiring at all) that is fully correctable.

**After applying 6 required corrections, the safe implementation scope is GREEN.**

---

## 19. Stop Conditions

### Verified as of this audit:

- [x] No Python source files modified — `git diff --stat HEAD` is empty [OBSERVED]
- [x] No test files modified [OBSERVED]
- [x] No schema modified — `benchmark_case.schema.json` unchanged [OBSERVED]
- [x] No Phase 1/2 code modified [OBSERVED]
- [x] No live LLM/API calls made [OBSERVED]
- [x] No candidates generated [OBSERVED]
- [x] No OD resolved — all 12 confirmed UNRESOLVED [VERIFIED]
- [x] No verdict logic invented [CONFIRMED]
- [x] No distractor/risk policy invented [CONFIRMED]
- [x] corpus_position Option A lock maintained — string-index fallback already removed in 3D-1 hardening [OBSERVED]
- [x] Audit document created: `docs/Phase 3/3d3_architecture_audit.md` [OBSERVED]
- [x] Git status: only two untracked documents (`3d3_reconnaissance_plan.md`, `3d3_architecture_audit.md`) [OBSERVED]
- [x] `git diff --check` passes [OBSERVED]

### Implementation may begin only after:

1. Correction 1 (P0): Recon plan Sec 23 Critical Design Question is updated to remove `StructuralValidator`-in-exception-handler wiring
2. Correction 2 (P0): Recon plan Sec 17 OD #9 blocking claim is corrected
3. Correction 3 (P0): Recon plan Sec 18 Dependency Graph is corrected
4. Implementation scope is confirmed as Scope B only (ArtifactWriter mechanism + tests)
5. Human authorization is received

**DO NOT IMPLEMENT ANYTHING FROM THIS AUDIT WITHOUT EXPLICIT HUMAN AUTHORIZATION.**

---

*All findings labelled OBSERVED are directly confirmed from repository source code. All findings labelled INFERRED are architectural necessities or risks not directly stated in code. All findings labelled UNKNOWN are not established by the repository. No protected Open Decision has been resolved by this audit. No implementation changes were made. No tests were added or modified. No live API calls were made. No candidates were generated.*
