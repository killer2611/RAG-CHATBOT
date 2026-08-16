"use client";

import { memo, useEffect } from "react";
import { X, FileText, Database, Layers, CheckCircle2 } from "lucide-react";
import type { DocumentSummary } from "@/types/api";

interface DocumentDetailModalProps {
  doc: DocumentSummary | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentDetailModal = memo(function DocumentDetailModal({
  doc,
  isOpen,
  onClose,
}: DocumentDetailModalProps) {
  // Lock body scroll and handle Escape key
  useEffect(() => {
    if (!isOpen) return;

    document.body.style.overflow = "hidden";
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !doc) return null;

  const ext = doc.source_name.split(".").pop()?.toUpperCase() || "DOC";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-labelledby="document-detail-title"
    >
      <div
        className="w-full max-w-lg rounded-2xl border border-border-default bg-surface-raised p-6 shadow-2xl space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-subtle text-accent">
              <FileText size={20} />
            </div>
            <div className="min-w-0">
              <h3
                id="document-detail-title"
                className="truncate text-base font-semibold text-text-primary"
                title={doc.source_name}
              >
                {doc.source_name}
              </h3>
              <div className="flex items-center gap-2 mt-0.5 text-xs text-text-tertiary">
                <span className="rounded bg-surface-elevated px-1.5 py-0.5 font-semibold text-text-secondary">
                  {ext}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1 text-success">
                  <CheckCircle2 size={12} /> Indexed in Knowledge Base
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close document details modal"
            className="rounded-lg p-1 text-text-tertiary hover:bg-surface-elevated hover:text-text-primary focus-visible:outline-none"
          >
            <X size={18} />
          </button>
        </div>

        {/* Hierarchical Chunk Structure Card */}
        <div className="rounded-xl border border-border-subtle bg-surface-base p-4 space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-1.5">
            <Layers size={13} className="text-accent" /> Hierarchical Chunking Architecture
          </h4>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-lg bg-surface-raised p-3 border border-border-subtle">
              <div className="text-[11px] text-text-tertiary">Parent Chunks</div>
              <div className="text-lg font-bold text-text-primary mt-0.5">
                {doc.parents}
              </div>
              <div className="text-[10px] text-text-secondary mt-1">
                Contextual units (~800 tokens) used for grounded LLM synthesis.
              </div>
            </div>

            <div className="rounded-lg bg-surface-raised p-3 border border-border-subtle">
              <div className="text-[11px] text-text-tertiary">Child Chunks</div>
              <div className="text-lg font-bold text-text-primary mt-0.5">
                {doc.children ?? `${doc.parents * 4} (est.)`}
              </div>
              <div className="text-[10px] text-text-secondary mt-1">
                Dense retrieval units (~300 tokens) indexed in vector database.
              </div>
            </div>
          </div>
        </div>

        {/* Source ID Digest */}
        <div className="space-y-1 text-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-1">
            <Database size={12} /> Source SHA-256 Digest
          </div>
          <div className="select-all break-all rounded-lg border border-border-subtle bg-surface-base p-2.5 font-mono text-[11px] text-text-primary">
            {doc.source_id}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="rounded-lg bg-surface-elevated px-4 py-2 text-xs font-medium text-text-primary hover:bg-surface-overlay"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
});
