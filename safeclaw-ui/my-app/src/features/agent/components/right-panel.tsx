/**
 * Right Panel - Feature Component
 * 
 * Business: Execution graph, skills used, context visibility
 * Responsibility: Agent runtime visibility
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Wrench, FileText, X } from "lucide-react";
import { useUIStore, RightPanelView } from "@/stores/ui-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useMessageStore } from "@/stores/message-store";
import { useSessionStore } from "@/stores/session-store";
import { useSkillStore } from "@/stores/skill-store";
import { cn } from "@/shared/utils/cn";
import { ExecutionGraph } from "./execution-graph";

const TABS: { id: RightPanelView; label: string; icon: typeof Activity }[] = [
  { id: "execution", label: "Execution", icon: Activity },
  { id: "skills", label: "Skills", icon: Wrench },
  { id: "context", label: "Context", icon: FileText },
];

export function RightPanel() {
  const { rightPanelView, setRightPanelView, rightPanelOpen, toggleRightPanel } = useUIStore();
  const { getActiveExecution, getExecutionPath } = useExecutionStore();
  const { getLastMessage, isStreaming } = useMessageStore();

  const lastMessage = getLastMessage();
  const execution = lastMessage ? getExecutionPath(lastMessage.id) : [];

  return (
    <div className="h-full flex flex-col bg-white border-l border-slate-200">
      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setRightPanelView(tab.id)}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors",
              rightPanelView === tab.id
                ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50/50"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
            )}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Close Button */}
      <button
        onClick={toggleRightPanel}
        className="absolute top-2 right-2 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={rightPanelView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {rightPanelView === "execution" && (
              <ExecutionGraphView executionPath={execution} isActive={isStreaming} />
            )}

            {rightPanelView === "skills" && <SkillsUsedView />}

            {rightPanelView === "context" && <ContextView />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function ExecutionGraphView({
  executionPath,
  isActive,
}: {
  executionPath: { name: string; duration: number }[];
  isActive: boolean;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-900">Execution Path</h3>

      {executionPath.length === 0 ? (
        <p className="text-sm text-slate-400">
          {isActive
            ? "Execution in progress..."
            : "No execution data available"}
        </p>
      ) : (
        <div className="space-y-2">
          {executionPath.map((step, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-2 rounded-lg bg-slate-50"
            >
              <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">
                {index + 1}
              </div>
              <div className="flex-1">
                <p className="text-sm text-slate-700">{step.name}</p>
                <p className="text-xs text-slate-400">
                  {step.duration.toFixed(2)}s
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SkillsUsedView() {
  const { getLastMessage } = useMessageStore();
  const lastMsg = getLastMessage();
  const skillsUsed: string[] = lastMsg?.metadata?.skillsUsed ?? [];

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-900">Skills Used</h3>

      {skillsUsed.length === 0 ? (
        <p className="text-sm text-slate-400">No skills used yet in this session.</p>
      ) : (
        <div className="space-y-2">
          {skillsUsed.map((name) => (
            <div
              key={name}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-50"
            >
              <span className="text-sm text-slate-700">{name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ContextView() {
  const { getCurrentSession } = useSessionStore();
  const { getEnabledSkills, totalSkills } = useSkillStore();
  const { getCurrentMessages } = useMessageStore();

  const session = getCurrentSession();
  const enabledSkills = getEnabledSkills();
  const messages = getCurrentMessages();
  const estimatedTokens = messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-900">Context</h3>

      <div className="space-y-4 text-sm text-slate-600">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase mb-1">
            Current Session
          </p>
          <p className="truncate">{session?.title ?? "No session"}</p>
          {session?.id && (
            <p className="text-xs text-slate-400 font-mono">{session.id.slice(0, 12)}…</p>
          )}
        </div>

        <div>
          <p className="text-xs font-medium text-slate-400 uppercase mb-1">
            Model
          </p>
          <p>{session?.settings?.model ?? "Default"}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-400 uppercase mb-1">
            Estimated Tokens
          </p>
          <p>~{estimatedTokens.toLocaleString()}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-400 uppercase mb-1">
            Enabled Skills
          </p>
          {enabledSkills.length === 0 ? (
            <p className="text-slate-400">None enabled</p>
          ) : (
            <p className="text-slate-500 text-xs break-words">
              {enabledSkills.slice(0, 5).join(", ")}
              {enabledSkills.length > 5 && ` +${enabledSkills.length - 5} more`}
            </p>
          )}
          <p className="text-xs text-slate-400 mt-1">{enabledSkills.length} / {totalSkills} total</p>
        </div>
      </div>
    </div>
  );
}
