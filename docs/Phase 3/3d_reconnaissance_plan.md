# Phase 3D Reconnaissance Plan: Production-Grade Integration

## 1. Repository State
- **HEAD:** `75e21b3 feat: complete Phase 3B and 3C benchmark pipeline` (OBSERVED).
- **Working Tree:** Clean. No uncommitted modifications (OBSERVED).
- **3D Work:** Zero Phase 3D implementation files exist (OBSERVED).

## 2. Scope / Production-Grade Objective
This is a PLAN-ONLY pass. Phase 3D must converge Phase 1/2, 3B, and 3C into a final `BenchmarkCase`. The objective is not just schema-validity, but **trustworthiness**. Every populated field must be traceable, policy decisions explicit, and unresolved decisions preserved.

## 3. Mandatory Handoff Inventory
The following maps the actual frozen schema requirements against the 3C `IntermediateVerificationResult` and `PartialBenchmarkCandidate` outputs:

| FIELD | Required? | Present in 3B/3C Output? | Current State | Proposed Owner | Blocked by Open Decision? |
|-------|-----------|--------------------------|---------------|----------------|---------------------------|
| `case_id` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `question` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `expected_answer`| Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `answerability` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `question_type` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `topics` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `source.*` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `evidence.*` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `claims.*` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `verification` | Yes | HollowVerificationStub | Stub | Final Assembly [INFERRED] | No (Structure), Yes (Values) |
| `verification.verdict` | Yes | No (`None` in Stub) | Null | Case Aggregation [INFERRED] | YES (#10) |
| `verification.primary` | Yes | Partially in Exception | Unassembled | Case Aggregation [INFERRED] | YES (#10) |
| `verification.secondary`| No (Cond) | No | Absent | Secondary Verifier [UNKNOWN] | YES (#6, #10) |
| `verification.human_review`| No (Cond) | No | Absent | Human Workflow [UNKNOWN] | YES (#7, #8, #10) |
| `retrieval_profile.evidence_scope` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | No |
| `retrieval_profile.corpus_position` | Yes | Conditionally (3B) | Populated/Absent | Corpus Enrichment [INFERRED] | No |
| `retrieval_profile.distractor_profile` | Yes | No | Absent | Corpus Enrichment [INFERRED] | No |
| `retrieval_profile.retrieval_risk` | Yes | No | Absent | Corpus Enrichment [INFERRED] | No |
| `version.*` | Yes | Yes (3B) | Populated | 3B [OBSERVED: `generator_v3.py`] | YES (#9) |

## 4. Evidence Classification Discipline
All findings below are labelled **OBSERVED** (found in code/schema), **INFERRED** (architectural necessity), or **UNKNOWN** (not established by repository).

## 5. Current Pipeline / Data Flow
**OBSERVED Flow:**
1. 3B Candidate Generation → `PartialBenchmarkCandidate` (Missing global retrieval fields, `verification` is a `HollowVerificationStub`).
2. 3C Structural Validation → Validates `answerability` vs `evidence_ids`.
3. 3C Semantic Verification → Evaluates claims.
4. 3C Return Boundary → Raises `UnresolvedPolicyError` containing `IntermediateVerificationResult` (partial dict + claim-level arrays).
5. **(GAP)** →
**OBSERVED:** 3C currently raises `UnresolvedPolicyError` containing `IntermediateVerificationResult.partial_result`.
**INFERRED:** 3D requires an explicit handoff adapter/boundary capable of consuming the `IntermediateVerificationResult` produced at the 3C policy boundary.
**UNKNOWN:** Whether the long-term implementation should directly catch the exception, wrap it in a dedicated adapter, or change the calling convention once OD #10 resolves.

## 6. Case-Level Verdict Aggregation
**UNKNOWN:** The repository does not establish a policy mapping claim outcomes (`supported`, `unsupported`, `contradicted`) to the case-level `verdict` (`accepted`, `rejected`, `disputed`).
- Is "any unsupported = rejected"? UNKNOWN.
- Is "mixed = disputed"? UNKNOWN.
**Dependency:** This is blocked directly by Open Decision #10. 3D must build the architectural boundary for this policy without resolving it.

## 7. Primary Verifier Result
**OBSERVED** (`verifier_v3.py::IntermediateVerificationResult`):
The 3C boundary provides:
- `partial_case_dict`: the working candidate dictionary with claim-level support_status populated per claim
- `claims_checked`: List[str] of claim_ids that were verified
- `unsupported_claims`: List[str] of claim_ids not fully supported

These are TOP-LEVEL fields of `IntermediateVerificationResult`. They are NOT nested inside `verification.primary`.
Therefore, `IntermediateVerificationResult.claims_checked` != `verification.primary.claims_checked`, and `IntermediateVerificationResult.unsupported_claims` != `verification.primary.unsupported_claims`.

3D must assemble the schema-compliant `verification.primary` structure from the intermediate result. The assembly of structural fields may be deterministic, but `primary.verdict`, `primary.reason`, and case-level interpretation must not be invented if they depend on unresolved case-level policy.

## 8. HollowVerificationStub Boundary
**OBSERVED DISCREPANCY:** The `HollowVerificationStub` (`verdict`, `verified_by`, `unsupported_claims`, `contradictions`, `reason`) structurally clashes with the frozen schema `verification` block (which nests `primary`, `secondary`, `human_review`).

**REPLACEMENT MECHANISM:** 3D must replace the `HollowVerificationStub` wholesale with the frozen-schema-compatible `verification` structure.

**FINAL VALUES:** The mechanism can be designed independently of policy, but policy-dependent fields cannot be fabricated.
In particular:
`HollowVerificationStub` ≠ `verification.primary` ≠ final case-level verification.

As stated in Section 7, `IntermediateVerificationResult.claims_checked` and `IntermediateVerificationResult.unsupported_claims` are TOP-LEVEL fields. They are NOT already a populated `verification.primary` object. 3D must structurally assemble the schema-required primary object from the intermediate result. However, if `primary.verdict` or `primary.reason` depends on unresolved case-level policy, those values remain policy-dependent. The replacement mechanism is not itself a resolution of OD #10.

## 9. Secondary Verification
**UNKNOWN:** The secondary verification trigger is undefined (OD #10). The secondary model is undefined (OD #6). Secondary verification is structurally permitted by the schema but operationally UNKNOWN.

## 10. Human Review
**UNKNOWN:** Trigger (OD #10), Interface (OD #7), API/CLI (OD #8) are completely unestablished.

## 11. Distractor Profile
**OBSERVED:**
The frozen benchmark schema permits the values "none", "near_duplicate", and "semantic_distractor" for `distractor_profile`.

**INFERRED:**
3D therefore requires a corpus-aware mechanism capable of producing a valid value from the schema's allowed vocabulary. Existing infrastructure only includes a Phase 1/2 vector store (`app/rag/retriever.py`). 3D requires corpus-level enrichment CAPABILITY for fields whose semantics depend on corpus context, such as `distractor_profile`.

**UNKNOWN:**
The classification algorithm, evidence-comparison semantics, similarity thresholds, decision thresholds, and implementation mechanism are not established by the current repository. Whether that capability should be implemented as a new component, existing retrieval infrastructure, offline corpus preprocessing, a reusable indexing layer, or another mechanism is unknown.

Explicitly maintain the distinction:
Schema vocabulary ≠ classification policy ≠ implementation mechanism.

*Per-candidate vs per-corpus timing:*
**INFERRED:** If `distractor_profile` is intended to identify near-duplicate or semantically competing evidence/candidates, then its computation requires corpus- or candidate-set-level comparison rather than purely source-local candidate generation. Whether this happens via post-generation batch enrichment, incremental enrichment, or offline corpus enrichment remains an architectural dependency.

## 12. Retrieval Risk
**INFERRED:** Requires determining `low`, `medium`, `high`. 3D requires corpus-level enrichment CAPABILITY to compute this metric.
**UNKNOWN:** The formula for retrieval risk is entirely unestablished. Depends on retrieval score thresholds, corpus density, or competition metrics. Whether it is owned by a new component or existing retrieval infrastructure is unknown.

## 13. `corpus_position` Completion

DECISION LOCKED — OPTION A:

`corpus_position` is an admission-critical retrieval-profile field
whose value must be derivable from authoritative structural
information in the source representation.

OBSERVED:
The current PDF path exposes page structure usable for deriving
`start / middle / end`.

OBSERVED:
The current TXT/DOCX loading path does not expose equivalent
authoritative page/structural metadata required by the current
benchmark semantics.

CONSEQUENCE:
TXT/DOCX candidates for which authoritative `corpus_position`
cannot be established cannot cross the benchmark-admission boundary.

They must produce an explicit, inspectable admission failure /
unresolved-admission state rather than being silently dropped or
assigned a heuristic value.

IMPORTANT:
A string-offset percentage is NOT the current benchmark definition
of `corpus_position`. Do not substitute character position for
authoritative structural position merely to satisfy the schema.

ARCHITECTURAL EXTENSIBILITY:
This is NOT a PDF-extension whitelist. The invariant is based on
authoritative structural provenance. A future source format may
become eligible if its loader/provenance layer can establish an
authoritative structural position.

## 14. Final `retrieval_profile` Completion
| Field | 3B Output | 3C Handoff | 3D Responsibility |
|-------|-----------|------------|-------------------|
| `evidence_scope` | Populated | Passed through | Preserve |
| `corpus_position` | Provisional/Missing | Passed through | Provide mechanism to resolve once semantics are established |
| `distractor_profile` | Absent | Absent | Determine and execute the approved corpus-level enrichment mechanism once the architecture is established. |
| `retrieval_risk` | Absent | Absent | Determine and execute the approved retrieval-risk derivation mechanism once its semantics and inputs are established. |

**UNKNOWN:**
Whether the implementation should reuse app/rag/retriever.py, use an existing index, introduce a new enrichment abstraction, perform offline preprocessing, or use another mechanism has not been established by reconnaissance.

## 15. Final Validation Gate
**VALIDATION MECHANISM:** Can be implemented as deterministic infrastructure now.
**INFERRED:** `jsonschema.validate(completed_case, frozen_schema)` should be the hard structural gate immediately before persistence.
**UNKNOWN / POLICY-DEPENDENT:** Whether all cases reaching this gate can be classified as accepted, rejected, disputed, or human_review depends on unresolved policies.

**ARCHITECTURAL INVARIANT — BENCHMARK ADMISSION**

A benchmark field is not trustworthy merely because a value can be
syntactically generated for it.

`corpus_position` must carry a consistent semantic meaning across
admitted benchmark cases.

Therefore:

    authoritative structure available
        -> corpus_position may be established
        -> case may continue toward admission

    authoritative structure unavailable
        -> corpus_position unresolved
        -> explicit admission boundary
        -> case cannot become a persisted benchmark artifact

This is a TRUSTWORTHINESS invariant, not merely a schema workaround.

`jsonschema.validate()` establishes structural conformance only.
It does NOT establish semantic correctness, retrieval quality, provenance completeness, policy compliance, or benchmark trustworthiness.

Therefore:

    schema-valid
        ≠
    benchmark-admissible
        ≠
    benchmark-trustworthy

The final benchmark-admission boundary must occur only after all required semantic, provenance, retrieval, and policy requirements have been satisfied.

Schema-validity is a hard structural gate, but schema-validity alone is NOT sufficient evidence that a case is trustworthy enough to become a production benchmark artifact.

## 16. Final Benchmark Artifact
**UNKNOWN:** The repository contains no Phase 3 artifact serialization or storage logic.
Serialization infrastructure may be implemented independently. BUT: Production benchmark admission must not occur merely because an object is serializable or schema-valid. A final benchmark artifact requires complete provenance, complete verification semantics, required retrieval metadata, resolved policy decisions, and frozen-schema validation.

## 17. 3E Awareness (Golden-of-Goldens)
**UNKNOWN:** Exact Phase 3E schema and interface contract.
**INFERRED:** Preserving the following fields would allow 3E calibration to compare automated outputs against human-reviewed references without re-running the upstream pipeline:
- `case_id`, `claim_id`
- final claim `support_status`
- evidence identifiers / `span_hash`
- primary verifier result and case-level verdict
- verifier model/version provenance
- generator model/version provenance
- `benchmark_version`
- secondary verification result (if one exists)
- human-review state (if one exists)

## 18. Cost Model
**UNKNOWN:** Exact 3D enrichment cost is unknown until the enrichment architecture is established from repository evidence.
Symbolic cost model for N candidates:
- **Lower bound:** N candidates × deterministic local operations, 0 additional LLM calls.
- **Corpus lookup/reuse case:** cost depends on existing index/query infrastructure.
- **Per-candidate embedding/corpus-scan case:** potentially O(N × M), where N = candidate count and M = relevant corpus items.
- **Secondary verification:** conditional on whatever trigger policy is eventually approved.

## 19. Open Decision #10 Mapping
**Crucial Distinction:** 3D owns the aggregation MECHANISM and INFRASTRUCTURE. OD #10 owns the aggregation POLICY. These must not be conflated.

| 3D Responsibility (MECHANISM) | Can Proceed Now? | Blocked by #10? |
|-------------------|------------------|-----------------|
| Final Verification Replacement Assembly | YES (Structure) | YES (Values depend on policy) |
| Case-Level Verdict Assignment (Mechanism) | YES (Build the interface) | YES (Policy logic) |
| Secondary Verification Trigger (Mechanism) | YES (Build the interface) | YES (Policy thresholds) |
| Human Review Trigger (Mechanism) | YES (Build the interface) | YES (Policy thresholds) |
| Corpus Enrichment (`distractor_profile`, etc.) | YES | NO |
| Final Schema Validation Gate | YES | NO |
| Artifact Serialization | YES | NO |

## 20. Complete Failure / Escalation Matrix
| Scenario | Current Behavior | Proposed 3D Safe Behavior |
|----------|------------------|---------------------------|
| 3C Structural Validation Failure (Input) | Raises `StructuralValidationError` | Candidate cannot be admitted to the benchmark artifact. Permanent rejection vs. deferral vs. regeneration remains policy-dependent and is not established by this plan. |
| 3C Semantic Output Malformed | Raises `RuntimeError` or `StructuralValidationError` | Candidate cannot cross the benchmark-admission boundary. Permanent rejection / deferral / regeneration remains policy-dependent. |
| `corpus_position` cannot be established from authoritative source structure. | Required field remains unresolved and final schema validation would fail. | Candidate reaches an EXPLICIT BENCHMARK-ADMISSION BOUNDARY and is NOT eligible for persistence as a benchmark artifact. This is NOT a silent drop. The implementation must preserve an inspectable failure / disposition signal so that the caller can distinguish schema/structural failure, inability to establish authoritative corpus position, and other policy-dependent candidate dispositions. Permanent rejection vs. deferral vs. regeneration remains a separate admission-policy question unless already established elsewhere. |
| Case Verdict Policy Undefined (OD #10) | Hardcoded Exception (`UnresolvedPolicyError`) | **CURRENT OBSERVED BEHAVIOR:**<br>3C raises `UnresolvedPolicyError` carrying the `IntermediateVerificationResult` because Open Decision #10 remains unresolved.<br><br>**3D ARCHITECTURAL BOUNDARY:**<br>3D must consume the `IntermediateVerificationResult` through an explicitly defined handoff mechanism.<br><br>**UNKNOWN:**<br>Whether the long-term implementation catches the exception directly, wraps it in an adapter, or changes the calling convention after Open Decision #10 is resolved.<br><br>**IMPORTANT:**<br>`UnresolvedPolicyError` is the current 3C policy-boundary transport mechanism. It must NOT be treated as the permanent 3D pipeline control-flow or candidate-admission policy. |
| Final Schema Validation Fails | N/A | DO NOT PERSIST |

## 21. 3D Ownership Matrix + Dependency Graph
**Ownership Matrix:**
- **Corpus Enrichment (3D Mechanism):** `distractor_profile`, `retrieval_risk`.
- **Corpus Position Mechanism:** 3D owns the mechanism/interface responsible for carrying or validating `corpus_position`. Semantic / Admission Invariant: `corpus_position` must originate from authoritative structural information in the source representation. Current supported source: PDF. Pageless/unresolved source: cannot cross benchmark admission until authoritative structural position can be established.
- **Aggregation Boundary (3D Mechanism):** Interface for `primary.verdict`, case `verdict`, secondary triggers. (Policy owned by OD #10).
- **Finalizer (3D Mechanism):** Stub replacement, jsonschema validation, persistence.

**Dependency Graph:**
```
PartialBenchmarkCandidate
        |
        v
3C IntermediateVerificationResult (UnresolvedPolicyError)
        |
        +-----------------------------------+
        |                                   |
        v                                   v
Corpus Enrichment Mechanism          Case-Level Aggregation (OD #10)
        |                                   |
        +--> distractor_profile             +--> primary verifier verdict
        +--> retrieval_risk                 +--> secondary verification?
        |                                   +--> human review?
        |
        v
Source Structural Position
        |
        v
corpus_position established?
      /       \
    YES        NO
     |          |
     v          v
continue     explicit
             admission
             boundary
     |
     v
Final Verification Replacement (Remove Stub)
        |
        v
Final jsonschema.validate() Gate
        |
        v
Artifact Serialization (Write to Disk)
```

## 22. Future Implementation Sequencing + Future Validation Requirements

**Stage 1 — Corpus-Enrichment Mechanism**
Define the interface/boundary required to populate:
- `distractor_profile`
- `retrieval_risk`

The semantic definition of `corpus_position` is LOCKED:
authoritative structural source position is required for benchmark
admission.

Future implementation work must implement the MECHANISM that:
1. preserves an already authoritative `corpus_position`,
2. derives it when the source representation exposes authoritative
   structural information,
3. explicitly signals admission failure when it cannot be derived,
4. never substitutes an unapproved heuristic merely to satisfy the
   frozen schema.

The actual implementation mechanism remains UNKNOWN until repository evidence and architectural review establish whether existing retrieval infrastructure, an enrichment abstraction, offline preprocessing, or another mechanism is appropriate. No component name is architecturally mandated at reconnaissance stage.

**Stage 2 — Finalization / Validation Boundary**
Define the boundary responsible for:
- replacing the HollowVerificationStub
- assembling the schema-compliant verification structure
- completing required retrieval_profile fields
- running the frozen-schema jsonschema.validate gate
- preventing persistence when validation fails
Do not implement this during reconnaissance.

**Stage 3 — Case Aggregation Boundary**
Define the mechanism/interface that converts verified claim-level information into case-level verification results. The mechanism can be designed now. The aggregation POLICY remains blocked by Open Decision #10. The future design must expose a policy hook/configuration boundary so that resolving OD #10 changes the policy implementation rather than requiring a pipeline redesign.

**Stage 4 — Secondary / Human Review Integration**
Define integration boundaries for:
- secondary verification
- human review
Their triggering policy remains unresolved. Dependencies include the relevant protected Open Decisions. Do not implement either workflow during reconnaissance.

**Future Validation Requirements:**
- corpus enrichment mechanism must be deterministic/reproducible where applicable and provenance-preserving
- schema validation must prevent persistence of invalid artifacts
- verification replacement must exactly match the frozen schema
- aggregation mechanism must not hardcode unresolved policy
- secondary/human-review boundaries must not silently invent triggers

## 23. Definition of Done & Stop
This reconnaissance pass is complete.

**PROTECTED OPEN DECISIONS:**
All 12 protected Open Decisions remain UNRESOLVED.
Their individual relevance and dependency relationships are documented in Section 24.

**Additional 3D architectural/design gaps:**
- authoritative `corpus_position` admission enforcement mechanism (SEMANTICS: RESOLVED / LOCKED. IMPLEMENTATION MECHANISM: FUTURE 3D implementation work)
- `retrieval_risk` derivation semantics
- distractor classification semantics
- exact Phase 3E interface/contract

## 24. Open Decisions
| OD | Name | 3D Relevance | Dependency | Status |
|----|------|---------------|------------|--------|
| #1 | Exact DeepEval thresholds | UNKNOWN | UNKNOWN | UNRESOLVED |
| #2 | Abstention Accuracy | UNKNOWN | UNKNOWN | UNRESOLVED |
| #3 | Bootstrap Methodology | UNKNOWN | UNKNOWN | UNRESOLVED |
| #4 | Cache Implementation | UNKNOWN | UNKNOWN | UNRESOLVED |
| #5 | Evidence Overlap / Normalization | UNKNOWN | UNKNOWN | UNRESOLVED |
| #6 | Secondary Verifier Model | Secondary verification execution | INFERRED | UNRESOLVED |
| #7 | Human-Review Interface | Human review routing | INFERRED | UNRESOLVED |
| #8 | CLI/API Surface | Human review triggering/API | INFERRED | UNRESOLVED |
| #9 | Benchmark Versioning | Version metadata assignment | OBSERVED (generator_v3.py) | UNRESOLVED |
| #10 | Phase 3 Acceptance Thresholds | Case-level verdict/aggregation | INFERRED | UNRESOLVED |
| #11 | Accepted-Case Count After Filtering | Final case admission size | INFERRED | UNRESOLVED |
| #12 | Candidate Determinism | Candidate stability | INFERRED | UNRESOLVED |

**STOP.** Await human authorization before Phase 3D implementation begins.
