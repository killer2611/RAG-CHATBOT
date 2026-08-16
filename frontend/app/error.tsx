"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error for debugging — never expose stack traces to end users.
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-xl font-semibold text-text-primary">
        Something went wrong
      </h1>
      <p className="max-w-md text-sm text-text-secondary">
        An unexpected error occurred. Please try again.
      </p>
      <button
        onClick={reset}
        className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-text-inverse transition-colors duration-[var(--transition-fast)] hover:bg-accent-hover"
      >
        Try again
      </button>
    </div>
  );
}
