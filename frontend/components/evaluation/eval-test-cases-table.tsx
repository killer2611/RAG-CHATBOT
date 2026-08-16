"use client";

import { memo, useState, useMemo } from "react";
import { CheckCircle2, XCircle, Search, Filter } from "lucide-react";
import type { TestCaseResult } from "@/types/api";

interface EvalTestCasesTableProps {
  testCases: TestCaseResult[];
  onSelectCase: (testCase: TestCaseResult, index: number) => void;
}

export const EvalTestCasesTable = memo(function EvalTestCasesTable({
  testCases,
  onSelectCase,
}: EvalTestCasesTableProps) {
  const [filterStatus, setFilterStatus] = useState<"all" | "passed" | "failed">("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredCases = useMemo(() => {
    return testCases.map((tc, originalIndex) => ({ tc, originalIndex })).filter(({ tc }) => {
      if (filterStatus === "passed" && !tc.success) return false;
      if (filterStatus === "failed" && tc.success) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesQ = tc.question.toLowerCase().includes(q);
        const matchesActual = tc.actual_output?.toLowerCase().includes(q) ?? false;
        if (!matchesQ && !matchesActual) return false;
      }
      return true;
    });
  }, [testCases, filterStatus, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Table Filter Controls */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search test case questions…"
            aria-label="Search test case questions"
            className="w-full rounded-lg border border-border-subtle bg-surface-raised pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5 text-xs">
          <Filter size={13} className="text-text-tertiary mr-1" />
          {(["all", "passed", "failed"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                filterStatus === st
                  ? "bg-accent text-text-inverse font-semibold shadow-sm"
                  : "bg-surface-raised border border-border-subtle text-text-secondary hover:text-text-primary"
              }`}
            >
              {st}
            </button>
          ))}
          <span className="ml-2 text-[11px] text-text-tertiary">
            {filteredCases.length} of {testCases.length}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-surface-raised">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="border-b border-border-subtle bg-surface-base/60 text-text-tertiary">
              <tr>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px] w-16">
                  Case
                </th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px] w-24">
                  Status
                </th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                  Evaluation Query / Question
                </th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                  Scores Breakdown
                </th>
                <th className="py-3 px-4 text-right font-semibold uppercase tracking-wider text-[11px] w-24">
                  Action
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border-subtle/50">
              {filteredCases.map(({ tc, originalIndex }) => (
                <tr
                  key={originalIndex}
                  className="transition-colors hover:bg-surface-elevated/40"
                >
                  <td className="py-3 px-4 font-mono font-semibold text-text-secondary">
                    #{originalIndex + 1}
                  </td>

                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        tc.success
                          ? "bg-success/15 text-success"
                          : "bg-error/15 text-error"
                      }`}
                    >
                      {tc.success ? (
                        <CheckCircle2 size={11} />
                      ) : (
                        <XCircle size={11} />
                      )}
                      {tc.success ? "Pass" : "Fail"}
                    </span>
                  </td>

                  <td className="py-3 px-4 font-medium text-text-primary max-w-xs sm:max-w-md truncate" title={tc.question}>
                    {tc.question}
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {Object.entries(tc.metrics).map(([mName, mDetail]) => {
                        if (mDetail.score === null || mDetail.score === undefined) return null;
                        const percent = (mDetail.score * 100).toFixed(0);
                        const isPass = mDetail.passed ?? mDetail.score >= 0.7;

                        return (
                          <span
                            key={mName}
                            title={`${mName}: ${percent}%`}
                            className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-medium ${
                              isPass
                                ? "bg-surface-base text-text-secondary border border-border-subtle"
                                : "bg-error/10 text-error border border-error/20"
                            }`}
                          >
                            {mName.slice(0, 4)}: {percent}%
                          </span>
                        );
                      })}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectCase(tc, originalIndex)}
                      aria-label={`Inspect case #${originalIndex + 1}`}
                      className="rounded-lg border border-border-subtle bg-surface-base px-2.5 py-1 text-xs font-medium text-text-secondary hover:border-border-default hover:text-text-primary"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
});
