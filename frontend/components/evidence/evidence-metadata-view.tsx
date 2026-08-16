"use client";

import { memo, useState } from "react";
import { ChevronDown, ChevronRight, Hash, Database, Info } from "lucide-react";
import type { SourceCitation } from "@/types/api";

interface EvidenceMetadataViewProps {
  source: SourceCitation;
}

export const EvidenceMetadataView = memo(function EvidenceMetadataView({
  source,
}: EvidenceMetadataViewProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-lg border border-border-subtle bg-surface-raised/60 text-xs">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        className="flex w-full items-center justify-between p-3 text-left text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none"
      >
        <span className="flex items-center gap-2 font-medium">
          <Info size={14} className="text-accent" />
          Technical Retrieval Details
        </span>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>

      {isOpen && (
        <div className="border-t border-border-subtle p-3 space-y-2 font-mono text-[11px] text-text-secondary">
          {/* Parent Chunk ID */}
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase font-semibold text-text-tertiary flex items-center gap-1">
              <Hash size={11} /> Parent Chunk ID
            </span>
            <span className="select-all break-all rounded bg-surface-base px-2 py-1 text-text-primary border border-border-subtle">
              {source.parent_id || "n/a"}
            </span>
          </div>

          {/* Document Source ID */}
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase font-semibold text-text-tertiary flex items-center gap-1">
              <Database size={11} /> Source Document ID
            </span>
            <span className="select-all break-all rounded bg-surface-base px-2 py-1 text-text-primary border border-border-subtle">
              {source.source_id || "n/a"}
            </span>
          </div>

          {/* Text Excerpt Statistics */}
          <div className="flex items-center justify-between pt-1 text-text-tertiary text-[10px]">
            <span>Chunk Length: {source.excerpt?.length ?? 0} chars</span>
            <span>Approx. {(source.excerpt?.split(/\s+/).length ?? 0)} words</span>
          </div>
        </div>
      )}
    </div>
  );
});
