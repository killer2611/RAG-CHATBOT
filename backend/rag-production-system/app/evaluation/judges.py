from __future__ import annotations

import os

from deepeval.models import GeminiModel, OllamaModel

from app.core.config import Settings


def build_judge(settings: Settings, override: str | None = None):
    provider = override or settings.eval_judge
    # DeepEval already retries transient failures with exponential backoff. These flags
    # increase the retry budget for provider-side 429/5xx behavior without duplicating
    # the whole evaluation loop in application code.
    os.environ.setdefault("DEEPEVAL_RETRY_MAX_ATTEMPTS", "5")
    os.environ.setdefault("DEEPEVAL_RETRY_CAP_SECONDS", "30")

    if provider == "ollama":
        return OllamaModel(
            model=settings.eval_ollama_model,
            base_url=settings.eval_ollama_base_url,
            temperature=0,
        )
    if provider == "gemini":
        key = settings.eval_gemini_api_key or settings.gemini_api_key
        if not key:
            raise RuntimeError("GEMINI API key is required for Gemini evaluation")
        return GeminiModel(model=settings.eval_gemini_model, api_key=key, temperature=0)
    raise ValueError(f"Unsupported evaluation judge: {provider}")
