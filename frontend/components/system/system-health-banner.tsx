"use client";

import { memo } from "react";
import { CheckCircle2, AlertCircle, RefreshCw, Server, Activity } from "lucide-react";
import type { HealthResponse } from "@/types/api";
import { config } from "@/lib/config";

interface SystemHealthBannerProps {
  health: HealthResponse | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: Date | null;
  onRefresh: () => void;
}

export const SystemHealthBanner = memo(function SystemHealthBanner({
  health,
  isLoading,
  error,
  lastChecked,
  onRefresh,
}: SystemHealthBannerProps) {
  const isHealthy = health?.status === "ok";

  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm space-y-4"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
              isHealthy
                ? "bg-success/15 text-success"
                : "bg-error/15 text-error"
            }`}
          >
            {isHealthy ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-text-primary">
                {isHealthy ? "FastAPI Core Services Operational" : "Backend Connection Degraded"}
              </h3>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  isHealthy
                    ? "bg-success/20 text-success"
                    : "bg-error/20 text-error"
                }`}
              >
                {isHealthy ? "Healthy" : "Offline"}
              </span>
            </div>
            <p className="text-xs text-text-secondary mt-0.5">
              {isHealthy
                ? "API router, Chroma DB, SQLite ParentStore, and LangChain chat history are active."
                : error || "Unable to reach FastAPI backend server at configured endpoint."}
            </p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          aria-label="Refresh backend health status"
          className="flex items-center gap-1.5 self-start rounded-lg border border-border-subtle bg-surface-base px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-border-default hover:text-text-primary disabled:opacity-50"
        >
          <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
          <span>Check Health</span>
        </button>
      </div>

      {/* Connection Meta */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle/50 text-[11px] text-text-tertiary">
        <div className="flex items-center gap-2">
          <Server size={12} />
          <span>API Endpoint:</span>
          <span className="font-mono text-text-secondary select-all">{config.apiBaseUrl}</span>
        </div>

        <div className="flex items-center gap-2">
          <Activity size={12} />
          <span>Last Verified:</span>
          <span className="font-mono text-text-secondary">
            {lastChecked ? lastChecked.toLocaleTimeString() : "Never"}
          </span>
        </div>
      </div>
    </div>
  );
});
