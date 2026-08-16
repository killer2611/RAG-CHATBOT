"use client";

import { memo } from "react";
import { Loader2, CheckCircle2, AlertCircle, Clock, Hash } from "lucide-react";
import type { JobStatus } from "@/types/api";

interface EvalJobStatusCardProps {
  status: JobStatus;
  isPolling: boolean;
}

export const EvalJobStatusCard = memo(function EvalJobStatusCard({
  status,
  isPolling,
}: EvalJobStatusCardProps) {
  const isRunning = status.status === "running" || status.status === "queued";
  const isCompleted = status.status === "completed";
  const isFailed = status.status === "failed";

  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-2xl border border-border-default bg-surface-raised p-5 shadow-sm space-y-3.5"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRunning ? (
            <Loader2 size={18} className="animate-spin text-accent" />
          ) : isCompleted ? (
            <CheckCircle2 size={18} className="text-success" />
          ) : (
            <AlertCircle size={18} className="text-error" />
          )}
          <h3 className="text-sm font-semibold text-text-primary capitalize">
            Job Status: {status.status}
          </h3>
        </div>

        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
            isRunning
              ? "bg-accent-subtle text-accent"
              : isCompleted
              ? "bg-success/20 text-success"
              : "bg-error/20 text-error"
          }`}
        >
          {status.status}
        </span>
      </div>

      {/* Message */}
      <p className="text-xs text-text-secondary">
        {status.message ||
          (isRunning
            ? "Evaluating retrieval context and test cases against golden dataset…"
            : isCompleted
            ? "DeepEval execution completed successfully."
            : "Benchmark run failed.")}
      </p>

      {/* Error Details if Failed */}
      {isFailed && status.error && (
        <div className="rounded-lg border border-error/30 bg-error/10 p-3 text-xs text-error">
          <span className="font-semibold">Error: </span>
          <span>{status.error}</span>
        </div>
      )}

      {/* Metadata Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border-subtle/50 text-[11px] text-text-tertiary">
        <div className="flex items-center gap-1">
          <Hash size={12} />
          <span>Job ID:</span>
          <span className="font-mono text-text-secondary select-all">{status.job_id}</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            Started: {new Date(status.created_at).toLocaleTimeString()}
          </span>
          {isPolling && (
            <span className="text-accent font-medium animate-pulse">
              Live Polling (bounded backoff)…
            </span>
          )}
        </div>
      </div>
    </div>
  );
});
