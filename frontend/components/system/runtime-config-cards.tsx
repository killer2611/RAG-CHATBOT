"use client";

import { memo } from "react";
import { Cpu, Layers, ShieldAlert, Sliders } from "lucide-react";
import type { SystemInfoResponse } from "@/types/api";

interface RuntimeConfigCardsProps {
  systemInfo: SystemInfoResponse | null;
  isLoading: boolean;
}

export const RuntimeConfigCards = memo(function RuntimeConfigCards({
  systemInfo,
  isLoading,
}: RuntimeConfigCardsProps) {
  if (isLoading && !systemInfo) {
    return (
      <div className="grid gap-4 sm:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-44 rounded-2xl border border-border-subtle bg-surface-raised/40 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!systemInfo) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-2">
          <Sliders size={14} className="text-accent" /> Runtime Hyperparameters & Configuration
        </h3>
        <span className="text-xs text-text-tertiary font-mono">
          Environment: {systemInfo.environment}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {/* Model Infrastructure */}
        <div className="rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm space-y-3.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-primary border-b border-border-subtle pb-2.5">
            <Cpu size={15} className="text-accent" />
            <span>Model Infrastructure</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-text-tertiary">Chat Provider</span>
              <span className="font-semibold text-text-primary capitalize">
                {systemInfo.chat_provider}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Chat Model</span>
              <span className="font-mono text-text-primary text-[11px]">
                {systemInfo.chat_model}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Embedding Model</span>
              <span className="font-mono text-text-primary text-[11px]">
                {systemInfo.embedding_model}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Cross-Encoder</span>
              <span className="font-mono text-text-primary text-[11px]">
                {systemInfo.reranker_model}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Eval Judge</span>
              <span className="font-semibold text-text-primary capitalize">
                {systemInfo.eval_judge}
              </span>
            </div>
          </div>
        </div>

        {/* Hierarchical Retrieval */}
        <div className="rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm space-y-3.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-primary border-b border-border-subtle pb-2.5">
            <Layers size={15} className="text-accent" />
            <span>Hierarchical Chunking</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-text-tertiary">Parent Chunk Size</span>
              <span className="font-mono font-semibold text-text-primary">
                {systemInfo.parent_chunk_size} tokens
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Parent Overlap</span>
              <span className="font-mono text-text-primary">
                {systemInfo.parent_chunk_overlap} tokens
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Child Chunk Size</span>
              <span className="font-mono font-semibold text-text-primary">
                {systemInfo.child_chunk_size} tokens
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Child Overlap</span>
              <span className="font-mono text-text-primary">
                {systemInfo.child_chunk_overlap} tokens
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Retrieval Dense k</span>
              <span className="font-mono font-semibold text-accent">
                {systemInfo.retrieval_k} candidates
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Rerank Top-N</span>
              <span className="font-mono font-semibold text-success">
                {systemInfo.rerank_top_n} chunks
              </span>
            </div>
          </div>
        </div>

        {/* Constraints & Governance */}
        <div className="rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm space-y-3.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-primary border-b border-border-subtle pb-2.5">
            <ShieldAlert size={15} className="text-accent" />
            <span>Limits & Governance</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-text-tertiary">Max Upload File</span>
              <span className="font-mono font-semibold text-text-primary">
                {systemInfo.max_upload_mb} MB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">History Sliding Window</span>
              <span className="font-mono text-text-primary">
                {systemInfo.history_max_messages} messages
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">DeepEval Pass Threshold</span>
              <span className="font-mono font-semibold text-accent">
                {systemInfo.eval_threshold.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Supported Document Types</span>
              <span className="font-semibold text-text-primary">
                PDF, TXT, DOCX
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Vector Database</span>
              <span className="font-semibold text-text-primary">
                Chroma DB (Persistent)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});
