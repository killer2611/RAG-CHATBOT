"use client";

import { memo } from "react";
import { Search, X } from "lucide-react";

interface EvidenceSearchProps {
  query: string;
  onQueryChange: (query: string) => void;
}

export const EvidenceSearch = memo(function EvidenceSearch({
  query,
  onQueryChange,
}: EvidenceSearchProps) {
  return (
    <div className="relative">
      <Search
        size={14}
        className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-tertiary"
      />
      <input
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="Filter evidence by keyword or filename…"
        aria-label="Filter evidence sources"
        className="w-full rounded-lg border border-border-subtle bg-surface-base pl-8 pr-8 py-1.5 text-xs text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none"
      />
      {query && (
        <button
          onClick={() => onQueryChange("")}
          aria-label="Clear filter"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-text-tertiary hover:text-text-primary focus-visible:outline-none"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
});
