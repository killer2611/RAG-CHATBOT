"use client";

import { memo, useRef, useEffect, useState, useCallback } from "react";
import { ArrowUp, Square } from "lucide-react";

interface ChatComposerProps {
  isStreaming: boolean;
  onSend: (message: string) => void;
  onAbort: () => void;
  disabled?: boolean;
}

export const ChatComposer = memo(function ChatComposer({
  isStreaming,
  onSend,
  onAbort,
  disabled = false,
}: ChatComposerProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const nextHeight = Math.min(textarea.scrollHeight, 180);
    textarea.style.height = `${Math.max(nextHeight, 44)}px`;
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [input, adjustHeight]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (isStreaming) {
      onAbort();
      return;
    }
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "44px";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSubmit = input.trim().length > 0 && !disabled;

  return (
    <div className="relative border-t border-border-subtle bg-surface-base px-4 py-3 sm:px-6">
      <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
        <div className="relative flex items-end rounded-xl border border-border-subtle bg-surface-raised transition-colors focus-within:border-accent">
          {/* Multiline Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isStreaming
                ? "Waiting for response to finish…"
                : "Ask a question about your indexed knowledge base…"
            }
            rows={1}
            disabled={disabled}
            aria-label="Chat input message"
            className="w-full resize-none bg-transparent px-4 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none disabled:opacity-50 min-h-[44px] max-h-[180px]"
          />

          {/* Action Button: Send or Stop */}
          <div className="p-2 shrink-0">
            {isStreaming ? (
              <button
                type="button"
                onClick={onAbort}
                aria-label="Stop generation"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-elevated text-text-primary transition-colors hover:bg-surface-overlay hover:text-error"
                title="Stop generation"
              >
                <Square size={14} className="fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!canSubmit}
                aria-label="Send message"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-text-inverse transition-all hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-30 shadow-sm"
              >
                <ArrowUp size={16} strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>

        {/* Helper text */}
        <div className="mt-1.5 flex items-center justify-between px-1 text-[11px] text-text-tertiary">
          <span>
            Press <kbd className="rounded bg-surface-elevated px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to send, <kbd className="rounded bg-surface-elevated px-1 py-0.5 font-mono text-[10px]">Shift+Enter</kbd> for newline
          </span>
          {isStreaming && (
            <span className="text-accent font-medium animate-pulse">
              Generating answer…
            </span>
          )}
        </div>
      </form>
    </div>
  );
});
