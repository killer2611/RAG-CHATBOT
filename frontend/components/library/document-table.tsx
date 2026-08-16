"use client";

import { memo } from "react";
import { FileText, FileCode, CheckCircle2, Inbox } from "lucide-react";
import type { DocumentSummary } from "@/types/api";

interface DocumentTableProps {
  documents: DocumentSummary[];
  isLoading: boolean;
  onSelectDocument: (doc: DocumentSummary) => void;
}

function getFormatIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf" || ext === "docx") return <FileText size={16} className="text-accent" />;
  return <FileCode size={16} className="text-accent" />;
}

export const DocumentTable = memo(function DocumentTable({
  documents,
  isLoading,
  onSelectDocument,
}: DocumentTableProps) {
  if (isLoading && documents.length === 0) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-raised/40 p-8 text-center text-xs text-text-tertiary">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto mb-2" />
        Loading indexed documents…
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border border-border-subtle bg-surface-raised/30 p-12 text-center text-xs text-text-tertiary">
        <Inbox size={32} className="mx-auto mb-3 opacity-30 text-text-secondary" />
        <h4 className="text-sm font-semibold text-text-primary">No Documents in Library</h4>
        <p className="mt-1 max-w-sm mx-auto text-text-secondary">
          Upload PDF, TXT, or DOCX files using the dropzone above to begin indexing knowledge for retrieval.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border-subtle bg-surface-raised">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          {/* Table Header */}
          <thead className="border-b border-border-subtle bg-surface-base/60 text-text-tertiary">
            <tr>
              <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                Document
              </th>
              <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                Format
              </th>
              <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                Parent Chunks
              </th>
              <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                Child Chunks
              </th>
              <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[11px]">
                Status
              </th>
              <th className="py-3 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">
                Action
              </th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-border-subtle/50">
            {documents.map((doc) => {
              const ext = doc.source_name.split(".").pop()?.toUpperCase() || "DOC";

              return (
                <tr
                  key={doc.source_id}
                  className="transition-colors hover:bg-surface-elevated/40 group"
                >
                  {/* Document Name */}
                  <td className="py-3.5 px-4 font-medium text-text-primary">
                    <div className="flex items-center gap-2.5 min-w-0 max-w-xs sm:max-w-md">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-base border border-border-subtle">
                        {getFormatIcon(doc.source_name)}
                      </div>
                      <span className="truncate" title={doc.source_name}>
                        {doc.source_name}
                      </span>
                    </div>
                  </td>

                  {/* Format */}
                  <td className="py-3.5 px-4 text-text-secondary">
                    <span className="rounded bg-surface-base px-2 py-0.5 text-[10px] font-semibold border border-border-subtle">
                      {ext}
                    </span>
                  </td>

                  {/* Parent Chunks */}
                  <td className="py-3.5 px-4 text-text-secondary">
                    <span className="font-semibold text-text-primary">
                      {doc.parents}
                    </span>
                    <span className="text-[10px] text-text-tertiary ml-1">
                      (800-tok)
                    </span>
                  </td>

                  {/* Child Chunks */}
                  <td className="py-3.5 px-4 text-text-secondary">
                    <span className="font-semibold text-text-primary">
                      {doc.children ?? `${doc.parents * 4}*`}
                    </span>
                    <span className="text-[10px] text-text-tertiary ml-1">
                      (300-tok)
                    </span>
                  </td>

                  {/* Status */}
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-success/15 px-2.5 py-0.5 text-[10px] font-medium text-success">
                      <CheckCircle2 size={11} />
                      Indexed
                    </span>
                  </td>

                  {/* Action */}
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => onSelectDocument(doc)}
                      aria-label={`View details for ${doc.source_name}`}
                      className="rounded-lg border border-border-subtle bg-surface-base px-2.5 py-1 text-xs font-medium text-text-secondary transition-colors hover:border-border-default hover:text-text-primary"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
});
