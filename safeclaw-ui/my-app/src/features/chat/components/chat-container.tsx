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
  const { messagesBySession, isStreaming } = useMessageStore();

  const messages = (currentSessionId ? messagesBySession[currentSessionId] : undefined) ?? [];
  const currentSession = getCurrentSession();

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
