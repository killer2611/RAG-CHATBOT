from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "rag-production-system"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:8501"

    # Normal chat
    chat_provider: Literal["groq", "gemini", "ollama"] = "groq"

    groq_api_key: str | None = None
    groq_model: str = "qwen/qwen3.6-27b"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    chat_temperature: float = 0.1

    # Retrieval
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_device: str | None = None

    vector_store_dir: Path = Path("data/vectorstore")
    parent_store_db: Path = Path("data/parent_store/parents.sqlite3")

    parent_chunk_size: int = 800
    parent_chunk_overlap: int = 150
    child_chunk_size: int = 300
    child_chunk_overlap: int = 60
    retrieval_k: int = 10
    rerank_top_n: int = 3

    # Application state
    database_url: str = "sqlite+aiosqlite:///./data/chat_history.sqlite3"
    history_max_messages: int = 24
    max_upload_mb: int = 25

    # Evaluation judge
    eval_judge: Literal["deepseek", "sambanova"] = "deepseek"

    eval_deepseek_api_key: str | None = None
    eval_deepseek_base_url: str = "https://api.deepseek.com"
    eval_deepseek_model: str = "deepseek-v4-flash"

    eval_sambanova_api_key: str | None = None
    eval_sambanova_base_url: str = "https://api.sambanova.ai/v1"
    eval_sambanova_model: str = "Meta-Llama-3.3-70B-Instruct"

    # Evaluation answer generation is ALWAYS DeepSeek.
    eval_generation_provider: Literal["deepseek"] = "deepseek"
    eval_generation_model: str = "deepseek-v4-flash"
    eval_generation_temperature: float = 0.0

    eval_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    eval_max_concurrent: int = Field(default=1, ge=1)
    eval_throttle_seconds: float = Field(default=2.0, ge=0.0)
    eval_report_dir: Path = Path("data/reports")

    job_ttl_seconds: int = 86400

    def ensure_directories(self) -> None:
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.parent_store_db.parent.mkdir(parents=True, exist_ok=True)
        self.eval_report_dir.mkdir(parents=True, exist_ok=True)
        Path("data/documents").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
