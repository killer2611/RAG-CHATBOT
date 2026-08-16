"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat } from "@/lib/streaming/chat-stream";
import type { SourceCitation } from "@/types/api";

export type ChatStreamStatus = "idle" | "streaming" | "completed" | "error";

interface UseChatStreamOptions {
  onSources?: (sources: SourceCitation[]) => void;
  onToken?: (token: string) => void;
  onDone?: (
    sessionId: string,
    fullAnswer: string,
    sources: SourceCitation[]
  ) => void;
  onError?: (error: Error) => void;
}

interface UseChatStreamReturn {
  status: ChatStreamStatus;
  tokens: string;
  sources: SourceCitation[];
  error: string | null;
  sendMessage: (sessionId: string, message: string) => Promise<void>;
  abort: () => void;
  reset: () => void;
}

/**
 * Custom hook providing a typed, cancellation-capable streaming chat controller.
 *
 * Implements:
 * - Isolation of incoming token stream to prevent broad component re-renders
 * - Automatic AbortController lifecycle management
 * - Strict error normalization without raw stack trace leakage
 */
export function useChatStream(
  options?: UseChatStreamOptions
): UseChatStreamReturn {
  const [status, setStatus] = useState<ChatStreamStatus>("idle");
  const [tokens, setTokens] = useState<string>("");
  const [sources, setSources] = useState<SourceCitation[]>([]);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const fullAnswerRef = useRef<string>("");
  const currentSourcesRef = useRef<SourceCitation[]>([]);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setStatus("idle");
    }
  }, []);

  const reset = useCallback(() => {
    abort();
    setStatus("idle");
    setTokens("");
    setSources([]);
    setError(null);
    fullAnswerRef.current = "";
    currentSourcesRef.current = [];
  }, [abort]);

  const sendMessage = useCallback(
    async (sessionId: string, message: string) => {
      // Abort any ongoing stream before starting a new turn
      abort();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus("streaming");
      setTokens("");
      setSources([]);
      setError(null);
      fullAnswerRef.current = "";
      currentSourcesRef.current = [];

      await streamChat(
        {
          session_id: sessionId,
          message,
          stream: true,
        },
        {
          onSources: (incomingSources) => {
            currentSourcesRef.current = incomingSources;
            setSources(incomingSources);
            options?.onSources?.(incomingSources);
          },
          onToken: (token) => {
            fullAnswerRef.current += token;
            setTokens((prev) => prev + token);
            options?.onToken?.(token);
          },
          onDone: (data) => {
            setStatus("completed");
            options?.onDone?.(
              data.session_id,
              fullAnswerRef.current,
              currentSourcesRef.current
            );
          },
          onError: (err) => {
            setStatus("error");
            setError(err.message);
            options?.onError?.(err);
          },
        },
        controller.signal
      );
    },
    [abort, options]
  );

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    status,
    tokens,
    sources,
    error,
    sendMessage,
    abort,
    reset,
  };
}
