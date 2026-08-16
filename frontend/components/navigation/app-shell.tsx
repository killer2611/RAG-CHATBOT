"use client";

import { Sidebar } from "@/components/navigation/sidebar";

/**
 * Client shell containing the navigation sidebar and the main content area.
 * Separated from the root layout so that the layout itself remains a
 * Server Component (no "use client" directive on layout.tsx).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Sidebar />
      {/* Main content area — offset by sidebar on md+ screens */}
      <main
        id="main-content"
        className="min-h-screen pt-14 md:pl-[var(--sidebar-width)] md:pt-0"
      >
        {children}
      </main>
    </>
  );
}
