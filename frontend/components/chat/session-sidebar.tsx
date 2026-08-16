"use client";

import { memo } from "react";
import { MessageSquare, Plus, MessageCircle, X } from "lucide-react";
import type { SessionSummary } from "@/types/api";

interface SessionSidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
}

export const SessionSidebar = memo(function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  isOpen,
  onClose,
  isLoading,
}: SessionSidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed top-14 bottom-0 left-0 z-30 flex w-72 flex-col border-r border-border-subtle bg-surface-raised transition-transform duration-200 lg:static lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Conversation sessions"
      >
        {/* Header with New Chat action */}
        <div className="flex items-center justify-between border-b border-border-subtle p-3">
          <button
            onClick={() => {
              onNewSession();
              onClose();
            }}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-text-inverse transition-colors hover:bg-accent-hover shadow-sm"
          >
            <Plus size={15} />
            <span>New Chat</span>
          </button>
          <button
            onClick={onClose}
            aria-label="Close session drawer"
            className="ml-2 rounded-lg p-2 text-text-tertiary hover:bg-surface-overlay hover:text-text-primary lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Recent Threads
          </div>

          {isLoading && sessions.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-text-tertiary">
              Loading sessions…
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-text-tertiary">
              <MessageCircle size={24} className="mx-auto mb-2 opacity-40" />
              <p>No previous conversations</p>
              <p className="mt-1 text-[11px]">Start a new thread above</p>
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.session_id === activeSessionId;
              const displayTitle =
                s.preview ||
                (s.session_id.startsWith("session_")
                  ? `Thread ${s.session_id.slice(8, 16)}`
                  : s.session_id);

              return (
                <button
                  key={s.session_id}
                  onClick={() => {
                    onSelectSession(s.session_id);
                    onClose();
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${
                    isActive
                      ? "bg-accent-subtle text-accent font-medium"
                      : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 truncate">
                    <MessageSquare size={14} className="shrink-0" />
                    <span className="truncate">{displayTitle}</span>
                  </div>
                  <span className="shrink-0 rounded bg-surface-elevated px-1.5 py-0.5 text-[10px] text-text-tertiary">
                    {s.message_count}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
});
