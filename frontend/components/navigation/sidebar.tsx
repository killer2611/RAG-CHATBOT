"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  BookOpen,
  FlaskConical,
  Activity,
  Settings,
  Menu,
  X,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Chat", href: "/chat", icon: MessageSquare },
  { label: "Library", href: "/library", icon: BookOpen },
  { label: "Evaluate", href: "/evaluate", icon: FlaskConical },
  { label: "System", href: "/system", icon: Activity },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = useCallback(() => {
    setMobileOpen(false);
  }, []);

  const toggleMobile = useCallback(() => {
    setMobileOpen((prev) => !prev);
  }, []);

  // Close mobile nav on Escape key
  useEffect(() => {
    if (!mobileOpen) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeMobile();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [mobileOpen, closeMobile]);

  // Lock body scroll when mobile nav is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <>
      {/* ── Mobile Header Bar ── */}
      <header className="fixed top-0 left-0 right-0 z-40 flex h-14 items-center gap-3 border-b border-border-subtle bg-surface-raised px-4 md:hidden">
        <button
          onClick={toggleMobile}
          aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={mobileOpen}
          className="flex items-center justify-center rounded-md p-2 text-text-secondary hover:bg-surface-overlay hover:text-text-primary transition-colors duration-[var(--transition-fast)]"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="text-sm font-semibold tracking-tight text-text-primary">
          RAG Knowledge Platform
        </span>
      </header>

      {/* ── Mobile Overlay ── */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar Navigation ── */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 flex h-full w-[var(--sidebar-width)] flex-col border-r border-border-subtle bg-surface-raised transition-transform duration-[var(--transition-normal)]",
          "md:translate-x-0 md:z-30",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* ── Brand ── */}
        <div className="flex h-14 items-center gap-2.5 border-b border-border-subtle px-5">
          <Link
            href="/"
            onClick={closeMobile}
            className="flex items-center gap-2.5 text-text-primary no-underline"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-xs font-bold text-text-inverse">
              R
            </div>
            <span className="text-sm font-semibold tracking-tight">
              RAG Platform
            </span>
          </Link>
        </div>

        {/* ── Nav Links ── */}
        <nav className="flex flex-1 flex-col gap-1 px-3 py-3">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeMobile}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-[var(--transition-fast)] no-underline",
                  isActive
                    ? "bg-accent-subtle text-accent"
                    : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon
                  size={18}
                  className={cn(
                    "shrink-0 transition-colors duration-[var(--transition-fast)]",
                    isActive
                      ? "text-accent"
                      : "text-text-tertiary group-hover:text-text-secondary"
                  )}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* ── Footer ── */}
        <div className="border-t border-border-subtle px-5 py-3">
          <p className="text-xs text-text-tertiary">
            Flagship RAG v0.1
          </p>
        </div>
      </aside>
    </>
  );
}
