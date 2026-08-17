from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings


@lru_cache(maxsize=8)
def get_chat_model(
    provider: str,
    model: str,
    temperature: float,
    api_key: str | None,
    base_url: str,
) -> BaseChatModel:
    if provider == "groq":
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is required when CHAT_PROVIDER=groq")
        return ChatGroq(model=model, api_key=api_key, temperature=temperature)

    if provider == "gemini":
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required when CHAT_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )

    if provider == "ollama":
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported chat provider: {provider}")


@lru_cache(maxsize=4)
def get_deepseek_generation_model(
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
) -> BaseChatModel:
    """Dedicated cloud model for evaluation-time RAG answer generation."""
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        temperature=temperature,
        timeout=60,
        max_retries=2,
    )


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()

    if settings.chat_provider == "groq":
        api_key = settings.groq_api_key
        model = settings.groq_model
    elif settings.chat_provider == "gemini":
        api_key = settings.gemini_api_key
        model = settings.gemini_model
    elif settings.chat_provider == "ollama":
        api_key = None
        model = settings.ollama_model
    else:
        raise ValueError(f"Unsupported chat provider: {settings.chat_provider}")

    return get_chat_model(
        settings.chat_provider,
        model,
        settings.chat_temperature,
        api_key,
        settings.ollama_base_url,
    )


def build_evaluation_generation_model(
    settings: Settings | None = None,
) -> BaseChatModel:
    """
    Dedicated cloud model used only for evaluation-time RAG answer generation.

    Evaluation path:
        retrieval -> DeepSeek generation -> DeepEval DeepSeek judge

    This intentionally does NOT use CHAT_PROVIDER.
    """
    settings = settings or get_settings()

    if not settings.eval_deepseek_api_key:
        raise RuntimeError(
            "EVAL_DEEPSEEK_API_KEY is required for evaluation generation."
        )

    return get_deepseek_generation_model(
        api_key=settings.eval_deepseek_api_key,
        base_url=settings.eval_deepseek_base_url,
        model=settings.eval_deepseek_model,
        temperature=0.0,
    )


# Backward-compatible name used by app.rag.service.
# Evaluation generation is deliberately DeepSeek-only.
def build_evaluation_model(
    settings: Settings | None = None,
) -> BaseChatModel:
    return build_evaluation_generation_model(settings)
