/**
 * Chat Container - Feature Component
 * 
 * Business: Chat interface, message rendering, streaming
 * Responsibility: Compose chat sub-features
 */

"use client";

import { useEffect, useRef, useState } from "react";
import { useMessageStore } from "@/stores/message-store";
import { useSessionStore } from "@/stores/session-store";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { cn } from "@/shared/utils/cn";

export function ChatContainer() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { currentSessionId, getCurrentSession } = useSessionStore();
  const { messagesBySession, isStreaming, setCurrentSession, clearMessages, addMessage } = useMessageStore();
  const [loadError, setLoadError] = useState<string | null>(null);

  const messages = (currentSessionId ? messagesBySession[currentSessionId] : undefined) ?? [];
  const currentSession = getCurrentSession();

  // Load persisted messages when session changes — Fail Fast on HTTP/parse errors
  useEffect(() => {
    if (!currentSessionId) return;
    setCurrentSession(currentSessionId);
    setLoadError(null);

    // Only fetch if we don't already have messages in memory
    if (messagesBySession[currentSessionId]?.length) return;

    void fetch(`/api/sessions/${currentSessionId}/messages`)
      .then(async (r) => {
        if (!r.ok) {
          throw new Error(
            `[ChatContainer] Failed to load messages (Fail Fast)\n` +
              `  sessionId: ${currentSessionId}\n` +
              `  Status: ${r.status}`
          );
        }
        return r.json() as Promise<{
          messages: Array<{
            id: string;
            role: string;
            content: string;
            timestamp: string;
            sessionId?: string;
            metadata?: Record<string, unknown>;
          }>;
        }>;
      })
      .then((data) => {
        if (!Array.isArray(data.messages)) {
          throw new Error(
            `[ChatContainer] messages payload must be an array (Fail Fast)\n` +
              `  sessionId: ${currentSessionId}\n` +
              `  Actual: ${typeof data.messages}`
          );
        }
        if (!data.messages.length) return;
        clearMessages(currentSessionId);
        data.messages.forEach((m) => {
          addMessage({
            ...m,
            role: m.role as import("@/entities/message").MessageRole,
            timestamp: new Date(m.timestamp),
            sessionId: currentSessionId,
          });
        });
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : String(err);
        console.error(message);
        setLoadError(message);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSessionId]);

  // Auto-scroll to bottom on new messages or streaming
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <ChatHeader 
        session={currentSession} 
        messageCount={messages.length}
      />

      {loadError && (
        <div
          data-testid="messages-load-error"
          className="px-4 py-2 text-xs text-red-600 bg-red-50 border-b border-red-100 whitespace-pre-wrap"
        >
          {loadError}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <MessageList 
          messages={messages} 
          isStreaming={isStreaming}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput 
        sessionId={currentSessionId}
        disabled={!currentSessionId || !!loadError}
      />
    </div>
  );
}
