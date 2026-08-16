from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.evaluation.runner import EvaluationRunner
from app.rag.retriever import HierarchicalRetriever
from app.rag.service import HistoryStore, RagService


@lru_cache(maxsize=1)
def get_retriever() -> HierarchicalRetriever:
    return HierarchicalRetriever(get_settings())


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    settings = get_settings()
    return RagService(settings, get_retriever(), HistoryStore(settings))


@lru_cache(maxsize=1)
def get_evaluation_runner() -> EvaluationRunner:
    settings = get_settings()
    return EvaluationRunner(settings, get_rag_service())
