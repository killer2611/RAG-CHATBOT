"use client";

import { memo } from "react";
import { Sparkles, BookOpen, ShieldCheck, ArrowRight } from "lucide-react";

interface EmptyChatStateProps {
  onSelectPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS = [
  "Summarize the key findings from the ingested documents.",
  "What methodology was used in the evaluation benchmark?",
  "What are the main architectural components described in the text?",
  "Compare the performance metrics across the tested models.",
];

export const EmptyChatState = memo(function EmptyChatState({
  onSelectPrompt,
}: EmptyChatStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-12 text-center my-auto">
      {/* Brand Icon */}
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-subtle text-accent mb-4 shadow-sm">
        <Sparkles size={24} />
      </div>

      <h2 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
        Evidence-Grounded RAG Workspace
      </h2>
      <p className="mt-2 max-w-md text-xs leading-relaxed text-text-secondary sm:text-sm">
        Ask questions against your indexed documents. Answers are strictly synthesized
        from retrieved hierarchical chunks with source attribution.
      </p>

      {/* Feature Pills */}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-xs text-text-tertiary">
        <span className="flex items-center gap-1.5 rounded-full border border-border-subtle bg-surface-raised px-3 py-1">
          <BookOpen size={13} className="text-accent" />
          Hierarchical Retrieval
        </span>
        <span className="flex items-center gap-1.5 rounded-full border border-border-subtle bg-surface-raised px-3 py-1">
          <ShieldCheck size={13} className="text-success" />
          Strict Grounding
        </span>
      </div>

      {/* Suggested Prompts */}
      <div className="mt-8 w-full max-w-lg space-y-2">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary mb-2">
          Suggested Inquiries
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onSelectPrompt(prompt)}
              className="flex items-center justify-between gap-2 rounded-xl border border-border-subtle bg-surface-raised p-3 text-left text-xs text-text-secondary transition-all hover:border-border-default hover:bg-surface-overlay hover:text-text-primary group"
            >
              <span className="line-clamp-2">{prompt}</span>
              <ArrowRight
                size={14}
                className="shrink-0 text-text-tertiary group-hover:text-accent transition-colors"
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});
