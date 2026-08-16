from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_evaluate import router as evaluation_router
from app.api.routes_ingest import router as ingest_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.models.schemas import SystemInfoResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


settings = get_settings()
app = FastAPI(title="Production RAG API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(evaluation_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/system/info", response_model=SystemInfoResponse)
async def system_info(settings: Settings = Depends(get_settings)) -> SystemInfoResponse:
    chat_model = (
        settings.groq_model
        if settings.chat_provider == "groq"
        else settings.gemini_model
        if settings.chat_provider == "gemini"
        else settings.ollama_model
    )
    return SystemInfoResponse(
        app_name=settings.app_name,
        environment=settings.environment,
        chat_provider=settings.chat_provider,
        chat_model=chat_model,
        embedding_model=settings.embedding_model,
        reranker_model=settings.reranker_model,
        parent_chunk_size=settings.parent_chunk_size,
        parent_chunk_overlap=settings.parent_chunk_overlap,
        child_chunk_size=settings.child_chunk_size,
        child_chunk_overlap=settings.child_chunk_overlap,
        retrieval_k=settings.retrieval_k,
        rerank_top_n=settings.rerank_top_n,
        history_max_messages=settings.history_max_messages,
        max_upload_mb=settings.max_upload_mb,
        eval_judge=settings.eval_judge,
        eval_threshold=settings.eval_threshold,
    )
