/**
 * Streaming Message - Feature Component
 * 
 * Business: Show streaming state with thinking indicator
 * Responsibility: Streaming UI, thinking steps animation
 */

"use client";

import { motion } from "framer-motion";
import { Bot, Loader2 } from "lucide-react";
import { useMessageStore } from "@/stores/message-store";
import { useExecutionStore } from "@/stores/execution-store";
import { cn } from "@/shared/utils/cn";

export function StreamingMessage() {
  const { streamingContent } = useMessageStore();
  const { isThinking, thinkingSteps, currentThinkingStep } = useExecutionStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4 px-4"
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>

      {/* Content */}
      <div className="max-w-[80%] space-y-3">
        {/* Thinking Indicator */}
        {isThinking && (
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <div className="flex items-center gap-2 text-sm text-slate-600 mb-3">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
            </div>

            {/* Thinking Steps */}
            <div className="space-y-2">
              {thinkingSteps.map((step, index) => {
                const isActive = step === currentThinkingStep;
                const isCompleted =
                  thinkingSteps.indexOf(currentThinkingStep || "") > index;

                return (
                  <motion.div
                    key={step}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={cn(
                      "flex items-center gap-2 text-sm transition-colors",
                      isActive && "text-blue-600 font-medium",
                      isCompleted && "text-slate-400",
                      !isActive && !isCompleted && "text-slate-500"
                    )}
                  >
                    <div
                      className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        isActive && "bg-blue-500 animate-pulse",
                        isCompleted && "bg-green-500",
                        !isActive && !isCompleted && "bg-slate-300"
                      )}
                    />
                    <span>{step}</span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* Streaming Content */}
        {streamingContent && (
          <div className="bg-slate-100 rounded-2xl px-4 py-3 text-slate-900 whitespace-pre-wrap">
            {streamingContent}
            <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse" />
          </div>
        )}
      </div>
    </motion.div>
  );
}
