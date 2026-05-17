/**
 * Chat Input - Feature Component
 * 
 * Business: Message input, quick actions, file attachments
 * Responsibility: Input handling, validation, submission
 */

"use client";

import { useState, useRef, useCallback } from "react";
import { Send, Paperclip, Mic, Plus, Code, FileText, Sparkles } from "lucide-react";
import { useMessageStore } from "@/stores/message-store";
import { useExecutionStore } from "@/stores/execution-store";
import { streamChat } from "@/features/chat/services/chat-api";
import { cn } from "@/shared/utils/cn";

const QUICK_ACTIONS = [
  { icon: Sparkles, label: "Research", color: "text-purple-500" },
  { icon: FileText, label: "Analyze", color: "text-blue-500" },
  { icon: Code, label: "Code", color: "text-amber-500" },
  { icon: Plus, label: "Context", color: "text-slate-500" },
];

interface ChatInputProps {
  sessionId: string | null;
  disabled?: boolean;
}

export function ChatInput({ sessionId, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { 
    addUserMessage, 
    startStreaming, 
    appendStreamingContent,
    completeStreaming,
    cancelStreaming,
    isStreaming,
    getMessagesForSession,
  } = useMessageStore();

  const {
    startExecution,
    addThinkingStep,
    completeThinkingStep,
    setThinking,
    completeExecution,
  } = useExecutionStore();

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isStreaming || !sessionId) return;

    const content = input.trim();
    setInput("");

    // Add user message
    const userMessage = addUserMessage(content, sessionId);

    // Get all messages for context
    const messages = getMessagesForSession(sessionId);
    const apiMessages = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    // Start streaming
    const streamingId = startStreaming(sessionId);
    startExecution(sessionId, streamingId);
    setThinking(true);

    // Stream chat
    await streamChat(
      {
        messages: apiMessages,
        sessionId: sessionId,
      },
      {
        onThinking: (step) => {
          addThinkingStep(step);
        },
        onContent: (content) => {
          // Content updates handled in store
        },
        onComplete: (data) => {
          completeStreaming(data.message.content);
          completeExecution(streamingId);
          setThinking(false);
          // Persist after state update is flushed
          setTimeout(() => {
            const allMessages = getMessagesForSession(sessionId!);
            fetch(`/api/sessions/${sessionId}/messages`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                messages: allMessages.map((m) => ({
                  ...m,
                  timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp,
                })),
              }),
            }).catch(() => {});
          }, 0);
        },
        onError: (error) => {
          console.error("Chat error:", error);
          cancelStreaming();
          setThinking(false);
        },
      }
    );
  }, [
    input,
    isStreaming,
    sessionId,
    addUserMessage,
    getMessagesForSession,
    startStreaming,
    startExecution,
    setThinking,
    addThinkingStep,
    completeStreaming,
    completeExecution,
    cancelStreaming,
  ]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      {/* Quick Actions */}
      <div className="flex gap-2 mb-3 overflow-x-auto">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs",
              "bg-slate-100 hover:bg-slate-200 transition-colors",
              "text-slate-600 whitespace-nowrap"
            )}
          >
            <action.icon className={cn("w-3.5 h-3.5", action.color)} />
            <span>{action.label}</span>
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div
        className={cn(
          "relative flex items-end gap-2 rounded-xl border p-3 transition-all",
          isFocused
            ? "border-blue-500 ring-2 ring-blue-500/20"
            : "border-slate-200 hover:border-slate-300"
        )}
      >
        {/* Attachment Button */}
        <button
          className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          title="Attach files"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={disabled ? "Select a session to start chatting..." : "Ask anything..."}
          disabled={disabled || isStreaming}
          rows={1}
          className={cn(
            "flex-1 resize-none bg-transparent outline-none",
            "text-slate-900 placeholder:text-slate-400",
            "min-h-[24px] max-h-[200px]"
          )}
          style={{ height: "auto" }}
        />

        {/* Voice & Send */}
        <div className="flex items-center gap-1">
          <button
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Voice input"
          >
            <Mic className="w-5 h-5" />
          </button>

          <button
            onClick={handleSubmit}
            disabled={!input.trim() || disabled || isStreaming}
            className={cn(
              "p-2 rounded-lg transition-colors",
              input.trim() && !disabled && !isStreaming
                ? "bg-blue-500 text-white hover:bg-blue-600"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
