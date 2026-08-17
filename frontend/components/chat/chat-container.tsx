"use client";

import { useCallback, useEffect, useState, useRef, useSyncExternalStore } from "react";
import { Menu, Plus, RefreshCw, AlertCircle } from "lucide-react";
import { MessageList } from "@/components/chat/message-list";
import { ChatComposer } from "@/components/chat/chat-composer";
import { SessionSidebar } from "@/components/chat/session-sidebar";
import { EvidenceInspector } from "@/components/evidence/evidence-inspector";
import { useChatStream } from "@/lib/hooks/use-chat-stream";
import { getChatMessages, getChatSessions } from "@/lib/api/client";
import type { ChatMessage } from "@/components/chat/message-item";
import type { SessionSummary, SourceCitation } from "@/types/api";

function createSessionId(): string {
  const timestamp = Date.now().toString(36);
  const rand = Math.random().toString(36).substring(2, 7);
  return `session_${timestamp}_${rand}`;
}

const emptySubscribe = () => () => {};

export function ChatContainer() {
  const isHydrated = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );

  const [sessionId, setSessionId] = useState<string>(() => createSessionId());
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Evidence Inspector State
  const [activeEvidence, setActiveEvidence] = useState<{
    sources: SourceCitation[];
    initialIndex: number;
  } | null>(null);

  const lastUserMessageRef = useRef<string>("");
  const messageIdCounter = useRef<number>(0);

  // Load sessions list
  const refreshSessions = useCallback(async () => {
    try {
      setIsLoadingSessions(true);
      const list = await getChatSessions();
      setSessions(list);
    } catch {
      // Backend may be offline or no sessions yet
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  // Initial sessions load
  useEffect(() => {
    let isMounted = true;
    getChatSessions()
      .then((list) => {
        if (isMounted) {
          setSessions(list);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, []);

  // Load messages for a selected session
  const selectSession = useCallback(
    async (targetSessionId: string) => {
      setSessionId(targetSessionId);
      setHistoryError(null);
      setActiveEvidence(null);
      setIsLoadingHistory(true);
      try {
        const history = await getChatMessages(targetSessionId);
        const mappedMessages: ChatMessage[] = history.messages.map(
          (m, idx) => ({
            id: `${targetSessionId}-${idx}`,
            role: m.role,
            content: m.content,
          })
        );
        setMessages(mappedMessages);
      } catch (err) {
        setHistoryError(
          err instanceof Error
            ? err.message
            : "Failed to load session message history"
        );
      } finally {
        setIsLoadingHistory(false);
      }
    },
    []
  );

  const handleNewSession = useCallback(() => {
    const newId = createSessionId();
    setSessionId(newId);
    setMessages([]);
    setHistoryError(null);
    setActiveEvidence(null);
  }, []);

  const handleStreamDone = useCallback(
    (_finishedSessionId: string, fullAnswer: string, sourcesList: SourceCitation[]) => {
      messageIdCounter.current += 1;
      const assistantMessage: ChatMessage = {
        id: `assistant-${messageIdCounter.current}`,
        role: "assistant",
        content: fullAnswer,
        sources: sourcesList,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      refreshSessions();
    },
    [refreshSessions]
  );

  // Streaming Hook
  const {
    status,
    tokens,
    sources,
    error,
    sendMessage,
    abort,
  } = useChatStream({
    onDone: handleStreamDone,
  });

  const isStreaming = status === "streaming";

  const handleSend = useCallback(
    async (text: string) => {
      if (isStreaming) return;
      lastUserMessageRef.current = text;
      messageIdCounter.current += 1;

      // Ensure active session ID exists before dispatching
      const activeSession = sessionId || createSessionId();
      if (!sessionId) {
        setSessionId(activeSession);
      }

      // Add user turn immediately to message list
      const userMessage: ChatMessage = {
        id: `user-${messageIdCounter.current}`,
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, userMessage]);

      await sendMessage(activeSession, text);
    },
    [sessionId, isStreaming, sendMessage]
  );

  const handleRetry = useCallback(() => {
    if (lastUserMessageRef.current) {
      handleSend(lastUserMessageRef.current);
    }
  }, [handleSend]);

  const handleInspectEvidence = useCallback(
    (evidenceSources: SourceCitation[], initialIndex: number) => {
      setActiveEvidence({
        sources: evidenceSources,
        initialIndex,
      });
    },
    []
  );

  const handleCloseEvidence = useCallback(() => {
    setActiveEvidence(null);
  }, []);

  return (
    <div className="relative flex h-[calc(100dvh-3.5rem)] md:h-screen w-full overflow-hidden bg-surface-base">
      {/* Session Drawer / Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={sessionId}
        onSelectSession={selectSession}
        onNewSession={handleNewSession}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        isLoading={isLoadingSessions}
      />

      {/* Main Conversation Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Workspace Top Header Bar */}
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-border-subtle bg-surface-raised px-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSidebarOpen((prev) => !prev)}
              aria-label="Toggle sessions sidebar"
              className="rounded-lg p-1.5 text-text-secondary hover:bg-surface-overlay hover:text-text-primary transition-colors lg:hidden"
            >
              <Menu size={18} />
            </button>
            <span className="text-xs font-semibold text-text-primary truncate max-w-[200px] sm:max-w-xs">
              {isHydrated && sessionId
                ? sessionId.startsWith("session_")
                  ? `Thread ${sessionId.slice(8, 16)}`
                  : sessionId
                : "New Thread"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleNewSession}
              aria-label="Create new conversation thread"
              className="flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-base px-2.5 py-1 text-xs font-medium text-text-secondary hover:border-border-default hover:text-text-primary transition-colors"
            >
              <Plus size={14} />
              <span className="hidden sm:inline">New Thread</span>
            </button>
          </div>
        </header>

        {/* History Error Banner */}
        {historyError && (
          <div className="flex items-center justify-between bg-error/10 border-b border-error/20 px-4 py-2 text-xs text-error">
            <div className="flex items-center gap-2">
              <AlertCircle size={14} />
              <span>{historyError}</span>
            </div>
            <button
              onClick={() => selectSession(sessionId)}
              className="flex items-center gap-1 underline hover:text-text-primary"
            >
              <RefreshCw size={12} />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Messages List Area */}
        {isLoadingHistory ? (
          <div className="flex flex-1 items-center justify-center text-xs text-text-tertiary">
            Loading conversation history…
          </div>
        ) : (
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            streamingTokens={tokens}
            streamingSources={sources}
            streamingError={error}
            onSelectPrompt={handleSend}
            onRetry={handleRetry}
            onInspectEvidence={handleInspectEvidence}
          />
        )}

        {/* Bottom Composer */}
        <ChatComposer
          isStreaming={isStreaming}
          onSend={handleSend}
          onAbort={abort}
          disabled={isLoadingHistory}
        />
      </div>

      {/* Evidence Inspector Side Panel / Bottom Sheet */}
      <EvidenceInspector
        sources={activeEvidence?.sources ?? null}
        initialIndex={activeEvidence?.initialIndex ?? 0}
        isOpen={Boolean(activeEvidence)}
        onClose={handleCloseEvidence}
      />
    </div>
  );
}
