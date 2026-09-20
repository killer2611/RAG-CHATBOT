from __future__ import annotations

import os

from deepeval.models import OpenAIModel

from app.core.config import Settings


def build_judge(settings: Settings, override: str | None = None):
    """
    Build the cloud LLM used by DeepEval.

    Evaluation is intentionally cloud-only:
      - deepseek  -> DeepSeek V4 Flash (primary)
      - sambanova -> SambaNova hosted model (secondary/free option)
    """
    provider = (override or settings.eval_judge).strip().lower()

    # The previous run hit DeepEval's default ~32s per-attempt timeout.
    # DeepSeek responses were reaching the API successfully, but some metric
    # requests exceeded that client-side limit. Give individual judge calls
    # more room while keeping retries bounded.
    os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "300")
    os.environ.setdefault("DEEPEVAL_RETRY_MAX_ATTEMPTS", "2")
    os.environ.setdefault("DEEPEVAL_RETRY_CAP_SECONDS", "20")

    if provider == "deepseek":
        key = settings.eval_deepseek_api_key
        if not key:
            raise RuntimeError(
                "DEEPSEEK evaluation API key is required. "
                "Set EVAL_DEEPSEEK_API_KEY in .env."
            )

        return OpenAIModel(
            model=settings.eval_deepseek_model,
            api_key=key,
            base_url=settings.eval_deepseek_base_url,
            temperature=0,
        )

    if provider == "sambanova":
        key = settings.eval_sambanova_api_key
        if not key:
            raise RuntimeError(
                "SAMBANOVA evaluation API key is required. "
                "Set EVAL_SAMBANOVA_API_KEY in .env."
            )

        return OpenAIModel(
            model=settings.eval_sambanova_model,
            api_key=key,
            base_url=settings.eval_sambanova_base_url,
            temperature=0,
        )

    raise ValueError(
        f"Unsupported evaluation judge: {provider!r}. "
        "Evaluation is cloud-only; use 'deepseek' or 'sambanova'."
    )
