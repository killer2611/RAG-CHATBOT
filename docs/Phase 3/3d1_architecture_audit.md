# Phase 3D-1 Architecture Audit
## Independent R&D / Benchmark Infrastructure Hostile Review

**Audit Date:** 2026-08-24
**Auditor Role:** Independent Senior R&D / Benchmark Infrastructure Reviewer
**Repository HEAD:** `d919f24 feat: establish Phase 3D-1 pipeline infrastructure`
**Preceding Commit:** `75e21b3 feat: complete Phase 3B and 3C benchmark pipeline`
**Audit Scope:** Phase 3D-1 infrastructure layer only (orchestrator, aggregator, finalizer, supporting tests)
**Standard:** Can this architecture produce a trustworthy, reproducible, inspectable benchmark once unresolved policies are eventually supplied?

---

## 1. Executive Verdict

> **GREEN WITH CONDITIONS**

Phase 3D-1 is architecturally honest and structurally sound at the mechanism layer. The four new files (`orchestrator.py`, `aggregator.py`, `finalizer.py`, `test_3d_orchestrator.py`, `test_3d_finalizer.py`) together implement a genuine mechanism skeleton: they wire 3C output to a holding boundary, prevent premature persistence, and document what remains blocked by OD #10. No policy has been invented. No case-level verdict has been fabricated.

However, five specific conditions must be addressed before 3D-2 begins. Two are **architectural risks** of non-trivial scope. Three are **documentation/test gaps** that will not surface as runtime failures today but will cause correctness ambiguity later.

These conditions are identified below. They are not fatal to the current architecture; they are pre-conditions for 3D-2 safety. None requires a redesign.

---

## 2. Repository Evidence

The following files were directly inspected as the evidence base for this audit. All claims below are tagged with their evidence source.

| File | Role | Location |
|------|------|----------|
| `orchestrator.py` | 3D-1 orchestrator | `app/evaluation/orchestrator.py` |
| `aggregator.py` | CaseAggregator boundary | `app/evaluation/aggregator.py` |
| `finalizer.py` | StructuralValidator + ArtifactWriter | `app/evaluation/finalizer.py` |
| `test_3d_orchestrator.py` | Orchestrator tests | `tests/test_3d_orchestrator.py` |
| `test_3d_finalizer.py` | Finalizer tests | `tests/test_3d_finalizer.py` |
| `verifier_v3.py` | Phase 3C verifier (pre-existing) | `app/evaluation/verifier_v3.py` |
| `candidates.py` | PartialBenchmarkCandidate (pre-existing) | `app/evaluation/candidates.py` |
| `generator_v3.py` | 3B candidate generator (pre-existing) | `app/evaluation/generator_v3.py` |
| `provenance.py` | Provenance resolver (pre-existing) | `app/evaluation/provenance.py` |
| `loaders.py` | File loaders (pre-existing) | `app/rag/loaders.py` |
| `retriever.py` | Hierarchical retriever (pre-existing) | `app/rag/retriever.py` |
| `judges.py` | DeepEval judge factory (pre-existing) | `app/evaluation/judges.py` |
| `benchmark_case.schema.json` | Frozen schema | `docs/Phase 3/benchmark_case.schema.json` |
| `3d_reconnaissance_plan.md` | Locked recon plan | `docs/Phase 3/3d_reconnaissance_plan.md` |
| `3c_reconnaissance_plan.md` | 3C plan | `docs/Phase 3/3c_reconnaissance_plan.md` |
| `3b_implementation_plan.md` | 3B plan | `docs/Phase 3/3b_implementation_plan.md` |
| `3b_3_integration_plan.md` | 3B-3 integration plan | `docs/Phase 3/3b_3_integration_plan.md` |
| `phase3_contract_hardening.md` | Semantic invariants | `docs/Phase 3/phase3_contract_hardening.md` |

**Git state (OBSERVED):**
`d919f24` introduced exactly 5 files (aggregator, finalizer, orchestrator, test_3d_finalizer, test_3d_orchestrator). Zero pre-existing files were modified. The working tree is clean except for the untracked `3d_reconnaissance_plan.md` (which is a pre-3D-1 plan document, not a 3D-1 implementation artifact).

---

## 3. Reconnaissance-to-Implementation Conformance (Audit 1)

Cross-referencing every commitment in `3d_reconnaissance_plan.md` against the 3D-1 implementation.

| Requirement (from Recon Plan) | Evidence | Status | Risk | Recommendation |
|-------------------------------|----------|--------|------|----------------|
| **R1:** Phase3DOrchestrator must exist as explicit handoff adapter | `orchestrator.py` lines 7-40 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R2:** Orchestrator must catch UnresolvedPolicyError from 3C | `orchestrator.py` line 29 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R3:** Orchestrator must extract IntermediateVerificationResult from exception | `orchestrator.py` line 37 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R4:** Orchestrator must raise RuntimeError if UnresolvedPolicyError lacks partial_result | `orchestrator.py` lines 30-32 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R5:** Orchestrator must raise RuntimeError if verifier returns normally | `orchestrator.py` lines 39-40 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R6:** CaseAggregator boundary must exist | `aggregator.py` lines 4-19 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R7:** CaseAggregator must raise UnresolvedPolicyError (OD #10 firewall) | `aggregator.py` lines 16-18 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R8:** CaseAggregator must re-carry partial_result | `aggregator.py` line 18 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R9:** StructuralValidator (final schema gate) must be established | `finalizer.py` lines 6-26 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R10:** ArtifactWriter must exist and raise NotImplementedError | `finalizer.py` lines 29-42 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R11:** Orchestrator must deepcopy the caller-owned input (no mutation) | `orchestrator.py` line 25 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R12:** 3D-1 must introduce zero LLM/API calls | See Audit 11 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R13:** HollowVerificationStub must NOT be falsely represented as final verification | NotImplementedError in ArtifactWriter; final schema not satisfied [OBSERVED] | **A - Correctly implements** | Low | None |
| **R14:** StructuralValidator must use frozen-schema jsonschema.validate only | `finalizer.py` line 24 [OBSERVED] | **A - Correctly implements** | Low | None |
| **R15:** StructuralValidator must never silently repair/coerce invalid input | `finalizer.py` lines 23-26 raises ValueError [OBSERVED] | **A - Correctly implements** | Low | None |
| **R16:** Recon Section 22 "Stage 3 - Case Aggregation": must expose policy hook | `aggregate()` accepts typed arg [OBSERVED], but has no injectable policy parameter [OBSERVED] | **B - Partially implements** | **Medium** | See Red Flag #3 |
| **R17:** Corpus Enrichment mechanism - Recon Sec 22 Stage 1 | Explicitly NOT implemented (3D-2 work) [OBSERVED] | **D - Intentionally unimplemented** | Low (expected) | None |
| **R18:** Secondary / Human Review integration - Recon Sec 22 Stage 4 | Not implemented (3D-2+ work) [OBSERVED] | **D - Intentionally unimplemented** | Low (expected) | None |
| **R19:** UnresolvedPolicyError must NOT be treated as permanent pipeline control-flow | Recon plan Sec 20 warns of this; implementation relies on it as the primary output path [INFERRED] | **E - Introduces risk not resolved by plan** | **Medium** | See Red Flag #2 |
| **R20:** corpus_position admission boundary must be explicit when position not derivable | No 3D-1 mechanism enforces this at the 3D boundary; silently passes through from 3B as None [OBSERVED] | **B - Partially implements** | **High** | See Red Flag #1 |

**Summary:** 17 of 20 requirements correctly implemented. R16 is a partial implementation with medium risk. R19 and R20 are the two most significant non-conformances.

---

## 4. Mechanism vs. Policy Audit (Audit 2)

**OBSERVED:** The following policy decisions are inspected:

| Policy Area | File/Line | Finding | Severity |
|-------------|-----------|---------|---------|
| case verdict accepted/rejected/disputed/human_review | None found in 3D-1 [OBSERVED] | Not present - OD #10 firewall intact | Safe |
| acceptance threshold | None found in 3D-1 [OBSERVED] | Not present | Safe |
| secondary verification trigger | None found [OBSERVED] | Not present | Safe |
| human-review trigger | None found [OBSERVED] | Not present | Safe |
| retrieval-risk threshold | None found [OBSERVED] | Not present | Safe |
| distractor threshold | None found [OBSERVED] | Not present | Safe |
| candidate admission policy | None found [OBSERVED] | Not present | Safe |
| accepted-case filtering policy | None found [OBSERVED] | Not present | Safe |

**VERDICT:** The mechanism vs policy firewall is correctly maintained throughout 3D-1. No hidden policy exists in the four new files.

**INFERRED caveat:** The recon plan (Section 20) explicitly warns that `UnresolvedPolicyError` is the *current* 3C boundary transport mechanism and "must NOT be treated as the permanent 3D pipeline control-flow or candidate-admission policy." The 3D-1 orchestrator currently relies on catching this exception as its primary (and only) output path. This is architecturally correct for the *current* phase, but creates a coupling risk that will need explicit attention when OD #10 resolves. See Red Flag #2.

---

## 5. IntermediateVerificationResult Boundary Audit (Audit 3)

**OBSERVED:** `verifier_v3.py::IntermediateVerificationResult` (lines 16-24):

```python
@dataclass
class IntermediateVerificationResult:
    partial_case_dict: Dict[str, Any]
    claims_checked: List[str]
    unsupported_claims: List[str]
```

**Finding 1:** `claims_checked` is a **top-level field** on `IntermediateVerificationResult`. It is NOT `verification.primary.claims_checked`. [OBSERVED]

**Finding 2:** `unsupported_claims` is a **top-level field** on `IntermediateVerificationResult`. It is NOT `verification.primary.unsupported_claims`. [OBSERVED]

**Finding 3:** `partial_case_dict` is the working candidate dictionary - not the final schema-compliant case. [OBSERVED]

**Finding 4:** 3D-1 does NOT conflate `IntermediateVerificationResult.claims_checked` with `verification.primary.claims_checked`. The aggregator boundary simply re-raises the `UnresolvedPolicyError`, preserving the intermediate object intact. [OBSERVED]

**Finding 5:** The orchestrator test (`test_3d_orchestrator.py` line 98) correctly asserts on `partial_result.claims_checked` (the intermediate field), not on any `verification.primary.*` path. [OBSERVED]

**VERDICT:** No semantic conflation of intermediate fields with final schema fields was found. The boundary is correctly maintained. This is a strong point of the 3D-1 implementation.

---

## 6. Verification Architecture Audit (Audit 4)

**OBSERVED** layering:

```
HollowVerificationStub (3B output)
    |
IntermediateVerificationResult (3C output, claim-level populated)
    |
[CaseAggregator boundary - BLOCKED by OD #10]
    |
verification.primary (DOES NOT EXIST in 3D-1)
    |
final verification block (DOES NOT EXIST in 3D-1)
    |
case-level verdict (DOES NOT EXIST in 3D-1)
```

**Finding 1:** 3D-1 does NOT pretend the final verification structure exists. The `ArtifactWriter.write_case()` raises `NotImplementedError` explicitly. [OBSERVED]

**Finding 2:** The `StructuralValidator` in `finalizer.py` IS able to validate a complete case if one were assembled - and the test `test_structural_validator_success` passes a fully-assembled case with `verification.verdict = "accepted"` and `verification.primary`. This is correct behavior: the test exercises the schema gate with a deliberately complete case fixture. [OBSERVED]

**Finding 3:** The `StructuralValidator` test fixture in `test_3d_finalizer.py` (lines 12-47) successfully validates a case with `verification.verdict = "accepted"`. It is NOT fabricating a verdict in the pipeline - it is exercising the schema validator correctly. However, it creates potential documentation confusion: it could mislead a future developer into thinking the schema gate alone is sufficient for admission. [INFERRED risk]

**Finding 4:** No values are fabricated to satisfy the schema in the production pipeline path. [OBSERVED]

**VERDICT:** Correctly layered. No hollow stub is presented as a final verification block in any production code path.

---

## 7. Schema vs. Trustworthiness Audit (Audit 5)

**OBSERVED:** `StructuralValidator.validate()` (`finalizer.py` lines 17-26) wraps `jsonschema.validate()` and converts `ValidationError` to `ValueError`. It does not coerce, repair, or silently drop invalid cases.

**Finding 1:** jsonschema validation is correctly positioned as the structural gate only - not an admission decision. [OBSERVED]

**Finding 2:** The recon plan explicitly states the invariant: `schema-valid != benchmark-admissible != benchmark-trustworthy`. The `StructuralValidator` docstring correctly echoes: "Establishes structural conformance only." [OBSERVED]

**Finding 3:** The `ArtifactWriter.write_case()` raises `NotImplementedError`, so no semantically incomplete case can currently reach persistence even if it passes schema validation. [OBSERVED]

**Finding 4 [CONCERN]:** The `test_structural_validator_success` fixture uses `distractor_profile: "none"` and `retrieval_risk: "low"` as test values. A case reaching `StructuralValidator` with these values in a real pipeline would have required corpus-aware enrichment that does not yet exist. There is no application-level guard in `StructuralValidator` that checks whether `distractor_profile` was legitimately derived vs. fabricated. [INFERRED risk - relevant to 3D-2]

**Finding 5:** The schema's `allOf` conditional logic (lines 259-410 of schema) encodes secondary-verification rules. These conditions are schema-enforced structural constraints, not policy decisions. They are correctly treated as mechanical gates, not admission decisions. [OBSERVED]

**VERDICT:** The schema-vs-trustworthiness invariant is respected at the code level. The test fixture creates potential future confusion but is not a current production risk.

---

## 8. `corpus_position` Admission Audit (Audit 6)

This is the most important architectural finding.

**LOCKED DECISION from Recon Plan Sec 13:**
> TXT/DOCX candidates for which authoritative `corpus_position` cannot be established must produce an **explicit, inspectable admission failure** - NOT be silently dropped or assigned a heuristic.

**OBSERVED implementation in `generator_v3.py` (`_derive_corpus_position`, lines 175-231):**

The implementation has **two paths:**

**Path A - PDF with page data:** Uses `min_page / total_pages` as `position_ratio`, maps to start/middle/end via equal tertiles. This is page-structure-based derivation. [OBSERVED]

**Path B - String-index fallback (lines 208-219):**
```python
elif full_text and resolved_evidence:
    first_idx = -1
    for ev in resolved_evidence:
        idx = full_text.find(ev["quote"])
        ...
    if first_idx != -1 and len(full_text) > 0:
        position_ratio = first_idx / len(full_text)
```

This path applies when `pages_with_data` is empty but evidence quotes are present in `full_text`. **This path is reached by TXT and DOCX sources.** [OBSERVED]

**Critical Finding:** The locked decision in `3d_reconnaissance_plan.md` Section 13 explicitly states:
> *"A string-offset percentage is NOT the current benchmark definition of corpus_position. Do not substitute character position for authoritative structural position merely to satisfy the schema."*

The string-index fallback in `generator_v3.py` does exactly this: it assigns a string-character-position ratio as the basis for `corpus_position` on TXT/DOCX files. This is a **direct violation of the locked architectural decision.** [OBSERVED]

**Mitigating factor:** The code comment on `_derive_corpus_position` (lines 191-194) says "This is a provisional implementation." This acknowledges provisional status but does **not** acknowledge the explicit prohibition on string-offset substitution. The comment does not reference the locked decision. [OBSERVED]

**Consequence:** TXT/DOCX candidates can currently receive a `corpus_position` value derived from string index, which:
1. Violates the locked architectural decision
2. Produces a value that is syntactically valid ("start"/"middle"/"end")
3. But is NOT derived from authoritative structural information

**On the None path:** When `corpus_position = None` (quote not found in full_text), `PartialBenchmarkCandidate.to_dict()` correctly omits `corpus_position` (lines 128-129). The partial case then fails final schema validation (schema requires `corpus_position` as required string). This protection is currently **incidental** - it relies on the schema requiring the field, not on an explicit named admission boundary.

**On PDF-hardcoding:** The implementation does NOT hardcode `extension == ".pdf"` as a permanent whitelist. The abstraction is based on whether `page` metadata is available from `provenance_resolver.get_page_count()`, which returns `0` for TXT/DOCX. The intent is architecturally correct but the string-index fallback undermines it. [OBSERVED]

**VERDICT: P0 architectural finding.** See Red Flag #1.

---

## 9. Failure Semantics Audit (Audit 7)

| Failure Type | File/Location | Behavior | Safe? |
|-------------|---------------|----------|-------|
| `UnresolvedPolicyError` (with partial_result) | `orchestrator.py:29-37` | Routed to aggregator; re-raised with result. Inspectable. | Yes |
| `UnresolvedPolicyError` (without partial_result) | `orchestrator.py:30-32` | Raises `RuntimeError`. Explicit. | Yes |
| Verifier returns normally (contract violation) | `orchestrator.py:39-40` | Raises `RuntimeError`. Explicit. | Yes |
| `StructuralValidationError` from 3C | Not caught by orchestrator [OBSERVED] | Propagates upward. Caller must handle. | INFERRED risk - see Finding 1 |
| `RuntimeError` from LLM call failure | Not caught by orchestrator [OBSERVED] | Propagates upward. Caller must handle. | INFERRED risk - see Finding 1 |
| Schema validation failure | `finalizer.py:23-26` | Raises `ValueError`. Explicit. | Yes |
| ArtifactWriter called | `finalizer.py:36-42` | Raises `NotImplementedError`. Explicit and correct. | Yes |
| Missing corpus_position | Schema gate rejects at `StructuralValidator` | Incidental guard (see Audit 6) | Partial |
| Zero-claim answerable case entering 3C | `verifier_v3.py:221-223` | Raises `UnresolvedPolicyError` WITHOUT `partial_result` | OBSERVED gap - see Finding 2 |

**Finding 1 [INFERRED]:** The orchestrator catches `UnresolvedPolicyError` specifically, and separately catches the case where the verifier returns normally. However, it does NOT explicitly catch `StructuralValidationError` or `RuntimeError` from within the verifier. These propagate to the orchestrator's caller. There is no documented caller contract for the orchestrator. The test does not test what the caller does when these occur. This is an undocumented failure path.

**Finding 2 [OBSERVED]:** `verifier_v3.py` line 223 raises `UnresolvedPolicyError("Case-level aggregation policy for zero-claim cases...")` **without a `partial_result`**. The orchestrator handles this by re-raising as `RuntimeError("UnresolvedPolicyError did not contain IntermediateVerificationResult")`. This means a zero-claim case causes a `RuntimeError` that stops the pipeline. The semantics are defensible, but the distinction between "zero claims" and "structural failure" is flattened into the same `RuntimeError` path - a future caller cannot distinguish them programmatically.

**Finding 3 [INFERRED]:** There is no documented recovery or retry semantics in 3D-1. Whether failures should be logged, retried, or escalated is not established. Appropriate for the current phase but must be addressed in 3D-2.

---

## 10. Persistence Safety Audit (Audit 8)

**Tracing the path from `PartialBenchmarkCandidate` to persistence:**

```
PartialBenchmarkCandidate (3B)
    |
    v to_dict() - produces partial dict, corpus fields absent
Phase3CVerifier.verify_candidate()
    |
    v always raises UnresolvedPolicyError
Phase3DOrchestrator.run_pipeline()
    |
    v catches UnresolvedPolicyError, routes to aggregator
CaseAggregator.aggregate()
    |
    v raises UnresolvedPolicyError (OD #10 firewall)
[No further execution - caller receives exception]
ArtifactWriter.write_case() - NEVER CALLED in current pipeline
    |
    v would raise NotImplementedError if called
```

**OBSERVED:** No incomplete candidate can reach persistence in 3D-1. The protection exists via two independent mechanisms:
1. `CaseAggregator.aggregate()` always raises `UnresolvedPolicyError` - the pipeline never produces a completed case
2. `ArtifactWriter.write_case()` raises `NotImplementedError` unconditionally

**Finding:** The persistence protection is **explicit**, not incidental. Both guards are independently sufficient. This is a positive finding. [OBSERVED]

**Finding 2:** There is no execution path in 3D-1 where `ArtifactWriter.write_case()` is actually called. It exists purely as a named boundary stub. [OBSERVED]

**Finding 3:** The `StructuralValidator` is instantiated and tested, but is NOT wired into any execution path in 3D-1. It is a standalone boundary whose position in the final pipeline is documented but not yet enforced programmatically. [OBSERVED]

---

## 11. Cost Firewall Audit (Audit 9)

**OBSERVED:** 3D-1 introduces 3 new production files: `orchestrator.py`, `aggregator.py`, `finalizer.py`.

| Component | LLM/API calls introduced | Evidence |
|-----------|--------------------------|----------|
| `Phase3DOrchestrator` | 0 | Calls `verifier.verify_candidate()` which is the existing 3C boundary. No additional calls. [OBSERVED] |
| `CaseAggregator` | 0 | Pure exception raising. [OBSERVED] |
| `StructuralValidator` | 0 | Pure `jsonschema.validate()` call. [OBSERVED] |
| `ArtifactWriter` | 0 | Raises `NotImplementedError` immediately. [OBSERVED] |

**OBSERVED:** The orchestrator test (`test_3d_orchestrator.py` line 106) includes an explicit cost firewall assertion:
```python
mock_structured_llm.ainvoke.assert_awaited_once()
```
This proves exactly ONE LLM invocation (the existing 3C verifier call) occurs through the full pipeline. [OBSERVED]

**VERDICT:** Zero new LLM/API calls introduced by 3D-1. Cost firewall is intact and proven by test. [OBSERVED]

---

## 12. Reproducibility Audit (Audit 10)

| Source of Nondeterminism | Location | Status |
|--------------------------|----------|--------|
| UUID generation for `case_id`, `claim_id`, `ev_id` | `generator_v3.py` lines 268, 295, 318 | NONDETERMINISTIC - `uuid.uuid4()`. Acknowledged as OD #12. [OBSERVED] |
| `copy.deepcopy()` in orchestrator | `orchestrator.py:25` | Deterministic. [OBSERVED] |
| `copy.deepcopy()` in verifier | `verifier_v3.py:196` | Deterministic. [OBSERVED] |
| LLM call (3C) | `verifier_v3.py:253` | Nondeterministic unless LLM is deterministic. OD #12 pending. [OBSERVED] |
| Exception control-flow | `orchestrator.py:29-37` | Deterministic given same LLM output. [OBSERVED] |
| Timestamp generation | None found in 3D-1 [OBSERVED] | Not applicable |
| Filesystem ordering in provenance | `provenance.py` uses `document_dir.glob()` (line 53) | NONDETERMINISTIC for multi-file document dirs. Pre-existing. [OBSERVED] |
| Schema loading in StructuralValidator | `finalizer.py:14-15` - reads from file at init time | Deterministic for same schema file. [OBSERVED] |

**Finding 1:** UUID-based IDs are explicitly flagged as non-reproducible throughout the codebase. OD #12 remains unresolved and correctly documented. [OBSERVED]

**Finding 2:** `provenance.py::_find_document_path()` uses `glob()`. If two files match `{document_hash}.*`, only the first match is returned. Glob ordering is OS/filesystem-dependent. Pre-existing issue, not introduced by 3D-1. [OBSERVED]

**Finding 3:** 3D-1 itself introduces zero new nondeterminism. [OBSERVED]

---

## 13. Provenance Audit (Audit 11)

| Field | 3B Origin | 3C Handling | 3D Handling | Status |
|-------|-----------|-------------|-------------|--------|
| `case_id` | UUID (non-reproducible) | Preserved in `partial_case_dict` | Preserved by deepcopy | OK (OD #12) |
| `claim_id` | UUID (non-reproducible) | Used as key for claim mapping | Preserved in `partial_case_dict` | OK (OD #12) |
| `evidence_id` | UUID (non-reproducible) | Preserved in `partial_case_dict` | Preserved in `partial_case_dict` | OK (OD #12) |
| `span_hash` | SHA-256 of quote bytes | Preserved | Preserved in `partial_case_dict` | OK |
| `document_hash` | SHA-256 of source bytes | Preserved in `source` block | Preserved in `partial_case_dict` | OK |
| `source_name` / `source_id` | From provenance resolver | Preserved | Preserved in `partial_case_dict` | OK |
| `support_status` (per-claim) | Not set by 3B (answerable) | Set by 3C LLM, stored in `partial_case_dict.claims[*].support_status` | Preserved by deepcopy | OK |
| `claims_checked` | Not in 3B | Top-level on `IntermediateVerificationResult` | Re-raised in `UnresolvedPolicyError.partial_result` | OK |
| `unsupported_claims` | Not in 3B | Top-level on `IntermediateVerificationResult` | Re-raised in `UnresolvedPolicyError.partial_result` | OK |
| Generator model provenance | `version.generator_prompt_version` from config | Preserved | Preserved | OK (OD #9) |
| Verifier model provenance | `version.verifier_prompt_version` from config | Preserved | Preserved | OK (OD #9) |
| `benchmark_version` | From config | Preserved | Preserved | OK (OD #9) |
| Per-claim LLM `reason` | Not in 3B | Set on `ClaimVerification.reason` | NOT in `IntermediateVerificationResult` | GAP - see Finding 3 |

**Finding 1:** All identity fields survive 3B to 3C to 3D without corruption. [OBSERVED]

**Finding 2:** The verifier uses `copy.deepcopy()` before modifying `working_case`, and the orchestrator also uses `copy.deepcopy()` on the caller-owned input. The intermediate result in `partial_case_dict` is therefore a deepcopy of the original candidate. [OBSERVED]

**Finding 3 [INFERRED for 3E]:** The `IntermediateVerificationResult` carries `claims_checked`, `unsupported_claims`, and `partial_case_dict`. This is sufficient for 3E to compare automated claim-level decisions against human reference cases. However, the per-claim LLM `reason` output is NOT preserved in `IntermediateVerificationResult` - it exists only in `ClaimVerification.reason` which is not stored after the claims loop. If 3E requires reasoning traces per claim, this must be addressed in 3D-2. [INFERRED]

---

## 14. 3E Compatibility Audit (Audit 12)

**Note:** The exact Phase 3E contract is UNKNOWN. This audit treats 3E as a future calibration consumer comparing automated decisions against human-reviewed references.

| Field needed for 3E | Present in 3D-1 output path? | Notes |
|--------------------|------------------------------|-------|
| `case_id` | Yes - preserved in `partial_case_dict` | [OBSERVED] |
| `claim_id` | Yes - preserved in `partial_case_dict` | [OBSERVED] |
| final `support_status` per claim | Yes - set in `partial_case_dict.claims[*].support_status` | [OBSERVED] |
| `span_hash` / evidence identity | Yes - in `partial_case_dict.evidence[*].span_hash` | [OBSERVED] |
| primary verifier verdict | No - does not exist yet. OD #10 blocks it | [OBSERVED] |
| case-level verdict | No - does not exist yet. OD #10 blocks it | [OBSERVED] |
| verifier model/version | Partially - in `version.verifier_prompt_version` (config-sourced) | [OBSERVED - OD #9 unresolved] |
| generator model/version | Partially - in `version.generator_prompt_version` | [OBSERVED - OD #9 unresolved] |
| `benchmark_version` | Yes - in `version.benchmark_version` | [OBSERVED] |
| `claims_checked` (intermediate) | Yes - top-level on `IntermediateVerificationResult` | [OBSERVED] |
| `unsupported_claims` (intermediate) | Yes - top-level on `IntermediateVerificationResult` | [OBSERVED] |
| Per-claim LLM reasoning | No - not preserved in `IntermediateVerificationResult` | [OBSERVED gap] |
| Secondary verification result | No - does not exist yet | [OBSERVED - expected] |
| Human-review state | No - does not exist yet | [OBSERVED - expected] |

**Finding:** 3D-1 preserves claim-level provenance fields adequately for future 3E consumption. The per-claim LLM `reason` is not preserved in the typed intermediate object. If 3E requires reasoning traces, this must be addressed in 3D-2. [INFERRED]

---

## 15. Corpus Enrichment Readiness (Audit 13)

**OBSERVED:** 3D-1 does NOT introduce any of the following:

- Vector database coupling beyond pre-existing `app/rag/retriever.py` [OBSERVED]
- `CorpusEnricher` class [OBSERVED - not present]
- Embedding strategy for 3D enrichment [OBSERVED - not present]
- Similarity threshold [OBSERVED - not present]
- Retrieval-risk formula [OBSERVED - not present]
- Candidate-set sequencing policy [OBSERVED - not present]
- Corpus indexing strategy [OBSERVED - not present]

**Finding:** The pre-existing `retriever.py` uses Chroma with HuggingFace embeddings and BGE reranking. This infrastructure exists for Phase 1/2 RAG, not for Phase 3 corpus enrichment. 3D-1 has not coupled to it for 3D purposes. Whether it will be reused for 3D corpus enrichment (`distractor_profile`, `retrieval_risk`) remains UNKNOWN, correctly left for 3D-2 reconnaissance. [OBSERVED]

**VERDICT:** 3D-1 is correctly mechanism-neutral on corpus enrichment. It has not overcommitted to any enrichment strategy.

---

## 16. Open Decision Firewall (Audit 14)

| OD | Name | Touched by 3D-1? | Implicitly encoded? | Risk | Status |
|----|------|-----------------|---------------------|------|--------|
| #1 | DeepEval thresholds | No | No | None | **UNRESOLVED** |
| #2 | Abstention Accuracy | No | No | None | **UNRESOLVED** |
| #3 | Bootstrap Methodology | No | No | None | **UNRESOLVED** |
| #4 | Cache Implementation | No | No | None | **UNRESOLVED** |
| #5 | Evidence Overlap / Normalization | No | No | None | **UNRESOLVED** |
| #6 | Secondary Verifier Model | No | No | None | **UNRESOLVED** |
| #7 | Human-Review Interface | No | No | None | **UNRESOLVED** |
| #8 | CLI/API Surface | No | No | None | **UNRESOLVED** |
| #9 | Benchmark Versioning | Referenced - config-sourced version strings used [OBSERVED], correctly flagged as provisional | No | Low | **UNRESOLVED** |
| #10 | Phase 3 Acceptance Thresholds | Referenced - CaseAggregator raises on it [OBSERVED], correctly blocked | No | None | **UNRESOLVED** |
| #11 | Accepted-Case Count After Filtering | No | No | None | **UNRESOLVED** |
| #12 | Candidate Determinism | UUID generation in 3B is pre-existing [OBSERVED], correctly flagged | No | None | **UNRESOLVED** |

**VERDICT:** All 12 protected Open Decisions remain UNRESOLVED. 3D-1 touches OD #9 and OD #10 only mechanically, without resolving either. [OBSERVED]

---

## 17. Test Architecture Audit (Audit 15)

### What the tests prove

**`test_3d_orchestrator_wiring()` claims and proof:**

| Claim | Proven? | Evidence |
|-------|---------|---------|
| Valid partial candidate enters pipeline | Yes | Lines 32-61 construct candidate, pipeline runs |
| No real LLM call | Yes | `mock_structured_llm` replaces `structured_llm` |
| Real 3C verifier boundary is exercised | Yes | `Phase3CVerifier(llm=mock_llm)` - real verifier instantiated |
| `UnresolvedPolicyError` caught correctly | Yes | `pytest.raises(UnresolvedPolicyError)` |
| Intermediate result populated | Yes | `partial_result.claims_checked == ["c1"]` |
| CaseAggregator receives it | Yes | Exception message confirms aggregator raised |
| OD #10 remains unresolved | Yes | "Case-level aggregation policy remains unresolved" in exception |
| No fabricated verdict | Yes | No `verdict` assertion - exception is the terminal state |
| Original candidate not mutated | Yes | `assert candidate == original_candidate` |
| No persistence | Yes | ArtifactWriter not in pipeline; exception terminates |
| Exactly ONE LLM call | Yes | `assert_awaited_once()` |

**`test_3d_orchestrator_verifier_returns_normally()`:** Proves contract violation raises `RuntimeError`. [OBSERVED]

**`test_3d_orchestrator_verifier_raises_without_partial_result()`:** Proves missing `partial_result` raises `RuntimeError`. [OBSERVED]

**`test_3d_finalizer.py`:** Proves `StructuralValidator` accepts valid case, rejects invalid case, and `ArtifactWriter` raises `NotImplementedError`. [OBSERVED]

### Critical missing tests (recommendations only - no tests added)

| Missing Test | Why It Matters | Priority |
|-------------|----------------|---------|
| `StructuralValidationError` propagation from 3C through orchestrator | A structurally invalid candidate entering `run_pipeline()` produces `StructuralValidationError` (not `UnresolvedPolicyError`), which the orchestrator doesn't catch. Caller behavior is untested. | **High** |
| `RuntimeError` from LLM failure propagation | What happens when the LLM call in 3C raises? Orchestrator doesn't catch it. | **High** |
| Unanswerable case through the full 3D pipeline | 3C raises `UnresolvedPolicyError` for unanswerable cases WITH partial_result and zero claims_checked. No 3D test exercises this path. | **Medium** |
| CaseAggregator mutation guard | Does the aggregator mutate the intermediate_result before re-raising? Currently not, but untested. | **Medium** |
| StructuralValidator with missing corpus_position | A partial case dict (missing `corpus_position`) should fail schema validation. No test proves this. | **Medium** |
| Schema path not found error | `StructuralValidator.__init__()` opens the schema file. No test verifies behavior when file is not at expected path. | **Low** |

### Test quality finding - `"test_scope"` invalid evidence_scope value

**[OBSERVED]** `test_3d_orchestrator.py` line 46: `"evidence_scope": "test_scope"`. This value is not in the frozen schema enum `["single_span", "multi_span"]`. The test is testing orchestrator pipeline wiring (not schema conformance), and the partial candidate never reaches `StructuralValidator` in the test, so it does not fail. But it means the orchestrator test exercises a case that would fail schema validation - which could mislead a future developer about what kinds of candidates are valid. [OBSERVED]

---

## 18. Interface / API Audit (Audit 16)

### `Phase3DOrchestrator`

```python
def __init__(self, verifier: Phase3CVerifier, aggregator: CaseAggregator)
async def run_pipeline(self, partial_candidate: Dict[str, Any]) -> Dict[str, Any]
```

**Finding 1:** Return type annotation is `-> Dict[str, Any]`, but `run_pipeline` never returns normally - it either raises `UnresolvedPolicyError` (via aggregator) or `RuntimeError`. The correct return type is `NoReturn`. [OBSERVED]

**Finding 2:** The verifier is typed as `Phase3CVerifier` (concrete class), not an abstract interface. Future substitution of a different verifier would require subclassing `Phase3CVerifier`. [INFERRED]

**Finding 3:** The aggregator is typed as `CaseAggregator` (concrete class), not an abstract interface. When OD #10 resolves, the aggregation policy would need to be injected by either:
  (a) subclassing `CaseAggregator` and passing the subclass in,
  (b) adding a policy callable to `CaseAggregator.__init__()`, or
  (c) rewriting `aggregate()`.
None requires a pipeline redesign, but option (c) is destructive. This partially implements Recon Stage 3. [OBSERVED / INFERRED]

### `CaseAggregator`

**Finding 4:** `aggregate()` is correctly typed as `NoReturn`. [OBSERVED]

**Finding 5:** The aggregator carries no state and has no injection surface for a future policy implementation. Appropriate for 3D-1 but will require extension in 3D-2. [OBSERVED]

### `StructuralValidator`

```python
def __init__(self, schema_path: str = "docs/Phase 3/benchmark_case.schema.json")
```

**Finding 6 [IMPORTANT]:** The default `schema_path` is a **relative path** resolved relative to the **current working directory** at instantiation time. If CWD is not the project root, the schema file will not be found and the constructor will raise `FileNotFoundError`. [OBSERVED]

The test `test_3d_finalizer.py` works around this by computing an absolute path:
```python
schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
```
Test and production code use different path-resolution strategies. The production default path will break in any non-standard invocation context. [OBSERVED]

### `ArtifactWriter`

**Finding 7:** `ArtifactWriter` accepts `output_dir` but does not validate it or create the directory. Since `write_case()` raises `NotImplementedError`, this is not currently a risk. When 3D-2 implements persistence, this will need validation. [INFERRED]

### OD #10 injection assessment

**Can OD #10 be resolved by replacing a policy implementation without rewriting the pipeline?**

INFERRED: Partially yes. The orchestrator accepts `CaseAggregator` by constructor injection. Creating a `ConcreteAggregator(CaseAggregator)` subclass that implements a real `aggregate()` method would leave `run_pipeline()` code unchanged - because `return self.aggregator.aggregate(...)` would then return a completed case dict normally. The `-> Dict[str, Any]` return type annotation mismatch would become semantically correct for the non-OD-10-blocked path. This is a well-designed forward compatibility path.

---

## 19. Adversarial Scenario Matrix (Audit 17)

| # | Scenario | Current Behavior | Safe? | Policy Required? | Severity |
|---|----------|-----------------|-------|-----------------|---------|
| 1 | Candidate has zero claims (answerable) | `verifier_v3.py:221-223` raises `UnresolvedPolicyError` WITHOUT `partial_result`; orchestrator converts to `RuntimeError` | Stops pipeline explicitly | No (structural) | Medium - caller cannot distinguish from other RuntimeErrors |
| 2 | Candidate has unsupported claims | 3C sets `support_status: "unsupported"` per claim; `unsupported_claims` populated in intermediate result; aggregator re-raises | Correct - verdict deferred | Yes (OD #10) | Low |
| 3 | Candidate has contradicted claims | Same as #2 - `support_status: "contradicted"` set | Correct - verdict deferred | Yes (OD #10) | Low |
| 4 | Candidate has missing evidence (zero evidence_ids on answerable claim) | `_validate_structure()` passes (see verifier comment lines 146-152). 3C sends empty canonical_evidence to LLM. | **Hidden risk** - LLM receives claim with zero evidence and may hallucinate support status | Yes (H-3 policy for supported with zero evidence) | **High** |
| 5 | Candidate has invalid evidence IDs | `_validate_structure()` catches dangling evidence_id references, raises `StructuralValidationError` | Safe | No | Low |
| 6 | TXT source with no authoritative corpus_position | String-index fallback may produce non-None `corpus_position` - violates locked decision | **Unsafe - see Audit 6** | Architecture | **P0** |
| 7 | DOCX source with no authoritative corpus_position | Same as #6 | **Unsafe** | Architecture | **P0** |
| 8 | PDF with malformed page metadata (no page numbers) | `pages_with_data` is empty; string-index fallback activates | **Unsafe for position derivation** | Architecture | Medium |
| 9 | 3C raises UnresolvedPolicyError without partial_result | `orchestrator.py:30-32` converts to `RuntimeError` | Explicit | No | Low |
| 10 | 3C returns unexpectedly (no exception) | `orchestrator.py:39-40` raises `RuntimeError("Verifier returned normally...")` | Explicit | No | Low |
| 11 | Aggregator receives malformed intermediate state | CaseAggregator raises `UnresolvedPolicyError` wrapping the malformed state | Passes through malformed state in partial_result | No (mechanical) | Medium |
| 12 | Schema validation fails | `StructuralValidator.validate()` raises `ValueError` | Explicit - never coerces | No | Low |
| 13 | ArtifactWriter receives incomplete case | Raises `NotImplementedError` immediately | Safe | No | Low |
| 14 | Future policy implementation returns invalid verdict | Schema `allOf` conditional logic may not catch all invalid verdict combinations depending on which if/then branch is triggered | Partially unsafe - depends on schema if/then semantics | Yes (policy must respect schema state machine H-7) | Medium |
| 15 | Future secondary verification fails | No secondary verification path exists in 3D-1 | Irrelevant for 3D-1 | Yes | Low |
| 16 | Human-review metadata is incomplete | No human-review path exists in 3D-1 | Irrelevant for 3D-1 | Yes | Low |

---

## 20. Architectural Red Flags (Audit 18)

### P0 - Correctness / Trustworthiness Blocker

**RF1: String-Index Fallback Violates Locked `corpus_position` Decision**

- **Exact evidence:** `generator_v3.py` lines 208-219. When `pages_with_data` is empty (TXT/DOCX documents, or PDFs with page-less cross-page spans), `_derive_corpus_position()` computes `position_ratio = first_idx / len(full_text)` using a character string index, then maps to `start/middle/end`.
- **Why it matters:** The locked architectural decision in `3d_reconnaissance_plan.md` Section 13 states: *"A string-offset percentage is NOT the current benchmark definition of corpus_position. Do not substitute character position for authoritative structural position merely to satisfy the schema."*
- **Affected boundary:** `generator_v3.py::_derive_corpus_position()` to `PartialRetrievalProfile.corpus_position` to `partial_case_dict` - flows through 3D unchanged - would survive schema validation (string-index-derived `corpus_position` is syntactically valid: "start"/"middle"/"end")
- **Consequence:** TXT/DOCX candidates can receive a `corpus_position` value that appears authoritative but is derived from a string offset - an unapproved heuristic. These candidates could eventually reach a schema-passing state with a structurally valid but semantically meaningless `corpus_position`, directly violating the benchmark trustworthiness invariant.
- **Recommended direction:** Replace the string-index fallback with explicit `None` return for all cases where page-structure-based position is unavailable. The `None` path already exists (lines 221-224) and correctly defers to the admission boundary. The string-index branch (lines 208-219) should be removed. Do NOT implement until the locked decision is re-examined and the provisional status is resolved with the project owner.

---

### P1 - Serious Production Risk

**RF2: `UnresolvedPolicyError` as Primary Output Channel Creates Long-Term Coupling**

- **Exact evidence:** `orchestrator.py:29`, `aggregator.py:16-18`. The entire 3D-1 pipeline's only "success" output channel is an exception.
- **Why it matters:** The recon plan (Section 20) warns: *"UnresolvedPolicyError is the current 3C policy-boundary transport mechanism. It must NOT be treated as the permanent 3D pipeline control-flow or candidate-admission policy."* The 3D-1 implementation does treat it as the control-flow.
- **Consequence:** When OD #10 resolves, callers that have been written assuming an exception-only output will need to be updated. Architectural debt, not a correctness bug today.
- **Recommended direction:** Document in the orchestrator's docstring that the exception-based control flow is transitional. When designing 3D-2, ensure the orchestrator's callers are written to handle BOTH the exception path (pre-OD-10-resolution) and a normal return path (post-OD-10-resolution).

**RF3: CaseAggregator Has No Policy Injection Surface**

- **Exact evidence:** `aggregator.py` - `CaseAggregator` has no constructor parameters and no policy hook.
- **Why it matters:** The recon plan (Section 22, Stage 3) requires: *"The future design must expose a policy hook/configuration boundary so that resolving OD #10 changes the policy implementation rather than requiring a pipeline redesign."*
- **Consequence:** When OD #10 resolves, 3D-2 must add a policy injection mechanism to `CaseAggregator`. Not a redesign if done via constructor injection, but requires updating all construction sites.
- **Recommended direction:** In 3D-2, add a `policy` parameter to `CaseAggregator.__init__()`. Default to `None` (which raises `UnresolvedPolicyError` as today). When OD #10 resolves, inject the concrete policy callable. Do NOT implement this now.

---

### P2 - Architectural Debt

**RF4: `run_pipeline()` Return Type Annotation Incorrect**

- **Exact evidence:** `orchestrator.py:16` - `async def run_pipeline(...) -> Dict[str, Any]`. Function never returns normally.
- **Recommended direction:** Change to `-> NoReturn`. Minor change, no test required.

**RF5: `StructuralValidator` Default Schema Path is CWD-Relative**

- **Exact evidence:** `finalizer.py:11` - `schema_path: str = "docs/Phase 3/benchmark_case.schema.json"`. Relative path.
- **Why it matters:** Schema file not found if process is not started from project root. Tests use absolute path workaround; production and test code use different resolution strategies.
- **Recommended direction:** Resolve the schema path absolutely in `StructuralValidator.__init__()`, or require callers to pass the absolute path explicitly.

---

### P3 - Cleanup / Maintainability

**RF6: `"test_scope"` Invalid Evidence Scope in Orchestrator Test**

- **Exact evidence:** `test_3d_orchestrator.py:46` - `"evidence_scope": "test_scope"` is not a valid schema enum value.
- **Why it matters:** Test fixture represents a candidate that would fail schema validation. May mislead future developers.

**RF7: Per-Claim LLM Reasoning Not Captured in IntermediateVerificationResult**

- **Exact evidence:** `verifier_v3.py:300-304` - `IntermediateVerificationResult` captures `claims_checked` and `unsupported_claims` but not the LLM's `reason` per claim.
- **Why it matters:** 3E calibration may require per-claim reasoning traces. If not preserved now, cannot be recovered without re-running the pipeline.

---

## 21. 3D-2 Readiness Assessment (Audit 19)

### READY NOW

- Orchestrator pipeline wiring (`Phase3DOrchestrator`)
- CaseAggregator boundary (`CaseAggregator`)
- Schema structural gate (`StructuralValidator`)
- Persistence stub (`ArtifactWriter`)
- Test infrastructure (wiring and boundary tests pass)
- Cost firewall (proven by test)

### BLOCKED BY OD #10

- Case-level verdict assignment (accepted/rejected/disputed/human_review)
- Primary verifier result assembly (populating `verification.primary`)
- Secondary verification trigger logic
- Human-review trigger logic
- `CaseAggregator.aggregate()` returning a real result

### BLOCKED BY OTHER OPEN DECISIONS

- Benchmark versioning in `version.*` fields (OD #9)
- Candidate ID reproducibility (OD #12)
- Evidence overlap normalization in provenance (OD #5)

### REQUIRES ARCHITECTURAL DECISION (PRE-3D-2)

- **String-index fallback for `corpus_position` in TXT/DOCX (RF1 - P0):** Must be resolved before 3D-2 begins any enrichment work that touches corpus_position. Current fallback violates the locked decision.
- **CaseAggregator policy injection surface (RF3):** Should be addressed in 3D-2 design before implementation of the real aggregation policy.

### REQUIRES MORE RECONNAISSANCE

- `distractor_profile` classification algorithm (no implementation or specification)
- `retrieval_risk` derivation formula (no implementation or specification)
- Corpus enrichment mechanism choice (existing retriever vs. new component - UNKNOWN)
- Whether `app/rag/retriever.py` is appropriate for 3D corpus enrichment (currently Phase 1/2 only)
- Phase 3E interface contract (UNKNOWN)

---

## 22. Required Conditions Before 3D-2

The following conditions must be satisfied before 3D-2 implementation begins. Ordered by severity.

### Condition 1 [P0 - Must Resolve]
**Resolve the `corpus_position` string-index fallback.**

The `_derive_corpus_position()` fallback branch (`generator_v3.py` lines 208-219) violates the locked architectural decision. Before 3D-2 introduces any enrichment logic that depends on or validates `corpus_position`, this fallback must either:
(a) be removed, so TXT/DOCX always returns `None` when page structure is unavailable, or
(b) be explicitly approved as a policy extension to the locked decision with human sign-off.

The string-index fallback is a **Phase 3B artifact** (pre-existing, not introduced by 3D-1). It is flagged here because 3D-2 corpus enrichment will need to enforce the `corpus_position` admission boundary, and a silently passing string-index-derived value would undermine that enforcement.

### Condition 2 [P1 - Must Document Before 3D-2 Design]
**Document the transitional nature of exception-based control flow.**

Add explicit documentation to `Phase3DOrchestrator.run_pipeline()` stating that:
- The current exception-based output channel is transitional (tied to OD #10 being unresolved)
- When OD #10 resolves, `run_pipeline()` should return the assembled case dict normally
- Callers of `run_pipeline()` must be written to handle both paths

### Condition 3 [P1 - Must Design Before 3D-2 Implementation]
**Design the CaseAggregator policy injection surface.**

Before 3D-2 implements real aggregation logic, the policy injection mechanism for `CaseAggregator` must be designed (not implemented). The recon plan requires a policy hook boundary. The current implementation has none.

### Condition 4 [P2 - Should Fix Before 3D-2]
**Fix `StructuralValidator` default schema path to be absolute.**

The CWD-relative default path in `StructuralValidator.__init__()` is a latent runtime failure. Before 3D-2 wires `StructuralValidator` into real production paths, this must be addressed.

### Condition 5 [P2 - Should Fix Before 3D-2]
**Fix `run_pipeline()` return type annotation.**

Change `-> Dict[str, Any]` to `-> NoReturn` in `orchestrator.py`. Small change with no behavioral impact.

---

## 23. Final R&D Recommendation

### Engineering Verdict: **GREEN WITH CONDITIONS**

**Is 3D-1 architecturally sound?**
YES - with one pre-existing P0 violation (string-index corpus_position fallback in 3B) that 3D-1 exposes but did not create, and with the specific conditions listed in Section 22.

**Is it faithful to the locked 3D reconnaissance plan?**
SUBSTANTIALLY YES - 17 of 20 requirements correctly implemented. Two significant partial implementations (RF1, RF3) and one transitional coupling risk (RF2) are identified.

**Has it accidentally encoded policy?**
NO. The mechanism vs. policy firewall is correctly maintained. OD #10 remains blocked. All 12 ODs remain unresolved.

**Can incomplete/untrustworthy cases reach persistence?**
NO - not in 3D-1. Two independent explicit guards prevent this: the aggregator always raises, and the ArtifactWriter raises `NotImplementedError`. This protection is explicit, not incidental.

**Is the `corpus_position` invariant enforced correctly?**
PARTIALLY. The `None` path correctly defers to the admission boundary. However, the string-index fallback silently derives `corpus_position` for TXT/DOCX using an unapproved heuristic, violating the locked decision. This is a P0 finding inherited from 3B.

**Is the architecture sufficiently mechanism-neutral?**
YES - with the exception of the string-index fallback. No corpus enrichment strategy, vector database, or enrichment component has been prematurely committed.

**Is it safe to begin 3D-2?**
CONDITIONALLY. The five pre-conditions listed in Section 22 must be addressed. The P0 condition (string-index fallback) must be resolved before any 3D-2 enrichment work that touches `corpus_position`. The P1 conditions must be resolved before 3D-2 implementation begins.

**What exact conditions must be satisfied first?**
See Section 22. In priority order:
1. Resolve `corpus_position` string-index fallback (P0)
2. Document transitional exception control-flow (P1)
3. Design CaseAggregator policy injection surface (P1)
4. Fix schema path (P2)
5. Fix return type annotation (P2)

---

*All findings labelled OBSERVED are directly confirmed from repository source code. All findings labelled INFERRED are architectural necessities or risks not directly stated in code. All findings labelled UNKNOWN are not established by the repository. No protected Open Decision has been resolved by this audit. No implementation changes were made. No tests were added. No live API calls were made. No candidates were generated.*
