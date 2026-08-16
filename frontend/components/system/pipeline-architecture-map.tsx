"use client";

import { memo, useState } from "react";
import {
  MessageSquare,
  Sparkles,
  Search,
  Layers,
  Sliders,
  Cpu,
  FileCheck,
  ChevronRight,
  Info,
} from "lucide-react";

interface PipelineStep {
  id: string;
  step: number;
  title: string;
  subtitle: string;
  description: string;
  technicalDetails: string;
  icon: React.ReactNode;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "query",
    step: 1,
    title: "User Query & History",
    subtitle: "Input Session Ingestion",
    description: "Accepts incoming user question alongside the last 10 turns from SQLite message history.",
    technicalDetails: "Session-serialized via asyncio.Lock to prevent race conditions during conversational multi-turn generation.",
    icon: <MessageSquare size={16} className="text-accent" />,
  },
  {
    id: "reformulation",
    step: 2,
    title: "History-Aware Reformulation",
    subtitle: "Contextual Query Rewrite",
    description: "Condenses prior conversation history into a standalone, context-independent search query.",
    technicalDetails: "Executed via fast chat LLM prompt template if prior conversation history exists.",
    icon: <Sparkles size={16} className="text-accent" />,
  },
  {
    id: "child_retrieval",
    step: 3,
    title: "Dense Child Retrieval",
    subtitle: "Chroma Vector Store",
    description: "Embeds search query and retrieves top k=10 focused child chunks (300 tokens) using cosine distance.",
    technicalDetails: "all-MiniLM-L6-v2 embeddings indexed in Chroma persistent vector database.",
    icon: <Search size={16} className="text-accent" />,
  },
  {
    id: "parent_expansion",
    step: 4,
    title: "Parent Chunk Expansion",
    subtitle: "SQLite ParentStore",
    description: "Resolves child chunk parent_id references into complete 800-token parent contextual windows.",
    technicalDetails: "Transactional SQLite table parents(parent_id, source_id, content, metadata_json).",
    icon: <Layers size={16} className="text-accent" />,
  },
  {
    id: "reranking",
    step: 5,
    title: "Cross-Encoder Reranking",
    subtitle: "BAAI/bge-reranker-base",
    description: "Re-scores (query, parent_content) pairs and selects the top N=3 most relevant chunks.",
    technicalDetails: "Cross-attention transformer computing direct relevance logits between query and full parent text.",
    icon: <Sliders size={16} className="text-accent" />,
  },
  {
    id: "grounded_synthesis",
    step: 6,
    title: "Grounded LLM Synthesis",
    subtitle: "Strict Abstention Prompt",
    description: "Synthesizes evidence-grounded answer. Strictly abstains if retrieved context is insufficient.",
    technicalDetails: "Temperature 0.0 with explicit system guardrails prohibiting external knowledge hallucination.",
    icon: <Cpu size={16} className="text-accent" />,
  },
  {
    id: "evidence_output",
    step: 7,
    title: "Answer & Source Citations",
    subtitle: "Evidence Inspector Ready",
    description: "Streams response tokens with verifiable source citations (document, page, score, excerpt).",
    technicalDetails: "POST /chat Server-Sent Events stream emitting discrete 'sources', 'token', and 'done' events.",
    icon: <FileCheck size={16} className="text-success" />,
  },
];

export const PipelineArchitectureMap = memo(function PipelineArchitectureMap() {
  const [selectedStep, setSelectedStep] = useState<PipelineStep>(PIPELINE_STEPS[0]);

  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-sm space-y-6">
      {/* Section Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between border-b border-border-subtle pb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            RAG Pipeline Architecture Map
          </h3>
          <p className="text-xs text-text-secondary">
            Verified 7-stage hierarchical retrieval & cross-encoder reranking workflow.
          </p>
        </div>
        <span className="text-[11px] font-mono text-text-tertiary">
          Static Architecture Specification
        </span>
      </div>

      {/* Visual Pipeline Flow */}
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7" role="list" aria-label="Pipeline Architecture Steps">
        {PIPELINE_STEPS.map((step) => {
          const isSelected = selectedStep.id === step.id;

          return (
            <button
              key={step.id}
              onClick={() => setSelectedStep(step)}
              className={`flex flex-col justify-between rounded-xl border p-3 text-left transition-all relative ${
                isSelected
                  ? "border-accent bg-surface-base shadow-sm ring-1 ring-accent"
                  : "border-border-subtle bg-surface-base/60 hover:border-border-default hover:bg-surface-base"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-elevated font-mono text-[10px] font-bold text-text-tertiary">
                    {step.step}
                  </span>
                  {step.icon}
                </div>
                <h4 className="text-xs font-semibold text-text-primary leading-tight">
                  {step.title}
                </h4>
                <p className="text-[10px] text-text-tertiary mt-0.5 truncate">
                  {step.subtitle}
                </p>
              </div>

              {step.step < 7 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-border-default pointer-events-none">
                  <ChevronRight size={14} />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Step Technical Details (Progressive Disclosure) */}
      <div className="rounded-xl border border-border-subtle bg-surface-base p-4 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
          <Info size={14} className="text-accent" />
          <span>
            Stage {selectedStep.step}: {selectedStep.title} — Technical Deep Dive
          </span>
        </div>
        <p className="text-xs leading-relaxed text-text-secondary">
          {selectedStep.description}
        </p>
        <div className="pt-2 border-t border-border-subtle/50 text-[11px] font-mono text-accent">
          <span className="font-semibold text-text-tertiary">Implementation: </span>
          {selectedStep.technicalDetails}
        </div>
      </div>
    </div>
  );
});
