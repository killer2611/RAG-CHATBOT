# Contributing to RAG Benchmark Platform

Thank you for contributing! Please follow these practical guidelines to ensure consistency and stability across the project.

## Local Setup

*Docker support is being added in Phase 4b. Currently, please use the following local setup.*

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
copy .env.example .env
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

Disable `LANGCHAIN_TRACING_V2` in privacy-sensitive deployments. (Note: LangSmith integration is handled separately; simply ensure the environment variable is disabled if privacy is required).

## Branch and Commit Conventions

- **Branches**: Create a branch for your changes before requesting a review.
- **Focused Commits**: Keep your commits focused, atomic, and well-described.
- **Testing**: Run tests locally (`pytest`) before requesting a review.
- **Secrets**: Do not commit secrets, API keys, or credentials. Use `.env` files.
- **Runtime Data**: Do not commit runtime artifacts or generated data (e.g., `data/`, `.pytest_cache`, or generated CSVs).
- **Frozen Contracts**: Do not modify frozen contracts without explicit architectural approval.

## Frozen Schema Rule

The benchmark case schema located at `docs/Phase 3/benchmark_case.schema.json` is **FROZEN** and must not be modified.

Changes to this frozen schema require explicit architectural approval and are entirely outside normal contribution scope.
