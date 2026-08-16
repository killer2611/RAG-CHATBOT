"use client";

import { memo, useEffect, useRef } from "react";
import { MessageItem, type ChatMessage } from "@/components/chat/message-item";
import { ActiveStreamingMessage } from "@/components/chat/active-streaming-message";
import { EmptyChatState } from "@/components/chat/empty-chat-state";
import type { SourceCitation } from "@/types/api";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingTokens: string;
  streamingSources: SourceCitation[];
  streamingError: string | null;
  onSelectPrompt: (prompt: string) => void;
  onRetry?: () => void;
  onInspectEvidence?: (sources: SourceCitation[], index: number) => void;
}

export const MessageList = memo(function MessageList({
  messages,
  isStreaming,
  streamingTokens,
  streamingSources,
  streamingError,
  onSelectPrompt,
  onRetry,
  onInspectEvidence,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom smoothly on message update or stream
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingTokens]);

  const isEmpty = messages.length === 0 && !isStreaming && !streamingError;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto flex max-w-3xl flex-col min-h-full">
        {isEmpty ? (
          <EmptyChatState onSelectPrompt={onSelectPrompt} />
        ) : (
          <div className="divide-y divide-border-subtle/50">
            {/* Historical Turns */}
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onInspectEvidence={onInspectEvidence}
              />
            ))}

            {/* Active Streaming Turn (Isolated Leaf) */}
            {(isStreaming || streamingError) && (
              <ActiveStreamingMessage
                tokens={streamingTokens}
                sources={streamingSources}
                isStreaming={isStreaming}
                error={streamingError}
                onRetry={onRetry}
                onInspectEvidence={onInspectEvidence}
              />
            )}
          </div>
        )}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
});
