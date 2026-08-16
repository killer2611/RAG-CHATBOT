export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div
          className="h-6 w-6 animate-spin rounded-full border-2 border-border-default border-t-accent"
          role="status"
          aria-label="Loading"
        />
        <span className="text-sm text-text-tertiary">Loading…</span>
      </div>
    </div>
  );
}
