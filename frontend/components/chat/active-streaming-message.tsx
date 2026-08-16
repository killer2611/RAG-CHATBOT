"use client";

import { memo } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { MarkdownContent } from "@/components/chat/markdown-content";
import { SourceCitations } from "@/components/chat/source-citations";
import type { SourceCitation } from "@/types/api";

interface ActiveStreamingMessageProps {
  tokens: string;
  sources: SourceCitation[];
  isStreaming: boolean;
  error: string | null;
  onRetry?: () => void;
  onInspectEvidence?: (sources: SourceCitation[], index: number) => void;
}

export const ActiveStreamingMessage = memo(function ActiveStreamingMessage({
  tokens,
  sources,
  isStreaming,
  error,
  onRetry,
  onInspectEvidence,
}: ActiveStreamingMessageProps) {
  return (
    <article
      className="flex gap-3.5 py-4 bg-surface-raised/40 -mx-4 px-4 rounded-xl"
      aria-label="Active assistant response"
    >
      {/* Avatar */}
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent text-xs font-semibold text-text-inverse shadow-sm">
        {isStreaming ? (
          <Loader2 size={15} className="animate-spin" />
        ) : (
          <Sparkles size={15} />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-text-primary">
            RAG Assistant
          </span>
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-[11px] text-text-tertiary">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
              Thinking & synthesizing…
            </span>
          )}
        </div>

        {/* Dedicated polite live region for screen readers */}
        <div className="sr-only" aria-live="polite">
          {isStreaming
            ? "Assistant is generating response"
            : error
            ? `Error: ${error}`
            : "Assistant completed response"}
        </div>

        {/* Tokens & Markdown */}
        {tokens ? (
          <div className="relative">
            <MarkdownContent content={tokens} />
            {isStreaming && (
              <span className="inline-block h-4 w-1.5 animate-pulse bg-accent align-middle ml-1" />
            )}
          </div>
        ) : isStreaming ? (
          <div className="flex items-center gap-2 text-xs text-text-secondary py-1">
            <span className="h-2 w-2 animate-ping rounded-full bg-accent" />
            <span>Searching knowledge base and formulating grounded answer…</span>
          </div>
        ) : null}

        {/* Error State */}
        {error && (
          <div className="mt-2 rounded-lg border border-error/30 bg-error/10 p-3 text-xs text-error">
            <p className="font-semibold">Unable to complete response</p>
            <p className="mt-0.5 text-text-secondary">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2 rounded bg-surface-elevated px-2.5 py-1 text-xs font-medium text-text-primary hover:bg-surface-overlay"
              >
                Retry request
              </button>
            )}
          </div>
        )}

        {/* Grounding Sources */}
        {sources && sources.length > 0 && (
          <SourceCitations
            sources={sources}
            onInspect={onInspectEvidence}
          />
        )}
      </div>
    </article>
  );
});
