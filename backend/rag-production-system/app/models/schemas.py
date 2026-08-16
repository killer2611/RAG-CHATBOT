from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=12000)
    stream: bool = False


class SourceCitation(BaseModel):
    source_id: str
    source_name: str
    page: int | None = None
    parent_id: str
    score: float | None = None
    excerpt: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceCitation]


class SessionSummary(BaseModel):
    session_id: str
    message_count: int
    updated_at: datetime | None = None
    preview: str | None = None


class ChatMessageItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageItem]


class IngestResponse(BaseModel):
    source_id: str
    source_name: str
    documents: int
    parents: int
    children: int
    status: Literal["indexed", "replaced"]


class DocumentSummary(BaseModel):
    source_id: str
    source_name: str
    parents: int
    children: int | None = None
    status: Literal["indexed", "replaced"] = "indexed"
    created_at: datetime | None = None


class EvaluateRequest(BaseModel):
    judge: Literal["ollama", "gemini"] | None = None
    test_file: str | None = None


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100)
    message: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    report_path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricDetail(BaseModel):
    name: str
    score: float | None = None
    passed: bool | None = None
    reason: str | None = None
    error: str | None = None


class TestCaseResult(BaseModel):
    question: str
    expected_output: str | None = None
    actual_output: str | None = None
    success: bool
    metrics: dict[str, MetricDetail] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    total_cases: int
    passed_cases: int
    average_scores: dict[str, float] = Field(default_factory=dict)


class EvaluationResultsResponse(BaseModel):
    job_id: str
    status: str
    completed_at: datetime | None = None
    summary: EvaluationSummary
    test_cases: list[TestCaseResult]


class SystemInfoResponse(BaseModel):
    app_name: str
    environment: str
    chat_provider: str
    chat_model: str
    embedding_model: str
    reranker_model: str
    parent_chunk_size: int
    parent_chunk_overlap: int
    child_chunk_size: int
    child_chunk_overlap: int
    retrieval_k: int
    rerank_top_n: int
    history_max_messages: int
    max_upload_mb: int
    eval_judge: str
    eval_threshold: float
