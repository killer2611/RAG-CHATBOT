"use client";

import { memo } from "react";
import { CheckCircle2, Target, Sparkles } from "lucide-react";
import type { EvaluationSummary } from "@/types/api";

interface EvalMetricsOverviewProps {
  summary: EvaluationSummary;
}

const METRIC_DESCRIPTIONS: Record<string, string> = {
  Faithfulness: "Measures whether the answer is factually grounded in retrieved chunks without hallucination.",
  "Answer Relevancy": "Measures whether the generated answer directly addresses the query.",
  "Contextual Precision": "Measures whether relevant context was ranked at top retrieval positions.",
  "Contextual Recall": "Measures whether all information needed to answer the query was retrieved.",
};

export const EvalMetricsOverview = memo(function EvalMetricsOverview({
  summary,
}: EvalMetricsOverviewProps) {
  const passRate =
    summary.total_cases > 0
      ? (summary.passed_cases / summary.total_cases) * 100
      : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-2">
          <Sparkles size={14} className="text-accent" /> Benchmark Summary Metrics
        </h3>
        <span className="text-xs text-text-tertiary">
          Total Cases Evaluated: {summary.total_cases}
        </span>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {/* Pass Rate Card */}
        <div className="rounded-xl border border-border-subtle bg-surface-raised p-4 space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium">Test Case Pass Rate</span>
            <CheckCircle2 size={15} className="text-success" />
          </div>
          <div className="text-2xl font-bold text-text-primary">
            {passRate.toFixed(1)}%
          </div>
          <div className="text-[11px] text-text-secondary">
            {summary.passed_cases} passed of {summary.total_cases} test cases
          </div>
        </div>

        {/* Dynamic Metric Cards from backend average_scores */}
        {Object.entries(summary.average_scores).map(([metricName, avgScore]) => {
          const scorePercent = (avgScore * 100).toFixed(1);
          const description =
            METRIC_DESCRIPTIONS[metricName] || "DeepEval evaluation metric score.";

          return (
            <div
              key={metricName}
              className="rounded-xl border border-border-subtle bg-surface-raised p-4 space-y-2"
            >
              <div className="flex items-center justify-between text-text-tertiary">
                <span className="text-xs font-medium truncate" title={metricName}>
                  {metricName}
                </span>
                <Target size={14} className="text-accent" />
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {scorePercent}%
              </div>
              <p className="text-[10px] text-text-tertiary line-clamp-2" title={description}>
                {description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
});
