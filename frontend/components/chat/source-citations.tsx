"use client";

import { memo, useState } from "react";
import { ChevronDown, ChevronRight, FileText, ExternalLink } from "lucide-react";
import type { SourceCitation } from "@/types/api";

interface SourceCitationsProps {
  sources: SourceCitation[];
  onInspect?: (sources: SourceCitation[], index: number) => void;
}

export const SourceCitations = memo(function SourceCitations({
  sources,
  onInspect,
}: SourceCitationsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-border-subtle pt-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-semibold tracking-wider uppercase text-text-tertiary">
          Evidence Sources ({sources.length})
        </span>
        {onInspect && (
          <button
            onClick={() => onInspect(sources, 0)}
            className="flex items-center gap-1 text-[11px] font-medium text-accent hover:text-accent-hover transition-colors focus-visible:outline-none"
          >
            <ExternalLink size={12} />
            <span>Open Inspector</span>
          </button>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        {sources.map((source, idx) => {
          const isExpanded = expandedIndex === idx;
          const scorePercent =
            source.score !== null && source.score !== undefined
              ? `${(source.score * 100).toFixed(0)}% match`
              : null;

          return (
            <div
              key={`${source.parent_id}-${idx}`}
              className="rounded-lg border border-border-subtle bg-surface-base text-xs transition-colors hover:border-border-default"
            >
              <div className="flex w-full items-center justify-between p-2.5">
                <button
                  onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                  aria-expanded={isExpanded}
                  className="flex items-center gap-2 min-w-0 pr-2 text-left focus-visible:outline-none flex-1"
                >
                  <FileText size={14} className="shrink-0 text-accent" />
                  <span className="truncate font-medium text-text-primary">
                    {source.source_name}
                  </span>
                  {source.page !== null && source.page !== undefined && (
                    <span className="shrink-0 rounded bg-surface-elevated px-1.5 py-0.5 text-[10px] text-text-secondary">
                      p. {source.page}
                    </span>
                  )}
                </button>

                <div className="flex items-center gap-2 shrink-0">
                  {scorePercent && (
                    <span className="rounded bg-accent-subtle px-1.5 py-0.5 text-[10px] font-medium text-accent">
                      {scorePercent}
                    </span>
                  )}
                  {onInspect && (
                    <button
                      onClick={() => onInspect(sources, idx)}
                      title="Inspect evidence in detail"
                      aria-label={`Inspect evidence for ${source.source_name}`}
                      className="rounded p-1 text-text-tertiary hover:bg-surface-elevated hover:text-accent transition-colors"
                    >
                      <ExternalLink size={13} />
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    aria-label={isExpanded ? "Collapse excerpt" : "Expand excerpt"}
                    className="p-0.5 text-text-tertiary hover:text-text-primary"
                  >
                    {isExpanded ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t border-border-subtle bg-surface-raised p-2.5 text-text-secondary leading-relaxed font-mono text-[11px] select-text">
                  <p className="whitespace-pre-wrap">{source.excerpt}</p>
                  {onInspect && (
                    <div className="mt-2 pt-2 border-t border-border-subtle/50 flex justify-end">
                      <button
                        onClick={() => onInspect(sources, idx)}
                        className="text-[11px] font-medium text-accent hover:text-accent-hover flex items-center gap-1"
                      >
                        <ExternalLink size={11} />
                        <span>Inspect Full Evidence & Details</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});
