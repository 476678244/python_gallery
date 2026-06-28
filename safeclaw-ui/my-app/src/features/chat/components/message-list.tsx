import { motion, AnimatePresence } from "framer-motion";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/entities/message";
import { cn } from "@/shared/utils/cn";
import { StreamingMessage } from "./streaming-message";

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  return (
    <div className="py-4 space-y-4">
      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => (
          <MessageItem
            key={message.id}
            message={message}
            isLast={index === messages.length - 1}
          />
        ))}
      </AnimatePresence>

      {/* Streaming Indicator */}
      {isStreaming && <StreamingMessage />}
    </div>
  );
}

interface MessageItemProps {
  message: Message;
  isLast: boolean;
}

function MessageItem({ message, isLast }: MessageItemProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex gap-4 px-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div
        data-role={isUser ? "user" : "assistant"}
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          "prose prose-sm max-w-none",
          isUser
            ? "bg-blue-500 text-white prose-invert"
            : "bg-slate-100 text-slate-900"
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            table: ({ children }) => (
              <table className="border-collapse border border-slate-300 w-full my-4">
                {children}
              </table>
            ),
            th: ({ children }) => (
              <th className="border border-slate-300 px-2 py-1 text-left bg-slate-100 font-semibold">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-slate-300 px-2 py-1 text-left">
                {children}
              </td>
            ),
          }}
        >
          {message.content}
        </ReactMarkdown>

        {/* Metadata */}
        {message.metadata && !isUser && (
          <div className="mt-2 pt-2 border-t border-slate-200/50 text-xs text-slate-500">
            {message.metadata.processingTime && (
              <span>{message.metadata.processingTime.toFixed(1)}s</span>
            )}
            {message.metadata.agent && (
              <span className="ml-2">• {message.metadata.agent}</span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
