import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-xl font-semibold text-text-primary">
        Page not found
      </h1>
      <p className="max-w-md text-sm text-text-secondary">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/"
        className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-text-inverse no-underline transition-colors duration-[var(--transition-fast)] hover:bg-accent-hover"
      >
        Return home
      </Link>
    </div>
  );
}
