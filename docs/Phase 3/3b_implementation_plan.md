# Phase 3B Implementation Plan: Candidate Generation

## 1. Executive Summary
This document proposes the architecture for Phase 3B (Candidate Generation) of the universal RAG evaluation system. Its primary responsibility is to transform profiled source documents into a bounded set of candidate `BenchmarkCases`. The design relies on local deterministic signals and existing parsed structures where possible, minimizing expensive LLM calls while strictly preserving the Phase 1/2 safety boundaries, the frozen canonical schema, and the H-12 invariant. Crucially, 3B generates structural candidates; it does not verify truth (which is reserved for 3C).

## 2. Actual Repository Findings

*   **A. What 3A ACTUALLY accepts as input:**
    *   *OBSERVED*: `app/evaluation/profiler.py` (lines 35-50) accepts `documents: List[Document]` (LangChain core Documents).
*   **B. What 3A ACTUALLY returns:**
    *   *OBSERVED*: `app/evaluation/profiler.py` (line 111) returns a `ProfilerResult` model containing `document_type` and `type_confidence`.
*   **C. Which model/API 3A currently uses:**
    *   *OBSERVED*: `app/evaluation/profiler.py` (line 116) uses `build_evaluation_generation_model()`, ensuring isolation from chat paths.
*   **D. How 3A obtains input document representation:**
    *   *OBSERVED*: Extracts `page_content` from `Document` chunks, truncating at 10,000 characters to prevent token limit errors (`app/evaluation/profiler.py`, lines 39-50).
*   **E. Retaining ORIGINAL SOURCE FILE BYTES:**
    *   *OBSERVED*: `app/api/routes_ingest.py` (lines 35-40) saves the original bytes to `data/documents/{digest}{suffix}`. The `digest` acts as the document hash.
*   **F. Retaining ORIGINAL SOURCE DOCUMENT TEXT:**
    *   *OBSERVED*: The original file remains on disk at `data/documents/{digest}{suffix}`. Text can be cleanly re-extracted on demand.
*   **G. Page numbers and section metadata representation:**
    *   *OBSERVED*: `app/rag/loaders.py` (line 26) injects `{"source_name": path.name, "page": page_number}` into PDF `Document` metadata.
*   **H. How chunker transforms source text:**
    *   *OBSERVED*: `app/rag/retriever.py` (lines 47-60) uses `RecursiveCharacterTextSplitter.from_tiktoken_encoder` with `cl100k_base` to split by tokens into parents/children.
*   **I. Reusable existing utilities:**
    *   *OBSERVED*: `app/rag/loaders.py` (`load_file`), `build_evaluation_generation_model()`, and `HierarchicalRetriever` methods can be safely repurposed as read-only utilities.
*   **J. Existing evaluation-generation model/config:**
    *   *OBSERVED*: `build_evaluation_generation_model` wraps the configured LLM API (e.g., DeepSeek) exclusively for evaluation tasks.
*   **K. Reusable adapters/factories:**
    *   *OBSERVED*: `app/evaluation/profiler.py` sets the pattern of building isolated instances via `build_evaluation_generation_model()`.
*   **L. Risks of accidental live model invocation:**
    *   *INFERRED*: Reusing existing `routes_chat.py` or default RAG `build_chat_model()` factories could accidentally trigger the production Groq/chat model.
*   **M. Risks of mutating legacy GoldenCase:**
    *   *INFERRED*: Both Phase 1/2 and Phase 3 logic exist in the `evaluation` directory. If 3B uses `datasets.py` (which parses `golden_qa.json`), it could mistakenly append or overwrite legacy data instead of emitting to a separate Phase 3 benchmark format.

## 3. Frozen Contract Compatibility
The 3B architecture strictly adheres to the frozen `benchmark_case.schema.json` and `phase3_contract_hardening.md`.
*   Evidence is strictly chunker-independent.
*   Evidence identity leverages exact `quote` + `span_hash`, completely avoiding `chunk_id`.
*   `document_hash` is the exact SHA-256 of the original file bytes stored in `data/documents/`.
*   Claims and verification remain strictly separate.
*   Supported/Contradicted claims require non-empty evidence IDs.
*   Primary and Secondary verification are distinct, with secondary reserved for disputes.
*   Answerability remains a first-class state (`answerable` vs `unanswerable`).
*   The document-type taxonomy is strictly limited to the 7 predefined document categories.
*   Zero Phase 1/2 infrastructure is modified.

## 4. Proposed 3B Architecture
Phase 3B acts exclusively as a candidate generator via an isolated pipeline in `app/evaluation/generator_v3.py`:
1.  **Source Hydration:** Uses `document_hash` to load the original bytes from `data/documents/` and applies `load_file()` to get full page text.
2.  **Type Strategy Execution:** Selects a generation prompt template based on the 3A `document_type` (e.g., `technical-research` vs `legal`).
3.  **Structured Generation:** Calls the LLM to propose structured combinations of (Question, Answerability, Quotes, Claims).
4.  **Provenance Grounding:** Deterministically maps proposed quotes back to the raw source text to generate the final chunker-independent `span_hash` and exact `quote`.
5.  **Structural Quality Gate:** Locally filters out cases that violate schema semantics (e.g., missing evidence, H-12 violations).

## 5. Cost Model and Exact LLM Call Budget
We must minimize LLM costs while hitting the candidate generation budget.
**Design Choice:** Batched Structured Generation.
We will request exactly 5 candidates per generation LLM call.

**Budget (Generation calls based on requested candidates):**
*   1-5 candidates requested: 1 generation call
*   6-10 candidates requested: 2 generation calls
*   11-15 candidates requested: 3 generation calls
*   16-20 candidates requested: 4 generation calls
*   21-25 candidates requested: 5 generation calls
*   26-30 candidates requested: 6 generation calls

The important locked budget is:
*   **DEFAULT**: 20 candidate generation budget (at most 4 generation calls)
*   **HARD MAXIMUM**: 30 candidate generation budget (at most 6 generation calls)

Crucially, generated candidates may be rejected by local structural/provenance filters; the number surviving 3B filtering may therefore be lower. Final accepted-case count is protected and remains *[OPEN DECISION #11 — NOT RESOLVED]*.

This avoids the naive `30 candidates × 3 calls = 90 LLM calls` trap. All metadata, structure, and claim decomposition happens within the single batched structured output.

## 6. Provenance and Original-Source Evidence Strategy

**A. Original Bytes = Document Identity**
The original uploaded file bytes are the absolute authority for `document_hash`.
Conceptually:
`original file bytes -> SHA-256 -> document_hash`
The document hash identifies the source artifact independently of chunk size, chunk overlap, embeddings, reranking, retrieval strategy, or extracted-text normalization.

**B. Extracted Source Text = Quote Resolution**
The original source artifact identified by `document_hash` is re-extracted into source text/pages/sections.
Conceptually:
`document identified by document_hash -> source-text extraction -> page/section text -> exact quote resolution`
The quote used as evidence must ultimately be recoverable from the ORIGINAL SOURCE DOCUMENT TEXT derived from the source artifact.
*Note: If a future implementation uses retrieved chunks as a proposal mechanism, the proposed quote MUST be resolved against the original source text before becoming canonical evidence. We do not describe chunked/retrieved text as the authoritative provenance source.*

**C. Span Hash**
`span_hash` is derived from the evidence span/quote resolved from the original source text according to the provenance normalization procedure ultimately approved for Phase 3. It is never derived from a chunk ID, embedding, retrieval result, or model output. This maintains the provenance chain:
`ORIGINAL BYTES -> document_hash -> ORIGINAL SOURCE TEXT -> CANONICAL QUOTE/SPAN -> span_hash`.
(It is NEVER `CHUNK -> chunk_id -> span_hash`).

The exact evidence-overlap algorithm and normalization policy remain OPEN DECISION #5 — NOT RESOLVED.

## 7. Self-Grading Boundary — 3B vs 3C
*   **3B is a candidate generator.** It ensures structural validity, JSON schema adherence, provenance mapping (quote exists in source), and semantic consistency (e.g., H-12).
*   **3B MUST NOT verify truth.** It cannot decide if an answer is factually correct, if a quote sufficiently supports a claim, or if an unanswerable question is genuinely unanswerable.
*   **3C is the verification engine.** All truth-finding and validation of the LLM's claims against the text occur independently in Phase 3C.

## 8. Answerable and Unanswerable Candidate Strategy
The generator prompt explicitly requests a mixed batch of answerable and unanswerable questions.

**Zero-Claim / Zero-Evidence Semantics:**
Can a structurally valid candidate contain `claims = []` and/or `evidence = []`?
*   **Answerable Candidates:** It is recommended that an answerable candidate contain at least one claim, because an answerable benchmark case with zero claims provides nothing meaningful for claim-level grounding and independent verification.
*   **Unanswerable Candidates:** There are two structural possibilities:
    A. Zero claims (nothing was identified that can be decomposed).
    B. At least one `not_applicable` claim (creates an audit trail describing what was examined and why the requested information is absent).
The recommendation is that an unanswerable case should preferably have at least one `not_applicable` claim for auditability.
*Note:* Making this recommendation mandatory constitutes an operational policy that is not already locked by the contract. Thus, it is an *[OPEN DECISION — NOT RESOLVED]*.

3B may enforce structural sanity and H-12. However, 3B must NOT conclude "this case is genuinely unanswerable." That determination belongs entirely to 3C. Missing/empty evidence required by a structural candidate shape is a 3B structural failure, whereas evidence that is present but does not actually support the claim is a 3C truth/support verification failure.

**Unanswerable Claim Invariant (H-12):**
"For answerability = 'unanswerable', every claim's support_status must be 'not_applicable' — never 'supported' or 'contradicted'. Evidence may still be attached to such a case, but its role is to help 3C assess genuine unanswerability, not to support an expected_answer that doesn't exist."

## 9. Document-Type Routing Strategy
3B consumes the `document_type` and `type_confidence` produced by 3A.
Instead of 7 independent architectures, 3B uses a **single generation pipeline** with **strategy-specific prompt templates**.
*   `legal`: Prompt prioritizes obligation/clause generation.
*   `tabular`: Prompt focuses on numeric lookups and comparisons.
*   `general` (fallback): Generic QA generation prompt.

## 10. Candidate Structure and Generation Responsibilities
The batched structured output generates all fields required by the `BenchmarkCase` schema except `verification`, `retrieval_profile`, and `version`.
`retrieval_profile` fields are assigned only when their required evidence scope is available. Source-local fields may be derived during 3B; corpus/global fields must not be fabricated and may be deferred until a corpus-aware stage.
The generation call handles Question, Expected Answer, Answerability, Question Type, Topics, Evidence (proposed quotes), and Claims simultaneously.

## 11. Structural Quality Gate
3B rejects candidates locally for:
*   Malformed JSON or invalid schema.
*   Unrecognized enums.
*   Missing evidence for supported/contradicted claims.
*   H-12 invariant violations.
*   Proposed quotes that do not exist in the original source document (Provenance failure).

## 12. Diversity and Candidate Quality Controls
*   **Local Checks:** Local cosine similarity checks (using existing fast local embedding models like BGE, if available in memory, or purely lexical overlap) to drop near-duplicate questions.
*   **Balance:** The prompt demands a spread of `question_type` and `answerability`.

## 13. Retrieval Profile Strategy
The retrieval profile must explicitly separate source-local information from corpus/global information.

**A. Source-Local / Document-Local Information**
- `evidence_scope`
- `corpus_position`: As defined by the frozen contract, this is the approximate position of the relevant evidence within the source document itself.
These fields can potentially be derived from the source document and grounded evidence without requiring knowledge of unrelated documents.

**B. Corpus / Global Information**
- `distractor_profile` (whether a near-duplicate or semantic distractor exists elsewhere)
- `retrieval_risk` (characteristics that depend on the broader corpus)
3B MUST NOT fabricate or guess such information merely to make a BenchmarkCase look complete. If a field cannot legitimately be determined at the 3B stage without corpus knowledge, its assignment is deferred to later stages. The operational assignment algorithm for these fields remains *[OPEN DECISION — NOT RESOLVED]*.

## 14. OPEN DECISION #12 — NOT RESOLVED
**Candidate Determinism Policy**
The implementation would prefer setting `temperature=0.0` or a very low temperature (`0.2`) with fixed seed inputs to ensure candidates generated from the same document hash remain relatively stable. However, candidate determinism remains an unresolved open decision. 3B will capture generation metadata (model version, prompt version, temperature) but will not encode a final policy.

## 15. OPEN DECISION #4 — NOT RESOLVED
**Cache Implementation**
Regeneration and caching must eventually be implemented to avoid generating candidates for already-processed document hashes. The previously identified conceptual cache identity is based on: content + source_hash + model + prompt_version + schema_version. The exact cache implementation remains OPEN DECISION #4 — NOT RESOLVED.

## 16. Other Protected Open Decisions Touched
*   **Abstention Accuracy Formula (#2):** Not resolved. Unanswerable case claims remain `not_applicable`.
*   **Evidence Overlap Algorithm (#5):** Not resolved. 3B just outputs exact quotes and span hashes.
*   **Phase 3 Acceptance Thresholds (#10):** Not resolved.
*   **Accepted-case Count After Filtering (#11):** Not resolved.

## 17. Legacy Phase 1/2 Safety
*   **Isolation:** 3B will reside in `app/evaluation/generator_v3.py`.
*   **Data Isolation:** Candidates will be output to a new file (e.g., `data/benchmark_v3_candidates.json`), keeping `golden_qa.json` entirely untouched.
*   **API/CLI:** Will not alter existing evaluation routes or CLI commands.

## 18. Testing Strategy
Future 3B implementation tests will include:
*   **Unit:** Mocked LLM structured output parsing.
*   **Unit:** Provenance grounding function testing (finding string indices in raw text).
*   **Unit:** H-12 and structural gate validation checks.
*   **Integration:** Full candidate generation batch (mocking LLM but using real `load_file` text).
*   **Integration:** Budget limit tests (ensuring no more than max LLM calls are made).
*   **Regression:** Existing Phase 1/2 test suite execution to prove isolation.

## 19. Observability and Cost Accounting
The pipeline will emit structured JSON logs capturing:
*   Requested candidates vs Generated vs Survived filtering.
*   LLM call count and token usage (if exposed by API).
*   Model version and prompt version.
These fields will not resolve any cost/budgeting decisions but provide necessary visibility.

## 20. Failure and Fallback Behavior
*   **JSON Parse Failure:** retry behavior is not yet finalized. Any future retry policy must remain consistent with the locked 20-default / 30-hard-maximum candidate-generation budget and must not silently multiply generation expenditure beyond the approved budget. The exact retry policy is not resolved by this plan. (OPEN DECISION — NOT RESOLVED)
*   **Provenance Failure:** The individual candidate is dropped locally.
*   **All Candidates Fail:** Bubble up a 3B generation exception.
*   **General/Short Document:** Short or structurally sparse documents may produce fewer viable candidates after local structural/provenance filtering. The 5-candidates-per-generation-call planning assumption remains unchanged. Any adaptive reduction of batch size would require explicit human review because it would change the documented LLM cost model.

## 21. Security and Data Integrity
The source document is UNTRUSTED DATA. A document may contain adversarial text such as: "IGNORE PREVIOUS INSTRUCTIONS."
Therefore:
*   Source text must be treated as data, not instructions.
*   Document content must never override the generation system/developer instructions.
*   Candidate generation must not execute or interpret document text as operational instructions.
*   Source text must not be allowed to alter the output schema or generation policy.
*   Provenance validation must remain local/deterministic rather than trusting instructions contained in the document.
*   Delimiters are only a representation/prompt-structuring aid, NOT the security boundary.

## 22. Implementation Sequence for Future 3B Work
1. Build `app/evaluation/provenance.py` (Deterministic quote locator).
2. Build `app/evaluation/generator_v3.py` (LLM batch generation and structural gate).
3. Wire 3A Profiler output into 3B inputs.
4. Implement tests.

## 23. Risks and Explicit Unknowns
*   **UNKNOWN**: The reliability of batched structured generation for five complex candidates per call has not yet been empirically established. If implementation testing shows that the five-candidate batch format is unreliable, any alternative generation strategy that changes the 5-candidates-per-call assumption or materially changes LLM call expenditure requires explicit human review before implementation. Such an alternative is NOT part of the current 3B plan.
*   **UNKNOWN**: How robust exact-quote provenance matching will be against LLM minor rewrites.

## 24. Definition of Done for the Future 3B Implementation
*   Candidate generator accepts profiled documents and outputs structurally valid Phase 3 candidate `BenchmarkCases` for downstream 3C verification.
*   Budget is respected.
*   Provenance is successfully tied to original bytes.
*   H-12 is respected.
*   No verification is performed.
*   Phase 1/2 is unmodified.

## 25. Definition of Done for THIS Reconnaissance/Plan Pass
*   [x] Read schema, hardening contract, profiler.py, and test_profiler.py.
*   [x] Inspected surrounding architecture (ingestion bytes location).
*   [x] Documented explicit LLM call limits.
*   [x] Provenance mapped to original source text.
*   [x] H-12 invariant explicitly reproduced.
*   [x] Boundary between 3B (generator) and 3C (verifier) explicitly stated.
*   [x] Open Decisions #4 and #12 isolated in dedicated sections.
*   [x] No code written, no APIs called, no existing Phase 1/2 code modified.

## 26. 3B PLAN HARDENING CHANGELOG
*   **H1 — Provenance precision:** Explicitly separated original bytes (document identity) from extracted source text (quote resolution), removed ambiguous "extremely close match" wording, and clarified that span_hash is derived from the canonical quote resolved from original source text, not chunk IDs.
*   **H2 — Retrieval-profile boundaries:** Explicitly separated source-local fields (evidence_scope, corpus_position) from global/corpus fields (distractor_profile, retrieval_risk) which 3B must not fabricate if it lacks corpus knowledge.
*   **H3 — Candidate budget precision:** Clarified generation calls to exactly 5 candidates per call. Defined budget as 20 default (max 4 calls) and 30 hard max (max 6 calls). Clarified that surviving candidate counts may be lower due to filtering.
*   **H4 — Zero-claim / zero-evidence semantics:** Recommended at least one claim for answerable cases, and discussed zero claims vs at least one `not_applicable` claim for unanswerable cases. Labeled making this mandatory as an open decision, and distinguished 3B structural failure from 3C truth verification.
*   **H5 — Source-data security:** Explicitly established that source documents are untrusted data, not instructions, and that prompt delimiters are not the security boundary.

## PROTECTED OPEN DECISIONS
None of the 12 protected open decisions were resolved by this pass. All remain explicitly unresolved.
