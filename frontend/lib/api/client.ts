import { config } from "@/lib/config";
import type {
  ChatRequest,
  ChatResponse,
  DocumentSummary,
  EvaluateRequest,
  EvaluationResultsResponse,
  HealthResponse,
  IngestResponse,
  JobStatus,
  SessionHistoryResponse,
  SessionSummary,
  SystemInfoResponse,
} from "@/types/api";

/**
 * Generic API error with HTTP status and detail.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public endpoint: string
  ) {
    super(`API Error ${status} on ${endpoint}: ${detail}`);
    this.name = "ApiError";
  }
}

/**
 * Base fetch wrapper handling JSON headers, baseUrl resolution, and error normalization.
 */
async function apiFetch<T>(
  endpoint: string,
  init?: RequestInit
): Promise<T> {
  const base = config.apiBaseUrl.replace(/\/+$/, "");
  const url = `${base}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network request failed";
    throw new ApiError(0, message, endpoint);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson && typeof errJson.detail === "string") {
        detail = errJson.detail;
      }
    } catch {
      // Use statusText if body is not JSON
    }
    throw new ApiError(response.status, detail, endpoint);
  }

  return response.json() as Promise<T>;
}

// ── HEALTH & SYSTEM ──

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function getSystemInfo(): Promise<SystemInfoResponse> {
  return apiFetch<SystemInfoResponse>("/system/info");
}

// ── CHAT ──

export async function postChat(
  request: ChatRequest,
  options?: { signal?: AbortSignal }
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, stream: false }),
    signal: options?.signal,
  });
}

export async function getChatSessions(): Promise<SessionSummary[]> {
  return apiFetch<SessionSummary[]>("/chat/sessions");
}

export async function getChatMessages(
  sessionId: string
): Promise<SessionHistoryResponse> {
  const encoded = encodeURIComponent(sessionId);
  return apiFetch<SessionHistoryResponse>(`/chat/${encoded}/messages`);
}

// ── INGESTION & DOCUMENTS ──

export async function postIngest(file: File): Promise<IngestResponse> {
  const base = config.apiBaseUrl.replace(/\/+$/, "");
  const url = `${base}/ingest`;

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(url, {
    method: "POST",
    body: formData,
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson && typeof errJson.detail === "string") {
        detail = errJson.detail;
      }
    } catch {
      // Ignore fallback
    }
    throw new ApiError(response.status, detail, "/ingest");
  }

  return response.json() as Promise<IngestResponse>;
}

export async function getDocuments(): Promise<DocumentSummary[]> {
  return apiFetch<DocumentSummary[]>("/documents");
}

// ── EVALUATION ──

export async function postEvaluate(
  request: EvaluateRequest
): Promise<JobStatus> {
  return apiFetch<JobStatus>("/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export async function getEvaluateStatus(jobId: string): Promise<JobStatus> {
  const encoded = encodeURIComponent(jobId);
  return apiFetch<JobStatus>(`/evaluate/${encoded}`);
}

export async function getEvaluateResults(
  jobId: string
): Promise<EvaluationResultsResponse> {
  const encoded = encodeURIComponent(jobId);
  return apiFetch<EvaluationResultsResponse>(`/evaluate/${encoded}/results`);
}
