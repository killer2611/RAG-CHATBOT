import { config } from "@/lib/config";
import type { ChatRequest, SourceCitation } from "@/types/api";

export interface StreamCallbacks {
  onSources?: (sources: SourceCitation[]) => void;
  onToken?: (token: string) => void;
  onDone?: (data: { session_id: string }) => void;
  onError?: (error: Error) => void;
}

/**
 * Streams chat responses from POST /chat using fetch + ReadableStream.
 *
 * Implements full Server-Sent Events (SSE) parsing for POST requests:
 * - Line buffer accumulation across chunk boundaries
 * - Event type and data payload extraction preserved across TCP packets
 * - Support for AbortController cancellation
 * - Zero native EventSource dependency (which only supports GET)
 */
export async function streamChat(
  request: ChatRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const base = config.apiBaseUrl.replace(/\/+$/, "");
  const url = `${base}/chat`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ ...request, stream: true }),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) {
      // Intentional abort — do not treat as error
      return;
    }
    const error = err instanceof Error ? err : new Error("Failed to connect to chat stream");
    callbacks.onError?.(error);
    return;
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson?.detail) detail = errJson.detail;
    } catch {
      // fallback
    }
    const error = new Error(`Chat stream error (${response.status}): ${detail}`);
    callbacks.onError?.(error);
    return;
  }

  if (!response.body) {
    callbacks.onError?.(new Error("Response body is empty"));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let currentEvent: string | null = null;
  let currentData: string | null = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // Keep the incomplete trailing fragment in the buffer
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          // Empty line indicates event boundary in SSE specification
          if (currentEvent && currentData !== null) {
            dispatchEvent(currentEvent, currentData, callbacks);
          }
          currentEvent = null;
          currentData = null;
          continue;
        }

        if (trimmed.startsWith("event:")) {
          currentEvent = trimmed.slice(6).trim();
        } else if (trimmed.startsWith("data:")) {
          const dataStr = trimmed.slice(5).trim();
          currentData = currentData === null ? dataStr : `${currentData}\n${dataStr}`;
        }
      }
    }

    // Process any trailing event remaining in the buffer when stream completes
    if (currentEvent && currentData !== null) {
      dispatchEvent(currentEvent, currentData, callbacks);
      currentEvent = null;
      currentData = null;
    }
  } catch (err) {
    if (signal?.aborted) {
      return;
    }
    const error = err instanceof Error ? err : new Error("Stream reading failed");
    callbacks.onError?.(error);
  } finally {
    reader.releaseLock();
  }
}

function dispatchEvent(
  event: string,
  rawPayload: string,
  callbacks: StreamCallbacks
): void {
  try {
    const parsed = JSON.parse(rawPayload);
    switch (event) {
      case "sources":
        if (Array.isArray(parsed)) {
          callbacks.onSources?.(parsed as SourceCitation[]);
        }
        break;
      case "token":
        if (typeof parsed === "string") {
          callbacks.onToken?.(parsed);
        }
        break;
      case "done":
        callbacks.onDone?.(parsed as { session_id: string });
        break;
      case "error":
        callbacks.onError?.(new Error(parsed?.detail ?? "Stream error received"));
        break;
      default:
        // Ignore unrecognized future events safely
        break;
    }
  } catch {
    // If payload is not JSON (e.g. raw string token)
    if (event === "token") {
      callbacks.onToken?.(rawPayload);
    }
  }
}
