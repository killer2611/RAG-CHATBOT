# Forensic Audit & Reconciliation

## 1. Source inventory

### Contribution README
The README frames the contribution around measurement-driven RAG diagnosis, BGE reranking, parent/child chunking, grounding, and local DeepEval reliability. It reports baseline scores of Answer Relevancy 0.93, Contextual Precision 0.62, Contextual Recall 0.75 and Faithfulness 0.71. fileciteturn1file0L40-L55

### `RAG_chatbot(3).py`
The script combines environment setup, model construction, document ingestion, retrieval, reranking, prompt construction, history wrapping, evaluation, and the CLI loop in one module. It currently uses an in-memory session dictionary, `InMemoryStore`, hard-coded provider credentials/placeholders, a hard-coded local PDF path, and 600/100 + 200/40 character splitters. fileciteturn1file1L468-L532

### `evaluation.ipynb`
The notebook is exploratory rather than a service artifact. It contains 20 golden QA pairs, local Ollama generation, a Gemini judge, the same hierarchical retrieval pipeline, and the DeepEval run. It also contains a literal Gemini API key and should not be committed as-is.

## 2. Critical findings

| Finding | Severity | Consequence | Production correction |
|---|---|---|---|
| Gemini API key hard-coded in notebook | CRITICAL | Credential exposure | Rotate credential; use `.env` only |
| Process-global session dict | HIGH | Memory growth, no persistence, unsafe multi-worker semantics | SQL-backed history + bounded history window |
| `InMemoryStore` parent store | HIGH | Documents vanish on restart and are not safe for concurrent production use | Persistent SQLite parent store |
| `RunnableWithMessageHistory` | HIGH | Legacy/deprecation/security migration surface | Explicit history orchestration |
| `langchain_community.cross_encoders` adapter | MEDIUM | Integration shifts as LangChain packages evolve | Direct `sentence-transformers.CrossEncoder` adapter |
| Chunk size mismatch | HIGH | README claims differ from actual runtime | Central config + 800/150 and 300/60 |
| Character/token ambiguity | HIGH | The documented values are not actually tokens | `from_tiktoken_encoder` |
| Ingestion at import time | HIGH | Startup performs I/O and can duplicate indexes | Explicit `/ingest` endpoint |
| `add_documents` on every startup | HIGH | Duplicate vector data across reruns | Persistent source IDs + delete/replace by source |
| Evaluation and serving coupled | HIGH | Eval blocks and competes with chat workload | Background evaluation jobs |
| `ignore_errors=True` | MEDIUM | Failed metrics can be mistaken for a pass | Surface evaluation errors |
| Retrieval evaluated separately from chain question rewrite | MEDIUM | Eval context may not exactly match actual rewritten query | RAG service exposes retrieval after rewrite |
| No upload validation/size control | HIGH | Disk/memory abuse | Extension + size limits |
| No streaming API | MEDIUM | Frontend cannot progressively render | SSE streaming endpoint |
| Hard-coded session ID | HIGH | All users share one history | Per-request session ID |
| No source lifecycle model | MEDIUM | Re-ingestion and deletes are difficult | Deterministic `source_id` with replace semantics |

## 3. Race conditions and memory risks

### Session history
The original dictionary is mutated without a lock and has no eviction. In a long-running process, every unique session remains resident. Multiple requests for the same session can also interleave. The refactor uses persistent SQL history and a per-session asyncio lock for ordering inside an instance.

### Vector/index writes
The original script performs indexing during module import. Multiple workers or reloads can execute the import multiple times. The refactor makes ingestion explicit and idempotent by hashing the uploaded file and replacing all child vectors/parent rows for that source.

### Evaluation overload
The README records that concurrent DeepEval work could contend for the limited local GPU/CPU resources. The production runner defaults to one concurrent test case and a delay between judge calls. DeepEval's own current configuration guide documents `max_concurrent` and `throttle_value` for rate-limit control. citeturn453246search4

### API streaming
Streaming requests now hold the per-session lock for the full turn and append history only after the model stream finishes. This prevents a second turn from reading a partially written conversation.

## 4. Deprecation reconciliation

The original script imports legacy `langchain_classic` chain/retriever surfaces and `RunnableWithMessageHistory`. Current LangChain documentation continues to expose `ParentDocumentRetriever` in `langchain-classic`, but the classic package is positioned as a legacy compatibility package. citeturn622476search7turn878355search0

The production implementation avoids the classic chain layer entirely. It keeps the proven retrieval *behavior* rather than coupling the service to deprecated orchestration APIs.

The current Python API reference still documents `RunnableWithMessageHistory`, but recent security guidance says LangChain is deprecating it as an older path and recommends newer memory/stream patterns. citeturn878355search8turn878355search3

## 5. Retrieval behavior preserved

The original design is: vector candidate retrieval -> parent expansion -> BGE reranking -> grounded answer. The contribution README explicitly describes this as the two-stage retrieval strategy and grounding guardrail. fileciteturn1file0L59-L73 fileciteturn1file0L178-L212

The new `HierarchicalRetriever` implements the same semantics with deterministic IDs and durable storage.

## 6. Evaluation improvements

The supplied notebook runs all 20 cases and uses `GeminiModel` directly. The original code disables timeouts and cache globally and uses synchronous evaluation, but its notebook still exhibits rate-limit concerns. The production runner instead:

- switches judges using `EVAL_JUDGE=ollama|gemini`;
- defaults local evaluation to an 8B-class Ollama model;
- sets DeepEval `max_concurrent=1` and throttle;
- increases retry budget through DeepEval-supported environment variables;
- runs evaluation in a background job;
- writes a structured CSV report;
- preserves metric errors rather than suppressing them.

DeepEval currently documents exponential backoff for transient failures and configurable concurrency/throttling for rate-limit control. citeturn493777search7turn453246search5

## 7. Security findings

1. Rotate the Gemini key found in the notebook immediately.
2. Never commit `.env` or notebook credentials.
3. Reject arbitrary filesystem paths in API input.
4. Sanitize uploaded filenames and cap body size.
5. Do not expose raw stack traces to API clients in production; map exceptions to safe messages and log the details server-side.
6. Keep evaluation behind authentication/rate limiting in a real deployment.

## 8. Zero-regression acceptance gates

A release candidate should not be called production-ready until the team has a before/after benchmark on the same 20 golden questions and confirms:

- no regression in Answer Relevancy;
- Contextual Precision improves materially over 0.62;
- Contextual Recall improves materially over 0.75;
- Faithfulness improves materially over 0.71;
- retrieval sources are stable across repeated runs;
- ingestion is idempotent;
- restart preserves vector/parent/history state;
- the streaming endpoint produces complete answers;
- Gemini 429s fall back to the local judge when desired.
