"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { RefreshCw, BookOpen, AlertCircle } from "lucide-react";
import { FileUploadDropzone } from "@/components/library/file-upload-dropzone";
import { IngestionStatusBanner, type IngestionPhase } from "@/components/library/ingestion-status-banner";
import { DocumentTable } from "@/components/library/document-table";
import { LibraryFilterBar } from "@/components/library/library-filter-bar";
import { DocumentDetailModal } from "@/components/library/document-detail-modal";
import { getDocuments, postIngest, ApiError } from "@/lib/api/client";
import type { DocumentSummary, IngestResponse } from "@/types/api";

export function LibraryWorkspace() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Ingestion State
  const [ingestPhase, setIngestPhase] = useState<IngestionPhase>("idle");
  const [uploadFileName, setUploadFileName] = useState<string>("");
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  // Filter & Search State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFormat, setSelectedFormat] = useState<string>("all");

  // Detail Modal State
  const [selectedDoc, setSelectedDoc] = useState<DocumentSummary | null>(null);

  // Fetch documents list from backend
  const fetchDocumentsList = useCallback(async () => {
    setIsLoadingDocs(true);
    setLoadError(null);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? err.detail
          : err instanceof Error
          ? err.message
          : "Failed to connect to documents endpoint"
      );
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    let isMounted = true;
    getDocuments()
      .then((data) => {
        if (isMounted) {
          setDocuments(data);
          setIsLoadingDocs(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setLoadError(
            err instanceof ApiError ? err.detail : "Unable to load document library"
          );
          setIsLoadingDocs(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Handle file ingestion
  const handleUpload = useCallback(
    async (file: File) => {
      setUploadFileName(file.name);
      setIngestPhase("uploading");
      setIngestError(null);
      setIngestResult(null);

      // Simulate step transition from upload to processing
      const processingTimer = setTimeout(() => {
        setIngestPhase("processing");
      }, 600);

      try {
        const response = await postIngest(file);
        clearTimeout(processingTimer);
        setIngestResult(response);
        setIngestPhase("success");

        // Immediately refresh documents list from authoritative backend
        await fetchDocumentsList();
      } catch (err) {
        clearTimeout(processingTimer);
        setIngestPhase("error");
        setIngestError(
          err instanceof ApiError
            ? err.detail
            : err instanceof Error
            ? err.message
            : "An unexpected error occurred during ingestion."
        );
      }
    },
    [fetchDocumentsList]
  );

  // Filtered documents
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Format Filter
      if (selectedFormat !== "all") {
        const ext = doc.source_name.split(".").pop()?.toLowerCase();
        if (ext !== selectedFormat.toLowerCase()) return false;
      }
      // Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = doc.source_name.toLowerCase().includes(q);
        const matchesId = doc.source_id.toLowerCase().includes(q);
        if (!matchesName && !matchesId) return false;
      }
      return true;
    });
  }, [documents, selectedFormat, searchQuery]);

  return (
    <div className="min-h-screen bg-surface-base px-4 py-8 sm:px-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border-subtle pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-subtle text-accent shadow-xs">
              <BookOpen size={20} />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
              Knowledge Library
            </h1>
          </div>
          <p className="mt-1 text-xs text-text-secondary sm:text-sm">
            Ingest and manage documents into the hierarchical vector index.
          </p>
        </div>

        <button
          onClick={fetchDocumentsList}
          disabled={isLoadingDocs}
          aria-label="Refresh documents list"
          className="flex items-center gap-1.5 self-start rounded-lg border border-border-subtle bg-surface-raised px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-border-default hover:text-text-primary disabled:opacity-50"
        >
          <RefreshCw size={13} className={isLoadingDocs ? "animate-spin" : ""} />
          <span>Refresh Library</span>
        </button>
      </div>

      {/* Upload Dropzone */}
      <section aria-label="Document Upload Area">
        <FileUploadDropzone
          onUpload={handleUpload}
          isIngesting={ingestPhase === "uploading" || ingestPhase === "processing"}
        />
      </section>

      {/* Ingestion Status Banner */}
      <IngestionStatusBanner
        phase={ingestPhase}
        fileName={uploadFileName}
        result={ingestResult}
        error={ingestError}
        onDismiss={() => setIngestPhase("idle")}
      />

      {/* Error State for Library Fetch */}
      {loadError && (
        <div className="flex items-center justify-between rounded-xl border border-error/30 bg-error/10 p-4 text-xs text-error">
          <div className="flex items-center gap-2.5">
            <AlertCircle size={16} />
            <div>
              <span className="font-semibold">Failed to load documents</span>
              <p className="mt-0.5 text-text-secondary">{loadError}</p>
            </div>
          </div>
          <button
            onClick={fetchDocumentsList}
            className="rounded bg-surface-elevated px-3 py-1 text-xs font-medium text-text-primary hover:bg-surface-overlay"
          >
            Retry
          </button>
        </div>
      )}

      {/* Library Filter & Document Table */}
      <section className="space-y-4" aria-label="Document Collection">
        <LibraryFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedFormat={selectedFormat}
          onFormatChange={setSelectedFormat}
          totalCount={documents.length}
          filteredCount={filteredDocuments.length}
        />

        <DocumentTable
          documents={filteredDocuments}
          isLoading={isLoadingDocs}
          onSelectDocument={setSelectedDoc}
        />
      </section>

      {/* Document Detail Modal */}
      <DocumentDetailModal
        doc={selectedDoc}
        isOpen={Boolean(selectedDoc)}
        onClose={() => setSelectedDoc(null)}
      />
    </div>
  );
}
