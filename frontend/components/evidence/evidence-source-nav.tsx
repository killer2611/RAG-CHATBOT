"use client";

import { memo } from "react";
import type { SourceCitation } from "@/types/api";

interface EvidenceSourceNavProps {
  sources: SourceCitation[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

export const EvidenceSourceNav = memo(function EvidenceSourceNav({
  sources,
  selectedIndex,
  onSelect,
}: EvidenceSourceNavProps) {
  if (sources.length <= 1) return null;

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-none" role="tablist" aria-label="Evidence Sources Navigation">
      {sources.map((source, idx) => {
        const isSelected = selectedIndex === idx;
        const scorePercent =
          source.score !== null && source.score !== undefined
            ? `${(source.score * 100).toFixed(0)}%`
            : null;

        return (
          <button
            key={`${source.parent_id}-${idx}`}
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(idx)}
            className={`flex items-center gap-1.5 shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
              isSelected
                ? "bg-accent text-text-inverse font-semibold shadow-sm"
                : "bg-surface-raised border border-border-subtle text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
            }`}
          >
            <span className="truncate max-w-[110px]">{source.source_name}</span>
            {scorePercent && (
              <span
                className={`rounded px-1 text-[10px] ${
                  isSelected
                    ? "bg-white/20 text-text-inverse"
                    : "bg-surface-elevated text-accent"
                }`}
              >
                {scorePercent}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
});
