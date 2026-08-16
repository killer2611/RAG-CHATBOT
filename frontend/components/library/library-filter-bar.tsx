"use client";

import { memo } from "react";
import { Search, X, Filter } from "lucide-react";

interface LibraryFilterBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedFormat: string;
  onFormatChange: (format: string) => void;
  totalCount: number;
  filteredCount: number;
}

const FORMAT_OPTIONS = [
  { label: "All Formats", value: "all" },
  { label: "PDF", value: "pdf" },
  { label: "TXT", value: "txt" },
  { label: "DOCX", value: "docx" },
];

export const LibraryFilterBar = memo(function LibraryFilterBar({
  searchQuery,
  onSearchChange,
  selectedFormat,
  onFormatChange,
  totalCount,
  filteredCount,
}: LibraryFilterBarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border-subtle pb-4">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Filter documents by filename or ID…"
          aria-label="Filter documents"
          className="w-full rounded-lg border border-border-subtle bg-surface-raised pl-9 pr-8 py-2 text-xs text-text-primary placeholder:text-text-tertiary transition-colors focus:border-accent focus:outline-none"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange("")}
            aria-label="Clear search"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-0.5 text-text-tertiary hover:text-text-primary focus-visible:outline-none"
          >
            <X size={13} />
          </button>
        )}
      </div>

      {/* Format Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto">
        <Filter size={13} className="text-text-tertiary shrink-0 mr-1" />
        {FORMAT_OPTIONS.map((opt) => {
          const isSelected = selectedFormat === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onFormatChange(opt.value)}
              className={`shrink-0 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                isSelected
                  ? "bg-accent text-text-inverse font-semibold shadow-sm"
                  : "bg-surface-raised border border-border-subtle text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
        <span className="ml-2 text-[11px] text-text-tertiary">
          {filteredCount} of {totalCount}
        </span>
      </div>
    </div>
  );
});
