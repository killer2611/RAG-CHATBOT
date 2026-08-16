"use client";

import { memo } from "react";
import { Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import type { IngestResponse } from "@/types/api";

export type IngestionPhase = "idle" | "uploading" | "processing" | "success" | "error";

interface IngestionStatusBannerProps {
  phase: IngestionPhase;
  fileName?: string;
  result?: IngestResponse | null;
  error?: string | null;
  onDismiss: () => void;
}

export const IngestionStatusBanner = memo(function IngestionStatusBanner({
  phase,
  fileName,
  result,
  error,
  onDismiss,
}: IngestionStatusBannerProps) {
  if (phase === "idle") return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="my-4 rounded-xl border p-4 shadow-sm transition-all"
    >
      {/* Uploading / Processing Indeterminate States */}
      {(phase === "uploading" || phase === "processing") && (
        <div className="flex items-start justify-between gap-3 border-accent/30 bg-accent-subtle/30 text-text-primary">
          <div className="flex items-start gap-3">
            <Loader2 size={18} className="mt-0.5 animate-spin text-accent shrink-0" />
            <div>
              <h4 className="text-xs font-semibold text-text-primary">
                {phase === "uploading"
                  ? `Uploading ${fileName || "document"}…`
                  : `Ingesting & Indexing ${fileName || "document"}…`}
              </h4>
              <p className="mt-1 text-xs leading-relaxed text-text-secondary">
                {phase === "uploading"
                  ? "Streaming file payload to FastAPI ingestion endpoint."
                  : "Performing hierarchical text chunking (parent: 800 tokens, child: 300 tokens) and updating Chroma vectorstore & SQLite ParentStore."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Success State */}
      {phase === "success" && result && (
        <div className="flex items-start justify-between gap-3 border-success/30 bg-success/10 text-text-primary">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={18} className="mt-0.5 text-success shrink-0" />
            <div>
              <h4 className="text-xs font-semibold text-text-primary flex items-center gap-2">
                <span>Successfully Ingested: {result.source_name}</span>
                <span className="rounded-full bg-success/20 px-2 py-0.5 text-[10px] font-semibold text-success uppercase">
                  {result.status}
                </span>
              </h4>
              <p className="mt-1 text-xs text-text-secondary">
                Created{" "}
                <span className="font-semibold text-text-primary">
                  {result.parents} parent chunks
                </span>{" "}
                and{" "}
                <span className="font-semibold text-text-primary">
                  {result.children} child retrieval units
                </span>
                . Document is now fully searchable in Chat.
              </p>
            </div>
          </div>

          <button
            onClick={onDismiss}
            aria-label="Dismiss ingestion success banner"
            className="rounded p-1 text-text-tertiary hover:bg-surface-elevated hover:text-text-primary"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Error State */}
      {phase === "error" && error && (
        <div className="flex items-start justify-between gap-3 border-error/30 bg-error/10 text-error">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="mt-0.5 text-error shrink-0" />
            <div>
              <h4 className="text-xs font-semibold">Ingestion Failed</h4>
              <p className="mt-1 text-xs text-text-secondary">{error}</p>
            </div>
          </div>

          <button
            onClick={onDismiss}
            aria-label="Dismiss ingestion error banner"
            className="rounded p-1 text-text-tertiary hover:bg-surface-elevated hover:text-text-primary"
          >
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
});
