"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Bot, Shield } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { ScrollArea } from "./ui/scroll-area";
import { cn } from "@/lib/utils";
import { ThinkingIndicator } from "./thinking-indicator";

function MessageBubble({ message, isStreaming }: { message: { role: string; content: string; id: string }; isStreaming?: boolean }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex gap-3 py-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
        isUser ? "bg-slate-200" : "bg-gradient-to-br from-blue-500 to-purple-600"
      )}>
        {isUser ? (
          <User className="w-4 h-4 text-slate-600" />
        ) : (
          <Shield className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn(
        "flex-1 max-w-[85%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser 
            ? "bg-blue-600 text-white ml-auto" 
            : "bg-slate-100 text-slate-900"
        )}>
          {isStreaming ? (
            <span className="animate-pulse">▊</span>
          ) : (
            <div className="prose prose-sm max-w-none">
              {message.content.split('\n').map((line, i) => (
                <p key={i} className="mb-1 last:mb-0">{line}</p>
              ))}
            </div>
          )}
        </div>
        
        {/* Timestamp */}
        <div className={cn(
          "text-xs text-slate-400 mt-1",
          isUser ? "text-right" : "text-left"
        )}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </motion.div>
  );
}

export function MessageList() {
  const { messages, isStreaming, currentStreamingContent } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, currentStreamingContent]);

  return (
    <ScrollArea className="h-full px-4 py-2">
      <div className="max-w-3xl mx-auto space-y-2">
        {/* Welcome message if empty */}
        {messages.length === 0 && !isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Welcome to SafeClaw
            </h2>
            <p className="text-slate-500 max-w-md mx-auto">
              Your AI safety assistant. Start a conversation by typing a message below.
            </p>
          </motion.div>
        )}

        {/* Messages */}
        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <MessageBubble 
              key={message.id} 
              message={message} 
            />
          ))}
        </AnimatePresence>

        {/* Streaming message */}
        {isStreaming && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <MessageBubble
              message={{
                role: 'assistant',
                content: currentStreamingContent,
                id: 'streaming'
              }}
              isStreaming={currentStreamingContent.length === 0}
            />
          </motion.div>
        )}

        {/* Thinking indicator */}
        <ThinkingIndicator />

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
