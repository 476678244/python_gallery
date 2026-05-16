"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Send, Paperclip, Mic, AtSign, Plus, Code, FileText, Sparkles } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { useChatStream } from "@/hooks/use-chat-stream";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";

const QUICK_ACTIONS = [
  { icon: Sparkles, label: "Deep Research", color: "text-purple-500" },
  { icon: FileText, label: "Analyze Data", color: "text-blue-500" },
  { icon: FileText, label: "Create Report", color: "text-green-500" },
  { icon: Code, label: "Code", color: "text-amber-500" },
  { icon: Plus, label: "Add Context", color: "text-slate-500" },
];

export function ChatInput() {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { 
    addMessage, 
    setIsStreaming, 
    setCurrentStreamingContent, 
    messages,
    currentSessionId,
    enabledSkills,
    selectedModel,
  } = useChatStore();

  const { sendMessage, isStreaming } = useChatStream({
    onThinking: (step, status, duration) => {
      // Could update thinking state here if needed
      console.log(`Thinking step: ${step} - ${status} (${duration}s)`);
    },
    onContent: (content, delta) => {
      setCurrentStreamingContent(content);
    },
    onComplete: (data) => {
      // Add final assistant message
      const assistantMessage = {
        id: data.messageId,
        role: 'assistant' as const,
        content: data.content,
        timestamp: new Date(),
        metadata: {
          agent: 'safeclaw',
          executionPath: data.executionPath?.map(p => p.name),
          processingTime: data.timing?.totalDuration,
          usage: data.usage,
        },
      };
      addMessage(assistantMessage);
      setIsStreaming(false);
      setCurrentStreamingContent("");
    },
    onError: (error) => {
      console.error("Chat error:", error);
      setIsStreaming(false);
      // Could add error message to chat
    },
  });

  const handleSubmit = async () => {
    if (!input.trim() || isStreaming) return;

    // Add user message
    const userMessageId = crypto.randomUUID();
    const userMessage = {
      id: userMessageId,
      role: 'user' as const,
      content: input,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setInput("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Start streaming
    setIsStreaming(true);
    setCurrentStreamingContent("");

    // Send to API
    const allMessages = [...messages, userMessage];
    const apiMessages = allMessages.map(m => ({ role: m.role, content: m.content }));
    
    await sendMessage({
      messages: apiMessages,
      sessionId: currentSessionId || undefined,
      enabledSkills: Array.from(enabledSkills),
      model: selectedModel,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement;
    target.style.height = 'auto';
    target.style.height = Math.min(target.scrollHeight, 200) + 'px';
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <div className="max-w-3xl mx-auto">
        {/* Quick Actions */}
        <div className="flex gap-2 mb-3 overflow-x-auto pb-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 text-xs font-medium text-slate-600 transition-colors whitespace-nowrap"
            >
              <action.icon className={`w-3.5 h-3.5 ${action.color}`} />
              {action.label}
            </button>
          ))}
        </div>

        {/* Input Container */}
        <motion.div
          animate={{
            boxShadow: isFocused 
              ? "0 0 0 2px rgba(59, 130, 246, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)" 
              : "0 2px 8px rgba(0, 0, 0, 0.04)"
          }}
          className="relative rounded-xl border border-slate-200 bg-white"
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Message SafeClaw..."
            rows={1}
            className="w-full resize-none bg-transparent px-4 py-3 pr-24 text-sm placeholder:text-slate-400 focus:outline-none max-h-[200px]"
          />

          {/* Input Actions */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <Plus className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <AtSign className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <Paperclip className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <Mic className="w-4 h-4" />
            </button>
            <Button
              onClick={handleSubmit}
              disabled={!input.trim()}
              size="icon"
              className="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>

        {/* Footer */}
        <div className="flex justify-center mt-2">
          <p className="text-xs text-slate-400">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
