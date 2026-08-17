/**
 * Typed API Contracts for the Flagship RAG Knowledge Platform.
 * Aligned 1:1 with backend Pydantic models in app.models.schemas.
 */

export interface HealthResponse {
  status: string;
}

export interface SourceCitation {
  source_id: string;
  source_name: string;
  page?: number | null;
  parent_id: string;
  score?: number | null;
  excerpt: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: SourceCitation[];
}

export interface SessionSummary {
  session_id: string;
  message_count: number;
  updated_at?: string | null;
  preview?: string | null;
}

export interface ChatMessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: ChatMessageItem[];
}

export interface IngestResponse {
  source_id: string;
  source_name: string;
  documents: number;
  parents: number;
  children: number;
  status: "indexed" | "replaced";
}

export interface DocumentSummary {
  source_id: string;
  source_name: string;
  parents: number;
  children?: number | null;
  status: "indexed" | "replaced";
  created_at?: string | null;
}

export interface EvaluateRequest {
  judge?: "deepseek" | "sambanova" | null;
  test_file?: string | null;
}

export type JobStatusType = "queued" | "running" | "completed" | "failed";

export interface JobStatus {
  job_id: string;
  status: JobStatusType;
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string | null;
  report_path?: string | null;
  error?: string | null;
  metadata?: Record<string, unknown>;
}

export interface MetricDetail {
  name: string;
  score?: number | null;
  passed?: boolean | null;
  reason?: string | null;
  error?: string | null;
}

export interface TestCaseResult {
  question: string;
  expected_output?: string | null;
  actual_output?: string | null;
  success: boolean;
  metrics: Record<string, MetricDetail>;
}

export interface EvaluationSummary {
  total_cases: number;
  passed_cases: number;
  average_scores: Record<string, number>;
}

export interface EvaluationResultsResponse {
  job_id: string;
  status: string;
  completed_at?: string | null;
  summary: EvaluationSummary;
  test_cases: TestCaseResult[];
}

export interface SystemInfoResponse {
  app_name: string;
  environment: string;
  chat_provider: string;
  chat_model: string;
  embedding_model: string;
  reranker_model: string;
  parent_chunk_size: number;
  parent_chunk_overlap: number;
  child_chunk_size: number;
  child_chunk_overlap: number;
  retrieval_k: number;
  rerank_top_n: number;
  history_max_messages: number;
  max_upload_mb: number;
  eval_judge: string;
  eval_threshold: number;
}

/**
 * Normalized SSE Stream Event definitions emitted during POST /chat (stream=true).
 */
export type StreamEvent =
  | { event: "sources"; data: SourceCitation[] }
  | { event: "token"; data: string }
  | { event: "done"; data: { session_id: string } }
  | { event: "error"; data: { detail: string } };
