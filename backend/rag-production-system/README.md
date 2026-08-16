# Production RAG System

A modular FastAPI backend that preserves the project's validated retrieval strategy while removing the main production risks in the original notebook/script.

## Architecture

```text
Client / Next.js / React / Streamlit
            |
            v
        FastAPI API
       /    |      \
   /chat  /ingest  /evaluate
      |       |         |
      v       v         v
  Chat svc  Loaders   Eval jobs
      |
      +--> Persistent SQL chat history
      |
      +--> History-aware question rewriting
      |
      +--> Dense child-vector retrieval (Chroma + MiniLM)
      |
      +--> Parent expansion (persistent SQLite parent store)
      |
      +--> BGE cross-encoder reranking
      |
      +--> Strict context-only grounded generation
```

## What was reconciled

The supplied contribution README documents parent chunks of 800 with 150 overlap and child chunks of roughly 250–300 with 50–80 overlap, while the runnable script/notebook still use 600/100 and 200/40. The production configuration adopts the documented target of 800/150 and 300/60, exposed through environment variables rather than hidden constants.

A second important correction is unit semantics: `RecursiveCharacterTextSplitter` is character-based unless a token encoder is explicitly used. The production implementation therefore uses `from_tiktoken_encoder`, so the configured 800/150 and 300/60 values are actually token-oriented.

The retrieval behavior is preserved semantically:

1. child chunks are embedded with `sentence-transformers/all-MiniLM-L6-v2`;
2. Chroma retrieves `k=10` child candidates;
3. candidate child metadata identifies parent documents;
4. parent documents are expanded from a persistent store;
5. `BAAI/bge-reranker-base` reranks the parent contexts and keeps the top 3;
6. an explicit history-aware rewrite is run before retrieval;
7. a context-only answer prompt abstains when evidence is insufficient.

## Why the architecture is safer

The original code keeps chat history in a process-global dictionary and stores parent documents in `InMemoryStore`. Current LangChain documentation describes in-memory stores as development/test-oriented and recommends persistent stores for production. This implementation uses SQL-backed chat history and a durable parent-document store instead. citeturn103915search0turn103915search5

`RunnableWithMessageHistory` is intentionally not used. The Python reference still documents it, but current security/release guidance identifies it as an older surface being deprecated; the production service performs history I/O explicitly and invokes the async model interfaces directly. citeturn878355search8turn878355search3

The BGE reranker is retained, but the old `langchain_community.cross_encoders` adapter is removed from the application path. The current LangChain reranking guide still validates BGE-family cross-encoders as a second-stage reranking pattern. citeturn800520search0

## API

### `POST /chat`

JSON request:

```json
{"session_id":"demo-1","message":"What does the paper say about mass transfer?","stream":false}
```

Set `stream=true` for Server-Sent Events. Events are `sources`, `token`, and `done`.

### `POST /ingest`

Multipart file upload. Supports PDF, TXT and DOCX, with a configurable upload-size cap.

### `POST /evaluate`

Starts a background DeepEval benchmark and returns a job ID.

### `GET /evaluate/{job_id}`

Polls job state until the report is ready.

## Evaluation strategy

The supplied work showed strong Answer Relevancy (0.93) but weaker Contextual Precision (0.62), Contextual Recall (0.75), and Faithfulness (0.71), which is why retrieval and grounding are the primary optimization targets. fileciteturn1file0L40-L55

The evaluator supports either local Ollama or Gemini. DeepEval's current guidance recommends reducing concurrency and adding throttling when judges hit rate limits; the implementation sets `max_concurrent=1`, a configurable throttle, and a larger retry budget. citeturn453246search4turn493777search7

For the constrained local machine described in the contribution document, the recommended default is the local 7B/8B class judge. The original report specifically describes the 14B setup as causing CPU/GPU splitting and very slow evaluation, while sequential, right-sized local evaluation reduced stalls. fileciteturn1file0L218-L282

## Run

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

## Production deployment notes

The included default SQLite configuration is operational and persistent for a single backend instance. For multiple API replicas, switch `DATABASE_URL` to PostgreSQL and place the vector/parent stores behind shared persistent infrastructure; add a distributed job queue (for example Celery/Arq/RQ) and Redis-backed session locking before horizontally scaling evaluation jobs.

No secrets belong in source. The supplied notebook contained a literal Gemini credential, so that credential must be rotated before any Git push. The refactored repository uses environment variables only.
