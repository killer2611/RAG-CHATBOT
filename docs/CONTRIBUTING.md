# Contributing to RAG Benchmark Platform

Thank you for contributing! Please follow these practical guidelines to ensure consistency and stability across the project.

## Local Setup

*Docker support is available. The local setup below remains the canonical development workflow.*

### Backend
To set up the FastAPI backend locally:
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

### Frontend
To set up the Next.js frontend locally:
```bash
cd frontend
npm install
npm run dev
```

## Testing

Tests should be executed locally before requesting a review. The current backend test command is:

```bash
cd backend/rag-production-system/
pytest
```

## Privacy & Observability

LangSmith tracing is optional, requires `LANGCHAIN_TRACING_V2` to be enabled, and should remain disabled in privacy-sensitive deployments.

## Branch and Commit Conventions

- **Branches**: Create a branch for your changes before requesting a review.
- **Focused Commits**: Keep your commits focused, atomic, and well-described.
- **Testing**: Run tests locally (`pytest`) before requesting a review.
- **Secrets**: Do not commit secrets, API keys, or credentials. Use `.env` files.
- **Runtime Data**: Do not commit runtime artifacts or generated data (e.g., `data/`, `.pytest_cache`, or generated CSVs).
- **Frozen Contracts**: Do not modify frozen contracts without explicit architectural approval.

## Open Decisions

Twelve architectural policy decisions (OD #1–#12) remain explicitly open.
These govern evaluation thresholds, aggregation policies, CI methodology,
and other system-level choices. Open Decisions must not be silently
resolved in code — each requires an explicit decision document in
`docs/decisions/` before any implementation proceeds. Consult the
project maintainer before implementing any policy-level change.

## Frozen Schema Rule

The benchmark case schema located at `docs/Phase 3/benchmark_case.schema.json` is **FROZEN** and must not be modified.

Changes to this frozen schema require explicit architectural approval and are entirely outside normal contribution scope.
