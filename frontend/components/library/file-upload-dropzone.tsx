"use client";

import { memo, useRef, useState, useCallback } from "react";
import { UploadCloud, FileText, AlertCircle } from "lucide-react";

interface FileUploadDropzoneProps {
  onUpload: (file: File) => void;
  isIngesting: boolean;
  disabled?: boolean;
}

const SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx"];
const MAX_FILE_SIZE_MB = 50;

export const FileUploadDropzone = memo(function FileUploadDropzone({
  onUpload,
  isIngesting,
  disabled = false,
}: FileUploadDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndProcess = useCallback(
    (file: File) => {
      setValidationError(null);
      const name = file.name.toLowerCase();
      const isSupported = SUPPORTED_EXTENSIONS.some((ext) => name.endsWith(ext));

      if (!isSupported) {
        setValidationError(
          `Unsupported file format (${file.name}). Only PDF, TXT, and DOCX files are supported.`
        );
        return;
      }

      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        setValidationError(
          `File size exceeds the ${MAX_FILE_SIZE_MB}MB limit (${(
            file.size /
            (1024 * 1024)
          ).toFixed(1)}MB).`
        );
        return;
      }

      onUpload(file);
    },
    [onUpload]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled || isIngesting) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled || isIngesting) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndProcess(files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndProcess(files[0]);
    }
    // Reset file input value so re-uploading the same file triggers change
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-2">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled && !isIngesting) {
            fileInputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload document dropzone. Drag and drop PDF, TXT, or DOCX files here, or click to browse."
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all cursor-pointer ${
          isDragOver
            ? "border-accent bg-accent-subtle/40 scale-[0.99]"
            : "border-border-default bg-surface-raised/50 hover:border-accent/60 hover:bg-surface-raised"
        } ${disabled || isIngesting ? "opacity-60 cursor-not-allowed pointer-events-none" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.docx"
          onChange={handleFileChange}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
        />

        {/* Center Icon */}
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-elevated text-accent mb-3 shadow-xs">
          <UploadCloud size={24} />
        </div>

        <h3 className="text-sm font-semibold text-text-primary">
          Upload Knowledge Document
        </h3>
        <p className="mt-1 max-w-sm text-xs text-text-secondary">
          Drag and drop your file here, or click to browse local filesystem.
        </p>

        {/* Badges */}
        <div className="mt-4 flex items-center gap-2 text-[11px] text-text-tertiary">
          <span className="flex items-center gap-1 rounded bg-surface-elevated px-2 py-0.5 font-medium">
            <FileText size={11} className="text-accent" /> PDF, TXT, DOCX
          </span>
          <span>•</span>
          <span>Max {MAX_FILE_SIZE_MB}MB</span>
        </div>
      </div>

      {/* Validation Error Alert */}
      {validationError && (
        <div className="flex items-center gap-2 rounded-lg border border-error/30 bg-error/10 p-3 text-xs text-error">
          <AlertCircle size={14} className="shrink-0" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
});
