/**
 * Chat Container - Feature Component
 * 
 * Business: Chat interface, message rendering, streaming
 * Responsibility: Compose chat sub-features
 */

"use client";

import { useEffect, useRef } from "react";
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

  const messages = (currentSessionId ? messagesBySession[currentSessionId] : undefined) ?? [];
  const currentSession = getCurrentSession();

  // Load persisted messages when session changes
  useEffect(() => {
    if (!currentSessionId) return;
    setCurrentSession(currentSessionId);

    // Only fetch if we don't already have messages in memory
    if (messagesBySession[currentSessionId]?.length) return;

    fetch(`/api/sessions/${currentSessionId}/messages`)
      .then((r) => r.ok ? r.json() : { messages: [] })
      .then((data: { messages: Array<{ id: string; role: string; content: string; timestamp: string; sessionId?: string; metadata?: Record<string, unknown> }> }) => {
        if (!data.messages?.length) return;
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
      .catch(() => {});
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
        disabled={!currentSessionId}
      />
    </div>
  );
}
