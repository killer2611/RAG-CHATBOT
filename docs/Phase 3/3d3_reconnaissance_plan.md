# Phase 3D-3 Reconnaissance Plan: Production-Grade Integration

## 1. Executive Summary
This document establishes the exact scope and dependencies for Phase 3D-3, continuing from the committed Phase 3D-2 baseline. Phase 3D-3 must establish the final validation and persistence mechanisms without resolving any protected policy.

## 2. Repository Baseline
- **HEAD:** `5ba033a feat: implement Phase 3D-2 enrichment boundaries` (OBSERVED).
- **Working Tree:** Clean (OBSERVED).
- **3D-2 Completion:** 3D-2 established explicit mechanisms for enrichment and aggregation, preserving all 12 Open Decisions (OBSERVED).

## 3. Current 3D-2 Handoff Inventory
**Input:** `PartialBenchmarkCandidate` via `Phase3DOrchestrator.run_pipeline()`.
**Output:** The orchestrator deterministically raises an exception.
- If `corpus_position` is missing: raises `BenchmarkAdmissionError` (OBSERVED).
- Otherwise, `CaseAggregator` raises `UnresolvedPolicyError` carrying `IntermediateVerificationResult` (with structurally assembled `verification.primary`) (OBSERVED).

**Fields Populated by 3D-2 Mechanism:**
- `verification.primary.claims_checked` (OBSERVED)
- `verification.primary.unsupported_claims` (OBSERVED)

**Fields Left Unresolved (Policy Blocked):**
- `verification.verdict` (OBSERVED)
- `verification.primary.verdict` (OBSERVED)
- `verification.primary.reason` (OBSERVED)
- `retrieval_profile.distractor_profile` (OBSERVED)
- `retrieval_profile.retrieval_risk` (OBSERVED)

## 4. Frozen Schema Gap Analysis
Every field required for a complete BenchmarkCase after 3D-2:

| Field | Requirement | Current Source | Status | Mechanism | Policy Dependent? | Owner |
|-------|-------------|----------------|--------|-----------|-------------------|-------|
| `verification.verdict` | Required (enum) | None | Null | Aggregation | YES (OD #10) | OD #10 |
| `verification.primary.verdict` | Required (enum) | None | Null | Aggregation | YES (OD #10) | OD #10 |
| `retrieval_profile.distractor_profile` | Required (enum) | None | Null | Enrichment | YES | 3D |
| `retrieval_profile.retrieval_risk` | Required (enum) | None | Null | Enrichment | YES | 3D |
| `verification.secondary` | Optional | None | Null | Secondary Verif | YES (OD #6, #10) | OD #6, #10 |
| `verification.human_review` | Optional | None | Null | Human Review | YES (OD #7, #8) | OD #7, #8 |
| `version.benchmark_version` | Required (str) | `generator_v3.py` / config | Populated | Generator | NO (OD #9 unresolved but field is populated) | 3B |

## 5. Current Pipeline/Data Flow
**OBSERVED:**
1. `Phase3CVerifier` raises `UnresolvedPolicyError`.
2. `CorpusEnricher` receives intermediate result.
3. `CorpusEnricher` enforces `corpus_position` admission (raises `BenchmarkAdmissionError` if absent).
4. `CorpusEnricher` raises `UnresolvedPolicyError` for retrieval policies.
5. `Phase3DOrchestrator` catches and passes result to `CaseAggregator`.
6. `CaseAggregator` structurally assembles `verification` and raises `UnresolvedPolicyError` (OD #10).
7. Handoff to Finalizer is currently blocked by the `UnresolvedPolicyError` raised by the aggregator.

## 6. Remaining Verification Boundary
**OBSERVED:** `verification.primary.claims_checked` and `unsupported_claims` are assembled.
**UNKNOWN:** How the pipeline catches the final `UnresolvedPolicyError` to route to a final validation/persistence boundary without blurring the error semantics. (Future implementation will route completed cases).

## 7. Case-Level Aggregation Boundary
**OBSERVED:** Handled by `CaseAggregator`, but structurally halts with an exception because verdicts cannot be determined.

## 8. Retrieval Profile Boundary
**OBSERVED:** `CorpusEnricher` establishes the mechanism but halts with `UnresolvedPolicyError` for `distractor_profile` and `retrieval_risk`.

## 9. corpus_position Boundary
**OBSERVED:** Option A locked and enforced. Missing position = `BenchmarkAdmissionError`.

## 10. Admission Boundary
**OBSERVED:** Explicit semantic admission invariant enforced at `CorpusEnricher`.

## 11. Persistence Boundary
**OBSERVED:** `app/evaluation/finalizer.py` defines `StructuralValidator` and `ArtifactWriter`. `ArtifactWriter` is now fully implemented.
**INFERRED:** 3D-3 owns the implementation of the persistence mechanism. The intended 3D-3 contract for `ArtifactWriter`:
- accepts a claimed-complete `case_dict`
- independently validates it via `StructuralValidator`
- refuses invalid/incomplete cases
- performs no persistence before successful validation
- persists schema-valid cases
- performs zero LLM/API calls

## 12. Cost Model
- Finalizer serialization: Deterministic, local I/O. Expected cost: ~0 (INFERRED).
- Schema validation: Deterministic, local. Expected cost: ~0 (INFERRED).
- Zero new LLM/API calls required (INFERRED).

## 13. Error/Failure Semantics
**OBSERVED:** The pipeline uses exception-based transport (`UnresolvedPolicyError`) to halt at policy boundaries. A valid final artifact cannot currently be produced.

## 14. Mechanism vs Policy Matrix
| Component | Mechanism | Policy | Status |
|-----------|-----------|--------|--------|
| Structural Assembly | 3D-2 | N/A | Implemented |
| Verdict Assignment | 3D-2 Interface | OD #10 | Blocked |
| Corpus Enrichment | 3D-2 Interface | Distractor/Risk Rules | Blocked |
| Schema Validation | 3D-3 (Finalizer) | N/A | Ready |
| Artifact Serialization | 3D-3 (Finalizer) | N/A | To be implemented |

## 15. 3D-3 Ownership Matrix
- **StructuralValidator Integration:** Executing the final `jsonschema.validate` check (INFERRED).
- **ArtifactWriter Mechanism:** Defining the mechanism to write validated JSON cases to disk (INFERRED).
- **Final Orchestrator Handoff:** Connecting the output of `CaseAggregator` to the `Finalizer` (INFERRED).

## 16. 3D → 3E Handoff
**INFERRED:** 3E will require a persisted benchmark artifact. 3D-3 builds the persistence mechanism, though it remains practically blocked by OD #10 from generating valid schema artifacts.

## 17. All 12 Open Decisions
| OD | Status | Blocker for 3D-3? |
|----|--------|-------------------|
| #1-5 | UNRESOLVED | No |
| #6-8 | UNRESOLVED | No (Structural mechanism only) |
| #9 | UNRESOLVED | No (Semantic convention unresolved, but field is populated via config) |
| #10 | UNRESOLVED | Yes (Prevents complete schema generation) |
| #11-12| UNRESOLVED | No |

## 18. Dependency Graph
3D pipeline → eventually produces a COMPLETE BenchmarkCase → StructuralValidator → ArtifactWriter → persisted artifact

*(Until policy decisions are resolved, the existing transitional `UnresolvedPolicyError` mechanism remains unchanged. Do not refactor the exception transport.)*

## 19. Implementation Candidates
- **Future Orchestrator Control Flow**: After OD #10 is resolved, `aggregate()` may return a completed `case_dict` normally. The future caller/pipeline driver can then perform: `StructuralValidator.validate(case_dict) -> ArtifactWriter.write_case(case_dict)`. (Do NOT implement this future path now).

## 20. Blocked/Unblocked Matrix
- **Blocked:** Emitting and persisting a final, schema-valid `BenchmarkCase` from the live pipeline.
- **Unblocked:** Implementing `ArtifactWriter` independently to prove the persistence boundary.

## 21. Testing Strategy
- Prove the persistence boundary: `ArtifactWriter` properly validates a claimed-complete case and writes it to disk.
- Prove `ArtifactWriter` rejects incomplete/invalid cases.
- Prove zero live LLM calls.

## 22. Future Implementation Sequencing
After 3D-3 completes the final infrastructure boundary, the Phase 3D infrastructure is functionally complete. The pipeline cannot yield an artifact until Open Decisions are resolved.

## 23. Definition of Done / Stop Conditions
3D-3 reconnaissance is complete upon delivery of this document. No implementation may begin.

---
## CRITICAL DESIGN QUESTION

**What is the smallest production-grade mechanism that 3D-3 can safely implement without resolving any protected policy?**

**Answer:**
The smallest production-grade mechanism is to implement **SCOPE B ONLY**: the `ArtifactWriter` mechanism and its tests.

The scope is strictly limited to:
- `ArtifactWriter` implementation
- Injected `StructuralValidator` inside `ArtifactWriter`
- Independent schema validation before persistence
- JSON persistence, output directory creation, deterministic `case_id` filename
- Tests proving the persistence boundary

**Explicitly Forbidden:**
- Invoking `StructuralValidator` from the orchestrator's `UnresolvedPolicyError` handler.
- Validating partial/intermediate objects.
- Refactoring the existing `UnresolvedPolicyError` transport mechanism.
- Resolving OD #10 or any other protected policies.
