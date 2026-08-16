"use client";

import { memo } from "react";
import Link from "next/link";
import {
  MessageSquare,
  BookOpen,
  Gauge,
  Terminal,
  ShieldCheck,
  Layers,
  Sparkles,
  ArrowRight,
  Sliders,
  CheckCircle2,
} from "lucide-react";

export const HomeWorkspace = memo(function HomeWorkspace() {
  return (
    <div className="min-h-screen bg-surface-base px-4 py-10 sm:px-8 max-w-6xl mx-auto space-y-12">
      {/* ── Hero Section ── */}
      <section className="text-center space-y-5 max-w-3xl mx-auto pt-4 sm:pt-8" aria-label="Platform Introduction">
        <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-subtle/50 px-3.5 py-1 text-xs font-semibold text-accent shadow-xs">
          <Sparkles size={14} className="text-accent" />
          <span>Production-Grade Conversational Intelligence</span>
        </div>

        <h1 className="text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl lg:text-5xl leading-[1.15]">
          Evidence-Grounded RAG Knowledge Platform
        </h1>

        <p className="text-sm leading-relaxed text-text-secondary sm:text-base max-w-2xl mx-auto">
          An enterprise knowledge engine pairing hierarchical chunk retrieval and cross-encoder reranking with strict factual grounding and automated DeepEval quality benchmarks.
        </p>

        {/* Hero CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link
            href="/chat"
            className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-xs font-semibold text-text-inverse transition-all duration-[var(--transition-fast)] hover:bg-accent-hover shadow-sm hover:shadow-md active:scale-[0.99]"
          >
            <MessageSquare size={16} />
            <span>Open Chat Workspace</span>
            <ArrowRight size={14} />
          </Link>

          <Link
            href="/library"
            className="flex items-center gap-2 rounded-xl border border-border-subtle bg-surface-raised px-4 py-2.5 text-xs font-semibold text-text-primary transition-all duration-[var(--transition-fast)] hover:border-border-default hover:bg-surface-elevated active:scale-[0.99]"
          >
            <BookOpen size={16} className="text-accent" />
            <span>Manage Document Library</span>
          </Link>
        </div>
      </section>

      {/* ── 4 Core Capabilities Grid ── */}
      <section aria-label="Core Capabilities" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Pillar 1: Conversational Chat */}
        <Link
          href="/chat"
          className="group rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm transition-all duration-[var(--transition-normal)] hover:border-border-default hover:bg-surface-elevated hover:shadow-md flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-subtle text-accent group-hover:scale-105 transition-transform duration-[var(--transition-fast)]">
              <MessageSquare size={20} />
            </div>
            <h2 className="text-sm font-bold text-text-primary group-hover:text-accent transition-colors duration-[var(--transition-fast)]">
              Conversational Chat
            </h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Token-by-token streaming with history-aware question reformulation and verifiable multi-turn session persistence.
            </p>
          </div>
          <div className="mt-5 flex items-center gap-1 text-xs font-medium text-accent">
            <span>Launch Chat</span>
            <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform duration-[var(--transition-fast)]" />
          </div>
        </Link>

        {/* Pillar 2: Knowledge Library */}
        <Link
          href="/library"
          className="group rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm transition-all duration-[var(--transition-normal)] hover:border-border-default hover:bg-surface-elevated hover:shadow-md flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-subtle text-accent group-hover:scale-105 transition-transform duration-[var(--transition-fast)]">
              <BookOpen size={20} />
            </div>
            <h2 className="text-sm font-bold text-text-primary group-hover:text-accent transition-colors duration-[var(--transition-fast)]">
              Knowledge Library
            </h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Drag-and-drop ingestion for PDF, TXT, and DOCX files with automated 800/300-token hierarchical chunking.
            </p>
          </div>
          <div className="mt-5 flex items-center gap-1 text-xs font-medium text-accent">
            <span>Explore Library</span>
            <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform duration-[var(--transition-fast)]" />
          </div>
        </Link>

        {/* Pillar 3: Evaluation Lab */}
        <Link
          href="/evaluate"
          className="group rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm transition-all duration-[var(--transition-normal)] hover:border-border-default hover:bg-surface-elevated hover:shadow-md flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-subtle text-accent group-hover:scale-105 transition-transform duration-[var(--transition-fast)]">
              <Gauge size={20} />
            </div>
            <h2 className="text-sm font-bold text-text-primary group-hover:text-accent transition-colors duration-[var(--transition-fast)]">
              Evaluation Lab
            </h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Asynchronous DeepEval test suites benchmarking Faithfulness, Answer Relevancy, Precision, and Recall.
            </p>
          </div>
          <div className="mt-5 flex items-center gap-1 text-xs font-medium text-accent">
            <span>Run Benchmarks</span>
            <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform duration-[var(--transition-fast)]" />
          </div>
        </Link>

        {/* Pillar 4: System Observability */}
        <Link
          href="/system"
          className="group rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-sm transition-all duration-[var(--transition-normal)] hover:border-border-default hover:bg-surface-elevated hover:shadow-md flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-subtle text-accent group-hover:scale-105 transition-transform duration-[var(--transition-fast)]">
              <Terminal size={20} />
            </div>
            <h2 className="text-sm font-bold text-text-primary group-hover:text-accent transition-colors duration-[var(--transition-fast)]">
              System Topology
            </h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Live FastAPI service health monitoring, verified hyperparameters, and 7-stage pipeline architecture visualization.
            </p>
          </div>
          <div className="mt-5 flex items-center gap-1 text-xs font-medium text-accent">
            <span>View Architecture</span>
            <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform duration-[var(--transition-fast)]" />
          </div>
        </Link>
      </section>

      {/* ── Architectural Guarantees ── */}
      <section aria-label="Architectural Guarantees" className="rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary flex items-center gap-2">
            <ShieldCheck size={14} className="text-success" />
            Core Engineering Guarantees
          </h2>
          <span className="text-[11px] text-text-tertiary">Verified by Automated Tests</span>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 text-xs">
          <div className="space-y-1.5 p-4 rounded-xl bg-surface-base border border-border-subtle">
            <div className="flex items-center gap-2 font-semibold text-text-primary">
              <Layers size={15} className="text-accent" />
              <span>Hierarchical Chunking</span>
            </div>
            <p className="text-text-secondary leading-relaxed">
              Decouples small 300-token dense retrieval units from 800-token parent contextual units for clean vector matching and rich synthesis context.
            </p>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-surface-base border border-border-subtle">
            <div className="flex items-center gap-2 font-semibold text-text-primary">
              <Sliders size={15} className="text-accent" />
              <span>Cross-Encoder Reranking</span>
            </div>
            <p className="text-text-secondary leading-relaxed">
              Evaluates top-10 candidate chunks with <code className="font-mono text-[11px] text-accent">BAAI/bge-reranker-base</code> to filter down to the top-3 most relevant passages.
            </p>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-surface-base border border-border-subtle">
            <div className="flex items-center gap-2 font-semibold text-text-primary">
              <CheckCircle2 size={15} className="text-success" />
              <span>Strict Factual Grounding</span>
            </div>
            <p className="text-text-secondary leading-relaxed">
              Zero-temperature inference with strict prompt constraints requiring the model to abstain if the retrieved context is insufficient.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
});
