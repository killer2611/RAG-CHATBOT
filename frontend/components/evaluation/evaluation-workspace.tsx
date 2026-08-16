"use client";

import { useCallback, useState } from "react";
import { Gauge } from "lucide-react";
import { EvalRunForm } from "@/components/evaluation/eval-run-form";
import { EvalJobStatusCard } from "@/components/evaluation/eval-job-status-card";
import { EvalMetricsOverview } from "@/components/evaluation/eval-metrics-overview";
import { EvalTestCasesTable } from "@/components/evaluation/eval-test-cases-table";
import { EvalCaseDetailModal } from "@/components/evaluation/eval-case-detail-modal";
import { useJobPoller } from "@/lib/hooks/use-job-poller";
import { postEvaluate, ApiError } from "@/lib/api/client";
import type { EvaluateRequest, TestCaseResult } from "@/types/api";

export function EvaluationWorkspace() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [selectedTestCase, setSelectedTestCase] = useState<{
    tc: TestCaseResult;
    index: number;
  } | null>(null);

  // Hook for bounded backoff polling of evaluation background job
  const {
    jobStatus,
    results,
    isPolling,
    error: pollError,
    startPolling,
  } = useJobPoller();

  const handleTriggerRun = useCallback(
    async (request: EvaluateRequest) => {
      setSubmitError(null);
      try {
        const job = await postEvaluate(request);
        startPolling(job.job_id);
      } catch (err) {
        setSubmitError(
          err instanceof ApiError
            ? err.detail
            : err instanceof Error
            ? err.message
            : "Failed to trigger benchmark evaluation job"
        );
      }
    },
    [startPolling]
  );

  const handleSelectCase = useCallback((tc: TestCaseResult, index: number) => {
    setSelectedTestCase({ tc, index });
  }, []);

  const isRunning = isPolling || (jobStatus?.status === "running" || jobStatus?.status === "queued");

  return (
    <div className="min-h-screen bg-surface-base px-4 py-8 sm:px-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 border-b border-border-subtle pb-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-subtle text-accent shadow-xs">
            <Gauge size={20} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
            Evaluation Lab & Benchmark Dashboard
          </h1>
        </div>
        <p className="text-xs text-text-secondary sm:text-sm">
          Run asynchronous DeepEval test suites to benchmark retrieval faithfulness, relevancy, and contextual precision.
        </p>
      </div>

      {/* Configuration & Run Trigger */}
      <section aria-label="Run Configuration">
        <EvalRunForm
          onSubmit={handleTriggerRun}
          isRunning={isRunning}
        />
        {submitError && (
          <div className="mt-3 rounded-xl border border-error/30 bg-error/10 p-3.5 text-xs text-error">
            <span className="font-semibold">Submission Error: </span>
            {submitError}
          </div>
        )}
      </section>

      {/* Active Job State */}
      {jobStatus && (
        <section aria-label="Job Status">
          <EvalJobStatusCard
            status={jobStatus}
            isPolling={isPolling}
          />
        </section>
      )}

      {/* Polling Error Alert */}
      {pollError && (
        <div className="rounded-xl border border-error/30 bg-error/10 p-4 text-xs text-error">
          <span className="font-semibold">Polling Error: </span>
          {pollError}
        </div>
      )}

      {/* Results Workspace */}
      {results && (
        <section className="space-y-6 pt-4 border-t border-border-subtle" aria-label="Benchmark Results">
          {/* Metrics Overview Cards */}
          <EvalMetricsOverview summary={results.summary} />

          {/* Test Cases Table */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
              Individual Test Case Evaluations ({results.test_cases.length})
            </h3>
            <EvalTestCasesTable
              testCases={results.test_cases}
              onSelectCase={handleSelectCase}
            />
          </div>
        </section>
      )}

      {/* Case Detail Modal */}
      <EvalCaseDetailModal
        testCase={selectedTestCase?.tc ?? null}
        index={selectedTestCase?.index ?? null}
        isOpen={Boolean(selectedTestCase)}
        onClose={() => setSelectedTestCase(null)}
      />
    </div>
  );
}
