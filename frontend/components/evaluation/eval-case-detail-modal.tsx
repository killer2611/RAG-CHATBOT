"use client";

import { memo, useEffect } from "react";
import { X, CheckCircle2, XCircle, HelpCircle, Sparkles, Target, AlertTriangle } from "lucide-react";
import type { TestCaseResult } from "@/types/api";

interface EvalCaseDetailModalProps {
  testCase: TestCaseResult | null;
  index: number | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EvalCaseDetailModal = memo(function EvalCaseDetailModal({
  testCase,
  index,
  isOpen,
  onClose,
}: EvalCaseDetailModalProps) {
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

  if (!isOpen || !testCase) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-labelledby="case-detail-title"
    >
      <div
        className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl border border-border-default bg-surface-raised shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border-subtle px-6 bg-surface-raised">
          <div className="flex items-center gap-2.5 min-w-0">
            {testCase.success ? (
              <CheckCircle2 size={18} className="text-success shrink-0" />
            ) : (
              <XCircle size={18} className="text-error shrink-0" />
            )}
            <h3 id="case-detail-title" className="text-sm font-semibold text-text-primary truncate">
              Test Case #{typeof index === "number" ? index + 1 : ""} Details
            </h3>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                testCase.success
                  ? "bg-success/20 text-success"
                  : "bg-error/20 text-error"
              }`}
            >
              {testCase.success ? "Passed" : "Failed"}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close test case details"
            className="rounded-lg p-1.5 text-text-tertiary hover:bg-surface-elevated hover:text-text-primary focus-visible:outline-none"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Question / Input */}
          <div className="space-y-1.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-1.5">
              <HelpCircle size={13} className="text-accent" /> Evaluation Input Query
            </h4>
            <div className="rounded-xl border border-border-subtle bg-surface-base p-3 text-xs leading-relaxed text-text-primary">
              {testCase.question}
            </div>
          </div>

          {/* Expected vs Actual Outputs */}
          <div className="grid gap-4 sm:grid-cols-2 text-xs">
            {/* Golden Reference */}
            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Expected Output (Golden Reference)
              </h4>
              <div className="rounded-xl border border-border-subtle bg-surface-base p-3 text-xs leading-relaxed text-text-secondary min-h-[80px]">
                {testCase.expected_output || (
                  <span className="italic text-text-tertiary">No reference text provided</span>
                )}
              </div>
            </div>

            {/* Actual Output */}
            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Actual RAG System Output
              </h4>
              <div className="rounded-xl border border-border-subtle bg-surface-base p-3 text-xs leading-relaxed text-text-primary min-h-[80px]">
                {testCase.actual_output || (
                  <span className="italic text-text-tertiary">No output recorded</span>
                )}
              </div>
            </div>
          </div>

          {/* DeepEval Metric Breakdown */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-1.5">
              <Sparkles size={13} className="text-accent" /> DeepEval Metric Breakdown
            </h4>

            <div className="space-y-2">
              {Object.entries(testCase.metrics).map(([metricName, detail]) => {
                const isPassed =
                  detail.passed ??
                  (detail.score !== null &&
                    detail.score !== undefined &&
                    detail.score >= 0.7);
                const scorePercent =
                  detail.score !== null && detail.score !== undefined
                    ? `${(detail.score * 100).toFixed(1)}%`
                    : "N/A";

                return (
                  <div
                    key={metricName}
                    className="rounded-xl border border-border-subtle bg-surface-base p-3.5 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Target size={14} className="text-accent" />
                        <span className="text-xs font-semibold text-text-primary">
                          {detail.name || metricName}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-text-primary">
                          {scorePercent}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                            isPassed
                              ? "bg-success/20 text-success"
                              : "bg-error/20 text-error"
                          }`}
                        >
                          {isPassed ? "Pass" : "Fail"}
                        </span>
                      </div>
                    </div>

                    {/* Metric Reasoning */}
                    {detail.reason && (
                      <p className="text-xs text-text-secondary leading-relaxed border-t border-border-subtle/50 pt-2">
                        <span className="font-medium text-text-primary">Reasoning: </span>
                        {detail.reason}
                      </p>
                    )}

                    {/* Metric Error if present */}
                    {detail.error && (
                      <div className="flex items-center gap-1 text-[11px] text-error">
                        <AlertTriangle size={12} />
                        <span>{detail.error}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-border-subtle bg-surface-raised px-6 py-3">
          <button
            onClick={onClose}
            className="rounded-lg bg-surface-elevated px-4 py-1.5 text-xs font-medium text-text-primary hover:bg-surface-overlay"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
});
