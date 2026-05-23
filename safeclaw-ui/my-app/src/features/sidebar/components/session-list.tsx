/**
 * Session List Component
 * 
 * Business: Display and manage chat sessions
 * Responsibility: List rendering, selection, deletion
 */

"use client";

import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Trash2, Loader2 } from "lucide-react";
import { useSessionStore } from "@/stores/session-store";
import { formatSessionTime } from "@/entities/session";
import { cn } from "@/shared/utils/cn";

export function SessionList() {
  const { 
    sessions, 
    currentSessionId, 
    setCurrentSession, 
    deleteSession, 
    isLoading,
    error 
  } = useSessionStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-4 text-sm text-red-600">
        <p>Error loading sessions</p>
        <p className="text-xs text-red-400">{error}</p>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
        <p className="text-sm text-slate-500">No sessions yet</p>
        <p className="text-xs text-slate-400 mt-1">
          Start a new chat to begin
        </p>
      </div>
    );
  }

  return (
    <div className="p-2 space-y-1">
      <AnimatePresence mode="popLayout">
        {sessions.map((session) => (
          <motion.div
            key={session.id}
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="group relative"
          >
            <button
              onClick={() => setCurrentSession(session.id)}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left",
                "transition-all duration-200",
                currentSessionId === session.id
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "text-slate-600 hover:bg-slate-100"
              )}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {session.title || "Untitled Chat"}
                </p>
                <p className="text-xs text-slate-400">
                  {formatSessionTime(session)}
                </p>
              </div>

              <div className="flex items-center gap-1">
                {session.messageCount > 0 && (
                  <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                    {session.messageCount}
                  </span>
                )}

                {/* Delete button - visible on hover */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }
                  }}
                  className={cn(
                    "p-1.5 rounded-md opacity-0 group-hover:opacity-100",
                    "transition-all duration-200 cursor-pointer",
                    "hover:bg-red-100 hover:text-red-600",
                    currentSessionId === session.id && "hover:bg-red-100"
                  )}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </div>
              </div>
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
