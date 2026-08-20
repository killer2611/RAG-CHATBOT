# Phase 3B-3: Reconnaissance & Integration Plan

## 1. Version Config Verification
**OBSERVED** — `app/evaluation/generator_v3.py`, `CandidateGenerator._process_candidate()`, lines 246–249.
The candidate `version` block is populated dynamically using `get_settings().phase3_schema_version`, etc.
**OBSERVED** — `app/core/config.py`, `Settings`, lines 81-85.
The configuration keys (`phase3_schema_version`, `phase3_benchmark_version`, `phase3_generator_prompt_version`, `phase3_verifier_prompt_version`) are explicitly defined.
**OBSERVED** — `tests/test_generator_v3.py`, `test_version_field_presence_and_schema_validation`, lines 356-373.
The tests actively modify the configuration values, execute generation, and mathematically assert that the output matches the overridden config, proving there is no hardcoded fallback.

## 2. Retrieval Profile Field-by-Field Analysis

### A. evidence_scope
Allowed: `single_span`, `multi_span`
**Ownership:** Source-Local.
**INFERRED** — The `evidence` array is populated in 3B. A simple count of distinct resolved evidence spans (or analyzing if a single quote crosses pages) is sufficient to determine if the case relies on a single contiguous span or multiple spans. No global context is needed.

### B. corpus_position
Allowed: `start`, `middle`, `end`
**Ownership:** Source-Local.
**OBSERVED** — `app/evaluation/provenance.py`, `resolve_quote()`, lines 111-116.
The `ProvenanceResult` captures the exact `page` of the quote. The resolver loads the document into an array of `Document` pages (`pages = self._extract_source_text(doc_path)`).
**INFERRED** — By comparing the resolved `page` against `len(pages)`, 3B or a local-enrichment wrapper can mathematically derive the `start`/`middle`/`end` tertile within the original source document without any corpus context.

### C. distractor_profile
Allowed: `none`, `near_duplicate`, `semantic_distractor`
**Ownership:** Corpus-Global.
**INFERRED** — Identifying distractors requires scanning a multi-document index to find semantic collisions or near-duplicates. The current Phase 3B architecture (generator and provenance resolver) only loads the single authoritative document bytes. It has zero awareness of the broader corpus.

### D. retrieval_risk
Allowed: `low`, `medium`, `high`
**Ownership:** Corpus-Global.
**INFERRED** — Retrieval risk is a function of the entire search space (e.g., competing documents, vocabulary overlap). 3B lacks the evidentiary context to make this assignment. The algorithm to assign this remains undefined and should be deferred (**OPEN DECISION — NOT RESOLVED**).

## 3. Recommended Integration Sequence

1. **Which fields can 3B legitimately populate?**
   `evidence_scope` and `corpus_position`.
2. **Which fields require a later corpus-aware stage?**
   `distractor_profile` and `retrieval_risk`.
3. **Where should source-local fields be populated?**
   Inside 3B's `_process_candidate` method. It already has the `profiler_result`, `document_hash`, and the resolved `evidence` objects. It can easily inject `evidence_scope` and `corpus_position` into a partial `retrieval_profile` block or explicitly document that it leaves the global fields missing.
4. **What exact object does 3B hand to 3C?**
   A partial Python dictionary (representing a partial candidate) that is structurally incomplete.
5. **How is that object explicitly represented as PARTIAL?**
   Currently, it is just a `Dict[str, Any]` at runtime. To prevent accidental misuse, the integration should adopt a `PartialBenchmarkCase` wrapper or type hint that explicitly marks it as pre-validation.
6. **At what exact pipeline stage does the complete BenchmarkCase become schema-valid?**
   At a dedicated Corpus Enrichment stage that runs *after* generation and verification, but *before* final export.
7. **At what exact stage is the frozen JSON Schema applied as the final gate?**
   At the absolute end of the pipeline, immediately before writing the case to the Golden benchmark JSON file.
8. **Does 3C require a schema-complete case before verification?**
   No. Semantic verification only requires the `claim` string and the `evidence` text. 3C operates safely on the partial candidate.

## 4. 3B → 3C Handoff Contract

### Fields present after 3B
**OBSERVED** — `app/evaluation/generator_v3.py`, `_process_candidate()`:
- `case_id`
- `question`
- `expected_answer`
- `answerability`
- `question_type`
- `topics`
- `source` (fully populated)
- `evidence` (fully populated)
- `claims` (fully populated, except `support_status` omitted for answerable)
- `version` (fully populated from config)

### Fields intentionally absent
- `verification`: Omitted because 3B is forbidden from performing semantic verification/truth assessment.
- `retrieval_profile`: Omitted because 3B cannot generate the global fields (`distractor_profile`, `retrieval_risk`), meaning the object cannot satisfy the schema yet.

### Identity Continuity
**OBSERVED** — `case_id`, `evidence_id`, and `claim_id` are populated in 3B via UUIDs.
These survive the handoff unchanged to provide runtime uniqueness. They do NOT provide reproducible candidate determinism. (**OPEN DECISION #12 — NOT RESOLVED**).

## 5. Staged Validation Strategy

### A. Candidate Structural Validation (Mid-Pipeline)
Python-level `jsonschema.validate` against the frozen schema must NOT be run here. Mid-pipeline structural validation asserts:
- `answerability` constraints (H-12 enforcement, which is already present).
- Provenance existence (already present).
- Zero-claim constraints (already present).

### B. Final Complete-Case Validation (End-of-Pipeline)
The `jsonschema.validate(candidate, frozen_schema)` call belongs strictly at the end of the orchestration script, after 3C has appended `verification` and after corpus-enrichment has appended the missing `retrieval_profile` attributes. If it fails, the case is dropped.

## 6. 3B / 3C Boundary
3B's responsibility ends exactly when it returns the unverified `case_dict` containing exact provenance matches.
3C's responsibility begins by taking that dictionary, reading `claims` and `evidence`, invoking the adversarial verifier model, and appending the `verification` block.

## 7. Cost / Call Implications
- 3B maintains its strict 5-candidate per batch cost firewall.
- Deriving `corpus_position` and `evidence_scope` inside 3B requires ZERO additional LLM calls; it is pure deterministic math on existing data.
- 3C will introduce verification LLM calls, but that is out of scope for 3B.

## 8. Protected Open Decisions
- #1. Exact DeepEval thresholds: OPEN DECISION — NOT RESOLVED.
- #4. Cache implementation: OPEN DECISION — NOT RESOLVED.
- #5. Evidence overlap algorithm: OPEN DECISION — NOT RESOLVED.
- #6. Secondary verifier model: OPEN DECISION — NOT RESOLVED.
- #9. Benchmark versioning convention: OPEN DECISION — NOT RESOLVED.
- #12. Candidate determinism policy: OPEN DECISION — NOT RESOLVED.
All 12 decisions remain strictly unresolved by this integration plan.
