# Phase 3 BenchmarkCase Contract Hardening

This document formalizes the canonical constraints, semantic invariants, and architectural rules for the Phase 3 `BenchmarkCase` contract. It serves to enforce application-level requirements that JSON Schema alone cannot reliably validate.

---

## A. JSON Schema Structural Constraints

The JSON Schema enforces the basic shape of the contract:

- **`case_id`, `question`, `expected_answer`**: Required non-empty strings.
- **`answerability`**: `answerable` or `unanswerable`.
- **`question_type`**: Fixed enum (`factual`, `definition`, `numeric`, `procedural`, `comparison`, `multi_hop`, `synthesis`, `abstention`).
- **`topics`**: Array of non-empty strings, or `null`.
- **`source`**: Object requiring `source_name`, `source_id`, `document_hash`, `document_type`, and `type_confidence`.
- **`evidence`**: Array of evidence objects containing `evidence_id`, `quote`, and `span_hash` (with optional `page` and `section`).
- **`claims`**: Array of claims, each with `claim_id`, `claim`, `support_status`, and `evidence_ids`.
- **`verification`**: Object containing `verdict`, `primary`, and optionally `secondary` and `human_review`.
- **`retrieval_profile`**: Object containing `evidence_scope`, `corpus_position`, `distractor_profile`, and `retrieval_risk`.
- **`version`**: Object defining `schema_version` and `benchmark_version`.
  _Note: The schema's `$id` identifies the schema family/major version and changes only on breaking revisions, whereas `version.schema_version` is a per-case field populated at generation time; synchronizing them is deferred to Open Decision #9._

---

## B. Application-Level Semantic Invariants

The following invariants MUST be enforced by application logic (e.g., Python Pydantic validators), as they cross-reference fields in ways JSON Schema cannot validate:

### 1. Document Hash Semantics (H-1)

`document_hash` represents the SHA-256 identity of the **ORIGINAL SOURCE FILE BYTES**.

- It MUST NOT depend on chunking, embedding, retrieval, reranking, text extraction, whitespace normalization, or LLM-generated text.

### 2. Evidence / Claim Referential Integrity (H-2)

- Every string in `claim.evidence_ids[]` MUST reference an existing `evidence_id` within the `evidence` array of the same `BenchmarkCase`.
- Every string in `verification.primary.claims_checked[]` and `verification.primary.unsupported_claims[]` (as well as corresponding secondary fields) MUST reference an existing `claim_id` in the `claims` array.
- **Dangling references MUST cause validation failure.**

### 3. Claim Support Integrity (H-3)

- If `claim.support_status = "supported"`, then `claim.evidence_ids` MUST contain at least one valid evidence ID.
- If `claim.support_status = "contradicted"`, then `claim.evidence_ids` MUST contain at least one valid evidence ID. A contradiction must point to the source evidence demonstrating that contradiction.
- A supported or contradicted claim with zero evidence references is structurally invalid.

### 4. Accepted Verdict Invariant (H-4)

- `verification.verdict = "accepted"` requires EVERY claim in the case to have a `support_status` of either `"supported"` OR `"not_applicable"`.
- A single claim marked `"unsupported"` or `"contradicted"` MUST prevent an accepted case verdict.

### 5. Disputed State Invariant (H-5)

- `verification.verdict = "disputed"` is a TRANSIENT state. It strictly means secondary verification is pending or in progress.
- A completed canonical case MUST NOT remain permanently disputed. It must have a valid escalation path through secondary verification or human review.

### 6. Human Review Consistency (H-6)

- If `verification.verdict = "human_review"`, then `verification.human_review.required` MUST be `true`.
- An `"accepted"` or `"rejected"` case MUST NOT simultaneously contain unresolved mandatory human review.

### 7. Abstention Consistency (H-8)

- `question_type = "abstention"` explicitly requires `answerability = "unanswerable"`.
- This is a semantic invariant linking the question taxonomy to the answerability state.

### 8. Corpus Position (H-9)

- `corpus_position` (`start` | `middle` | `end`) represents the approximate position of the relevant evidence **within the source document itself**, rather than position within a multi-document corpus.

### 9. Distractor Profile (H-10)

- `distractor_profile` (`none` | `near_duplicate` | `semantic_distractor`) is evaluated relative to the benchmark corpus snapshot associated with the case.

### 10. Topics Nullability (H-11)

- `topics = null` is a strictly valid state. Downstream reporting and stratified analysis must treat `null` safely without crashing or forcefully converting it to an empty array.

### 11. Unanswerable Claim Semantics (H-12)

- If `answerability = unanswerable`, every claim must have `support_status = not_applicable`.
- `supported`, `contradicted`, and `unsupported` are forbidden for claims belonging to an unanswerable case.
- `evidence` MAY still be populated.
- `evidence` in such a case is contextual/provenance evidence for establishing genuine unanswerability, NOT evidence supporting an answer.
- This is an application-level semantic invariant.
- It does not resolve Abstention Accuracy or any other protected decision.

---

## C. Locked Architectural Decisions

1.  **Evidence is chunker-independent**: Evidence MUST be represented using exact quoted source text (`quote`) and a deterministic `span_hash`. Evidence MUST NEVER use `chunk_id` (or `parent_id`/`child_id`) as its identity.
2.  **Claims and case-level verification are strictly separate**: Claims hold `support_status`, while the case verification holds the overall `verdict`.
3.  **Secondary verification is dispute-only**: The secondary verifier does not run by default; it is invoked only when the primary verifier yields a `disputed` verdict.
4.  **Generic difficulty is rejected**: Generic easy/medium/hard classifications are NOT the canonical retrieval diagnostic. The `retrieval_profile` object must be used instead.
5.  **Document-type routing**: Document types (`legal`, `policy`, `technical-research`, `manual`, `narrative`, `tabular`, `general`) are fixed. Low-confidence classifications must fall back to `general`.
6.  **Legacy Phase 1/2 is protected**: The Phase 1/2 `GoldenCase`, `golden_qa.json`, existing API routes, and DeepEval runner remain completely unmodified and runnable. Phase 3 benchmarks will use a separate data contract and adapter boundary.

### Verification State Machine (H-7)

`verification.secondary` may only be populated when `verification.primary.verdict = disputed`. If `verification.secondary` is populated, the case-level verdict must be derived from the secondary outcome and must never contradict it.

The secondary verifier does NOT create another `disputed` state. The intended state machine is:

- primary accepted → case accepted → secondary absent
- primary rejected → case rejected → secondary absent
- primary disputed → secondary accepted → case accepted
- primary disputed → secondary rejected → case rejected
- primary disputed → secondary disagreement → human_review

---

## D. Protected Open Decisions

The following 12 open decisions remain strictly unresolved and MUST NOT be decided until Phase 3 implementation. If the application of an invariant touches one of these domains, it is deferred to the open decision.

1.  **exact DeepEval thresholds**: [OPEN DECISION — NOT RESOLVED]
2.  **Abstention Accuracy formula**: [OPEN DECISION — NOT RESOLVED]
3.  **bootstrap methodology**: [OPEN DECISION — NOT RESOLVED]
4.  **cache implementation**: [OPEN DECISION — NOT RESOLVED]
5.  **evidence overlap algorithm**: [OPEN DECISION — NOT RESOLVED]
6.  **secondary verifier model**: [OPEN DECISION — NOT RESOLVED]
7.  **human-review interface**: [OPEN DECISION — NOT RESOLVED]
    _Note: The exact signal/criterion used to determine that secondary verification disagrees with the primary remains part of this open decision. The canonical schema does not resolve this because primary=disputed carries no directional accepted/rejected lean._
8.  **CLI/API surface**: [OPEN DECISION — NOT RESOLVED]
9.  **benchmark versioning convention**: [OPEN DECISION — NOT RESOLVED]
10. **Phase 3 acceptance thresholds**: [OPEN DECISION — NOT RESOLVED]
11. **accepted-case count after filtering**: [OPEN DECISION — NOT RESOLVED]
12. **candidate determinism policy**: [OPEN DECISION — NOT RESOLVED]
