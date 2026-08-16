"use client";

import { memo, useState } from "react";
import { FileText, Copy, Check, Sparkles } from "lucide-react";
import { EvidenceMetadataView } from "@/components/evidence/evidence-metadata-view";
import type { SourceCitation } from "@/types/api";

interface EvidenceCardProps {
  source: SourceCitation;
  index: number;
}

export const EvidenceCard = memo(function EvidenceCard({
  source,
  index,
}: EvidenceCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyExcerpt = async () => {
    try {
      await navigator.clipboard.writeText(source.excerpt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore copy error
    }
  };

  const scoreLabel =
    source.score !== null && source.score !== undefined
      ? `${(source.score * 100).toFixed(1)}% Rerank Score`
      : null;

  return (
    <div className="space-y-4">
      {/* Primary Card */}
      <div className="rounded-xl border border-border-default bg-surface-raised p-4 shadow-sm space-y-3.5">
        {/* Card Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-subtle text-accent">
              <FileText size={16} />
            </div>
            <div className="min-w-0">
              <h3 className="truncate text-sm font-semibold text-text-primary" title={source.source_name}>
                {source.source_name}
              </h3>
              <div className="flex items-center gap-2 mt-0.5 text-xs text-text-tertiary">
                <span>Evidence #{index + 1}</span>
                {source.page !== null && source.page !== undefined && (
                  <>
                    <span>•</span>
                    <span className="font-medium text-text-secondary">
                      Page {source.page}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Reranker Relevance Badge */}
          {scoreLabel && (
            <span className="shrink-0 rounded-full border border-accent/30 bg-accent-subtle px-2.5 py-1 text-xs font-semibold text-accent flex items-center gap-1">
              <Sparkles size={12} />
              {scoreLabel}
            </span>
          )}
        </div>

        {/* Excerpt Section */}
        <div className="relative rounded-lg border border-border-subtle bg-surface-base p-3.5">
          <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-border-subtle/50 text-[11px] font-semibold text-text-tertiary">
            <span className="uppercase tracking-wider">Grounded Excerpt</span>
            <button
              onClick={handleCopyExcerpt}
              aria-label="Copy excerpt text"
              className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none"
            >
              {copied ? (
                <>
                  <Check size={12} className="text-success" />
                  <span className="text-success">Copied</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <p className="select-text whitespace-pre-wrap font-sans text-xs leading-relaxed text-text-primary">
            {source.excerpt}
          </p>
        </div>
      </div>

      {/* Progressive Disclosure: Technical Metadata */}
      <EvidenceMetadataView source={source} />
    </div>
  );
});
