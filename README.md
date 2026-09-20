# RAG Benchmark Platform

A production-oriented Retrieval-Augmented Generation (RAG) system that automatically generates, verifies, calibrates, and evaluates benchmark cases without relying on the generation model as its sole judge.

## What makes this different

* **Adversarial candidate generation with independent verification:** Candidate evaluation questions are generated adversarially and independently verified against source text to ensure they are factually grounded and practically answerable.
* **Claim-level evidence grounding / no self-grading:** The system strictly separates the generation model from the evaluation judge, preventing the LLM from grading its own homework.
* **Benchmark calibration:** The benchmark suite is rigorously calibrated using an independent engine to establish a verifiable baseline ahead of future human-aligned validation.

## Architecture

The system is organized into a five-layer conceptual hierarchy mapping to the project roadmap:

* **Layer 1 — RAG Foundation:** Core document ingestion, embedding, and chat generation (Phase 1).
* **Layer 2 — Evaluation Baseline & Infrastructure:** DeepEval integration and local judge configuration (Phase 2).
* **Layer 3 — Self-Auditing Benchmark Construction:** Automated adversarial generation, verification, and assembly of test cases (Phases 3A–3D).
  * *(Phase 3E serves as the calibration bridge linking construction to evaluation)*
* **Layer 4 — Evaluation Integration:** Statistical reporting and baseline benchmark execution (Phase 3F).
* **Layer 5 — Evaluator Trust / Human Validation:** *[Planned / Upcoming Phase 8a]* Judge-Human Alignment Study.

### Execution Paths

**A. NORMAL RAG CHAT PATH**
```text
document ingestion → dense retrieval & parent expansion → reranking → chat LLM → grounded response
```

**B. BENCHMARK ENGINE PATH**
```text
document profiler → candidate generator → claim verifier → benchmark assembler → calibration → evaluation
```

## Advanced Retrieval Components

Advanced retrieval components include hierarchical parent-child chunking, `MiniLM` embeddings, Chroma vector store, and `BGE` cross-encoder second-stage reranking, all backed by persistent storage.

## Project Roadmap

* Phase 1–2 — ✅ complete
* Phase 3A    — ✅ complete
* Phase 3B    — ✅ complete
* Phase 3C    — ✅ complete
* Phase 3D    — ✅ complete
* Phase 3E    — ✅ complete
* Phase 3F    — ✅ complete
* Phase 4     — ✅ complete
* Phase 5     — ⏳ upcoming
* Phase 6     — ⏳ upcoming
* Phase 7     — ⏳ upcoming
* Phase 8     — ⏳ upcoming

*(Note: Layer 5 / Phase 8a human validation is a planned sub-milestone under Phase 8).*

## Local Development Quick Start

*Docker support is available for local development and containerized execution.*

### Backend
```bash
cd backend/rag-production-system
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
uvicorn app.main:app --reload
```
The API documentation is available at `http://127.0.0.1:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

**Backend:**
* FastAPI & Uvicorn
* LangChain (Core, Groq, Google GenAI, Ollama)
* Chroma (Vector Store)
* Sentence-Transformers (MiniLM, BGE)
* DeepEval (Evaluation)
* aiosqlite (Persistent parent store & chat history)

**Frontend:**
* Next.js (React 19)
* Tailwind CSS
* Lucide React
* React Markdown

## Evaluation Results

| Metric | Score | Cases |
|--------|-------|-------|
| Faithfulness | TBD | TBD |
| Answer Relevancy | TBD | TBD |
| Contextual Precision | TBD | TBD |
| Contextual Recall | TBD | TBD |

*Evaluation scores will be populated after the Phase 6 end-to-end benchmark run.*
