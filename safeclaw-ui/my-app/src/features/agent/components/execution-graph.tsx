/**
 * Execution Graph - Visual Component
 * 
 * Business: Visualize agent execution flow
 * Responsibility: Graph rendering, animations, step status
 */

"use client";

import { motion } from "framer-motion";
import { ExecutionStep } from "@/entities/execution";
import { cn } from "@/shared/utils/cn";
import { Check, X, Loader2, Circle } from "lucide-react";

interface ExecutionGraphProps {
  steps: ExecutionStep[];
  rootStepId: string;
  isActive?: boolean;
}

export function ExecutionGraph({ steps, rootStepId, isActive }: ExecutionGraphProps) {
  const rootStep = steps.find((s) => s.id === rootStepId);
  if (!rootStep) return null;

  return (
    <div className="space-y-2">
      <StepNode step={rootStep} steps={steps} depth={0} isActive={isActive} />
    </div>
  );
}

interface StepNodeProps {
  step: ExecutionStep;
  steps: ExecutionStep[];
  depth: number;
  isActive?: boolean;
}

function StepNode({ step, steps, depth, isActive }: StepNodeProps) {
  const children = step.childrenIds
    ?.map((id) => steps.find((s) => s.id === id))
    .filter(Boolean) as ExecutionStep[];

  const hasChildren = children && children.length > 0;

  return (
    <div style={{ marginLeft: depth > 0 ? 24 : 0 }}>
      <div
        className={cn(
          "flex items-center gap-2 p-2 rounded-lg",
          "transition-colors",
          step.status === "running" && "bg-blue-50 border border-blue-100",
          step.status === "completed" && "bg-green-50/50",
          step.status === "error" && "bg-red-50",
          step.status === "pending" && "bg-slate-50"
        )}
      >
        {/* Status Icon */}
        <div
          className={cn(
            "w-5 h-5 rounded-full flex items-center justify-center",
            step.status === "running" && "text-blue-500",
            step.status === "completed" && "text-green-500",
            step.status === "error" && "text-red-500",
            step.status === "pending" && "text-slate-300"
          )}
        >
          {step.status === "running" && (
            <Loader2 className="w-4 h-4 animate-spin" />
          )}
          {step.status === "completed" && <Check className="w-4 h-4" />}
          {step.status === "error" && <X className="w-4 h-4" />}
          {step.status === "pending" && <Circle className="w-4 h-4" />}
        </div>

        {/* Step Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-700 truncate">
            {step.name}
          </p>
          {step.duration && (
            <p className="text-xs text-slate-400">{step.duration.toFixed(2)}s</p>
          )}
        </div>

        {/* Type Badge */}
        <span
          className={cn(
            "text-xs px-2 py-0.5 rounded-full",
            step.type === "tool_call" && "bg-purple-100 text-purple-600",
            step.type === "model_call" && "bg-blue-100 text-blue-600",
            step.type === "reasoning" && "bg-amber-100 text-amber-600",
            step.type === "context_retrieval" && "bg-green-100 text-green-600"
          )}
        >
          {step.type}
        </span>
      </div>

      {/* Children */}
      {hasChildren && (
        <div className="mt-2 space-y-2 border-l-2 border-slate-200 pl-2">
          {children.map((child) => (
            <StepNode
              key={child.id}
              step={child}
              steps={steps}
              depth={depth + 1}
              isActive={isActive}
            />
          ))}
        </div>
      )}
    </div>
  );
}
