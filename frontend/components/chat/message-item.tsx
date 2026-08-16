"use client";

import { memo } from "react";
import { User, Sparkles } from "lucide-react";
import { MarkdownContent } from "@/components/chat/markdown-content";
import { SourceCitations } from "@/components/chat/source-citations";
import type { SourceCitation } from "@/types/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: SourceCitation[];
}

interface MessageItemProps {
  message: ChatMessage;
  onInspectEvidence?: (sources: SourceCitation[], index: number) => void;
}

export const MessageItem = memo(function MessageItem({
  message,
  onInspectEvidence,
}: MessageItemProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={`flex gap-3.5 py-4 ${
        isUser ? "bg-transparent" : "bg-surface-raised/40 -mx-4 px-4 rounded-xl"
      }`}
      aria-label={`${isUser ? "User message" : "Assistant message"}`}
    >
      {/* Avatar */}
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-semibold ${
          isUser
            ? "bg-surface-elevated text-text-secondary"
            : "bg-accent text-text-inverse shadow-sm"
        }`}
      >
        {isUser ? <User size={15} /> : <Sparkles size={15} />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-text-primary">
            {isUser ? "You" : "RAG Assistant"}
          </span>
        </div>

        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-primary">
            {message.content}
          </p>
        ) : (
          <div>
            <MarkdownContent content={message.content} />
            {message.sources && message.sources.length > 0 && (
              <SourceCitations
                sources={message.sources}
                onInspect={onInspectEvidence}
              />
            )}
          </div>
        )}
      </div>
    </article>
  );
});
