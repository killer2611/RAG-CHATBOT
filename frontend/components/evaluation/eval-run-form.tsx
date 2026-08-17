"use client";

import { memo, useState } from "react";
import { Play, Settings2, Database, Cpu } from "lucide-react";
import type { EvaluateRequest } from "@/types/api";

interface EvalRunFormProps {
  onSubmit: (request: EvaluateRequest) => Promise<void>;
  isRunning: boolean;
  disabled?: boolean;
}

export const EvalRunForm = memo(function EvalRunForm({
  onSubmit,
  isRunning,
  disabled = false,
}: EvalRunFormProps) {
  const [judge, setJudge] = useState<"deepseek" | "sambanova">("deepseek");
  const [testFile, setTestFile] = useState<string>("data/golden_qa.json");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const trimmedPath = testFile.trim();
    if (trimmedPath && !trimmedPath.startsWith("data/")) {
      setValidationError("Test dataset path must be under data/ directory (e.g. data/golden_qa.json).");
      return;
    }

    await onSubmit({
      judge,
      test_file: trimmedPath || undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm space-y-4"
    >
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <Settings2 size={16} className="text-accent" />
          <h3 className="text-sm font-semibold text-text-primary">
            Run Benchmark Configuration
          </h3>
        </div>
        <span className="text-[11px] text-text-tertiary">
          Engine: DeepEval Framework
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Judge Model Selector */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
            <Cpu size={13} className="text-accent" /> Evaluation Judge LLM
          </label>
          <select
            value={judge}
            onChange={(e) => setJudge(e.target.value as "deepseek" | "sambanova")}
            disabled={disabled || isRunning}
            aria-label="Evaluation judge LLM"
            className="w-full rounded-lg border border-border-subtle bg-surface-base px-3 py-2 text-xs text-text-primary focus:border-accent focus:outline-none disabled:opacity-50"
          >
            <option value="deepseek">DeepSeek V4 Flash (Primary / Cloud)</option>
            <option value="sambanova">SambaNova Llama 3.3 70B (Free / Cloud)</option>
          </select>
          <p className="text-[10px] text-text-tertiary">
            Cloud LLM used by DeepEval to evaluate faithfulness and contextual metrics. No local LLM is used.
          </p>
        </div>

        {/* Dataset Path Input */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
            <Database size={13} className="text-accent" /> Golden Dataset File
          </label>
          <input
            type="text"
            value={testFile}
            onChange={(e) => setTestFile(e.target.value)}
            placeholder="data/golden_qa.json"
            disabled={disabled || isRunning}
            aria-label="Golden test dataset file path"
            className="w-full rounded-lg border border-border-subtle bg-surface-base px-3 py-2 text-xs text-text-primary focus:border-accent focus:outline-none disabled:opacity-50"
          />
          <p className="text-[10px] text-text-tertiary">
            Must reside under <code className="rounded bg-surface-elevated px-1 text-accent">data/</code> directory.
          </p>
        </div>
      </div>

      {/* Validation Alert */}
      {validationError && (
        <div className="rounded-lg border border-error/30 bg-error/10 p-2.5 text-xs text-error">
          {validationError}
        </div>
      )}

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-border-subtle/60">
        <div className="text-[11px] text-text-tertiary">
          Metrics: Faithfulness, Answer Relevancy, Contextual Precision, Contextual Recall
        </div>

        <button
          type="submit"
          disabled={disabled || isRunning}
          className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-text-inverse transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40 shadow-sm"
        >
          <Play size={14} className={isRunning ? "animate-spin" : ""} />
          <span>{isRunning ? "Evaluation Running…" : "Trigger Benchmark Run"}</span>
        </button>
      </div>
    </form>
  );
});
