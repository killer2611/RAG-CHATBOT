from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.core.config import Settings, get_settings


@lru_cache(maxsize=4)
def get_chat_model(provider: str, model: str, temperature: float, api_key: str | None, base_url: str) -> BaseChatModel:
    if provider == "groq":
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is required when CHAT_PROVIDER=groq")
        return ChatGroq(model=model, api_key=api_key, temperature=temperature)
    if provider == "gemini":
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required when CHAT_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=temperature)
    if provider == "ollama":
        return ChatOllama(model=model, base_url=base_url, temperature=temperature)
    raise ValueError(f"Unsupported chat provider: {provider}")


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()
    api_key = settings.groq_api_key if settings.chat_provider == "groq" else settings.gemini_api_key
    model = settings.groq_model if settings.chat_provider == "groq" else settings.gemini_model
    if settings.chat_provider == "ollama":
        model = settings.ollama_model
    return get_chat_model(
        settings.chat_provider,
        model,
        settings.chat_temperature,
        api_key,
        settings.ollama_base_url,
    )
