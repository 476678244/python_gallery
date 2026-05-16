"use client";

import { motion } from "framer-motion";
import { useChatStore } from "@/stores/chat-store";
import { Sparkles, Search, BarChart3, TrendingUp, DollarSign, Brain, CheckCircle2, Clock } from "lucide-react";
import { useState, useEffect } from "react";

const THINKING_STEPS = [
  { id: 'reasoning', name: 'Reasoning', icon: Brain, color: 'from-blue-500 to-purple-600' },
  { id: 'search', name: 'Search global tire market for Porsche Macan', icon: Search, color: 'from-green-500 to-emerald-600' },
  { id: 'analyze', name: 'Analyze tire size distribution and specifications', icon: BarChart3, color: 'from-amber-500 to-orange-600' },
  { id: 'brands', name: 'Find top tire brands for Porsche Macan', icon: TrendingUp, color: 'from-pink-500 to-rose-600' },
  { id: 'research', name: 'Research price ranges and market data', icon: DollarSign, color: 'from-cyan-500 to-blue-600' },
  { id: 'drivers', name: 'Identify key purchase drivers and trends', icon: Sparkles, color: 'from-violet-500 to-purple-600' },
];

interface Step {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed';
  duration?: number;
}

export function ThinkingIndicator() {
  const { isStreaming, messages } = useChatStore();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [stepStartTime, setStepStartTime] = useState<number>(Date.now());
  const [stepDurations, setStepDurations] = useState<Record<number, number>>({});

  useEffect(() => {
    if (!isStreaming) {
      setCurrentStepIndex(0);
      setCompletedSteps(new Set());
      return;
    }

    // Simulate step progression
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < THINKING_STEPS.length - 1) {
          // Mark current step as completed
          setCompletedSteps((completed) => new Set([...completed, prev]));
          setStepDurations((durations) => ({
            ...durations,
            [prev]: (Date.now() - stepStartTime) / 1000
          }));
          setStepStartTime(Date.now());
          return prev + 1;
        }
        return prev;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [isStreaming, stepStartTime]);

  // Only show during streaming when we have messages
  const lastMessage = messages[messages.length - 1];
  const shouldShow = isStreaming && lastMessage?.role === 'user';

  if (!shouldShow) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3 py-4"
    >
      {/* Agent Avatar */}
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
        <Sparkles className="w-4 h-4 text-white" />
      </div>

      {/* Thinking Card */}
      <div className="flex-1 max-w-[85%]">
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-xl p-4">
          {/* Header */}
          <div className="flex items-center gap-2 mb-3">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles className="w-4 h-4 text-blue-600" />
            </motion.div>
            <span className="font-medium text-slate-900">Reasoning</span>
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-blue-600"
            >
              ...
            </motion.span>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            {THINKING_STEPS.map((step, index) => {
              const isCompleted = completedSteps.has(index);
              const isCurrent = index === currentStepIndex;
              const isPending = index > currentStepIndex;
              const duration = stepDurations[index];
              const Icon = step.icon;

              if (isPending) return null;

              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex items-center gap-3 p-2 rounded-lg ${
                    isCurrent 
                      ? 'bg-white/60 shadow-sm' 
                      : isCompleted 
                        ? 'opacity-70' 
                        : ''
                  }`}
                >
                  {/* Status Icon */}
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                    isCompleted 
                      ? 'bg-green-500' 
                      : isCurrent 
                        ? `bg-gradient-to-br ${step.color}` 
                        : 'bg-slate-200'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle2 className="w-3 h-3 text-white" />
                    ) : (
                      <Icon className="w-3 h-3 text-white" />
                    )}
                  </div>

                  {/* Step Name */}
                  <span className={`text-sm flex-1 ${
                    isCompleted ? 'text-slate-500 line-through' : 'text-slate-700'
                  }`}>
                    {step.name}
                  </span>

                  {/* Duration */}
                  {isCompleted && duration && (
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {duration.toFixed(1)}s
                    </span>
                  )}

                  {/* Running indicator */}
                  {isCurrent && (
                    <motion.div
                      className="flex gap-0.5"
                    >
                      {[0, 1, 2].map((i) => (
                        <motion.span
                          key={i}
                          className="w-1 h-1 bg-blue-500 rounded-full"
                          animate={{ 
                            scale: [1, 1.5, 1],
                            opacity: [0.3, 1, 0.3]
                          }}
                          transition={{ 
                            duration: 1.4, 
                            repeat: Infinity, 
                            delay: i * 0.2 
                          }}
                        />
                      ))}
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
