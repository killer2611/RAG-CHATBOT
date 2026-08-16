"use client";

import { memo, useState, useEffect, useMemo, useCallback } from "react";
import { X, ShieldCheck, FileQuestion } from "lucide-react";
import { EvidenceCard } from "@/components/evidence/evidence-card";
import { EvidenceSourceNav } from "@/components/evidence/evidence-source-nav";
import { EvidenceSearch } from "@/components/evidence/evidence-search";
import type { SourceCitation } from "@/types/api";

interface EvidenceInspectorProps {
  sources: SourceCitation[] | null;
  initialIndex?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceInspector = memo(function EvidenceInspector({
  sources,
  initialIndex = 0,
  isOpen,
  onClose,
}: EvidenceInspectorProps) {
  const [selectedIndex, setSelectedIndex] = useState<number>(initialIndex);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Sync selected index when initialIndex changes or inspector opens
  useEffect(() => {
    setSelectedIndex(initialIndex);
    setSearchQuery("");
  }, [initialIndex, isOpen]);

  // Handle Escape key and mobile scroll lock
  useEffect(() => {
    if (!isOpen) return;

    // Lock scroll on mobile screens only
    const isMobile = window.innerWidth < 1024;
    if (isMobile) {
      document.body.style.overflow = "hidden";
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Filter sources based on query
  const filteredSources = useMemo(() => {
    if (!sources) return [];
    if (!searchQuery.trim()) return sources;
    const q = searchQuery.toLowerCase();
    return sources.filter(
      (s) =>
        s.source_name.toLowerCase().includes(q) ||
        s.excerpt.toLowerCase().includes(q) ||
        (s.page !== null && s.page !== undefined && `page ${s.page}`.includes(q))
    );
  }, [sources, searchQuery]);

  const activeSource = filteredSources[selectedIndex] ?? filteredSources[0];

  const handleSelect = useCallback((idx: number) => {
    setSelectedIndex(idx);
  }, []);

  if (!isOpen || !sources || sources.length === 0) return null;

  return (
    <>
      {/* Mobile Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-out Panel (Desktop Right Panel / Mobile Bottom Sheet) */}
      <aside
        className={`fixed z-50 flex flex-col border-border-subtle bg-surface-raised shadow-2xl transition-transform duration-[var(--transition-normal)]
          /* Mobile: Bottom Sheet */
          bottom-0 left-0 right-0 max-h-[85vh] rounded-t-2xl border-t
          /* Desktop: Right Slide-out Drawer */
          lg:top-0 lg:bottom-0 lg:left-auto lg:right-0 lg:w-[440px] lg:max-h-none lg:rounded-none lg:border-l lg:border-t-0
          ${isOpen ? "translate-y-0 lg:translate-x-0" : "translate-y-full lg:translate-x-full"}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="Evidence Inspector"
      >
        {/* Mobile Drag Indicator Bar */}
        <div className="mx-auto mt-2.5 h-1 w-10 shrink-0 rounded-full bg-border-default lg:hidden" aria-hidden="true" />

        {/* Header */}
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border-subtle px-5">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-accent" />
            <h2 className="text-sm font-semibold tracking-tight text-text-primary">
              Evidence Inspector
            </h2>
            <span className="rounded-full bg-surface-elevated px-2 py-0.5 text-[11px] font-semibold text-text-tertiary">
              {sources.length} {sources.length === 1 ? "source" : "sources"}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close evidence inspector"
            className="rounded-lg p-1.5 text-text-tertiary hover:bg-surface-overlay hover:text-text-primary transition-colors focus-visible:outline-none"
          >
            <X size={18} />
          </button>
        </div>

        {/* Subheader / Grounding Context */}
        <div className="border-b border-border-subtle/60 bg-surface-base/80 px-5 py-2.5 text-[11px] leading-relaxed text-text-tertiary">
          This answer was formulated from the retrieved knowledge chunks below.
        </div>

        {/* Controls: Search & Source Navigation */}
        <div className="border-b border-border-subtle p-3.5 space-y-2.5 bg-surface-raised">
          {sources.length > 1 && (
            <EvidenceSearch
              query={searchQuery}
              onQueryChange={setSearchQuery}
            />
          )}

          <EvidenceSourceNav
            sources={filteredSources}
            selectedIndex={selectedIndex}
            onSelect={handleSelect}
          />
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeSource ? (
            <EvidenceCard
              source={activeSource}
              index={selectedIndex}
            />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center text-xs text-text-tertiary">
              <FileQuestion size={28} className="mb-2 opacity-40" />
              <p>No evidence matching &quot;{searchQuery}&quot;</p>
              <button
                onClick={() => setSearchQuery("")}
                className="mt-2 text-accent underline hover:text-accent-hover"
              >
                Clear filter
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border-subtle bg-surface-base px-5 py-3 text-right">
          <button
            onClick={onClose}
            className="rounded-lg bg-surface-elevated px-4 py-1.5 text-xs font-medium text-text-primary hover:bg-surface-overlay transition-colors focus-visible:outline-none"
          >
            Close Inspector
          </button>
        </div>
      </aside>
    </>
  );
});
