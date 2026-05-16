/**
 * Sidebar Feature Component
 * 
 * Business: Session management, Skill tree, Workspace navigation
 * Responsibility: Compose sidebar sub-features
 */

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Shield, Plus, Loader2 } from "lucide-react";
import { useUIStore, SidebarView } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { SessionList } from "./session-list";
import { SkillTreePanel } from "@/features/skills/components/skill-tree-panel";
import { MemoryPanel } from "@/features/memory/components/memory-panel";
import { SystemPanel } from "@/features/system/components/system-panel";
import { SafetyPanel } from "@/features/safety/components/safety-panel";
import { SettingsPanel } from "@/features/settings/components/settings-panel";
import { cn } from "@/shared/utils/cn";

const SIDEBAR_VIEWS: { id: SidebarView; label: string }[] = [
  { id: "sessions", label: "Chat" },
  { id: "skills", label: "Skills" },
  { id: "memory", label: "Memory" },
  { id: "safety", label: "Safety" },
  { id: "system", label: "System" },
  { id: "settings", label: "Settings" },
];

export function Sidebar() {
  const { sidebarView, setSidebarView } = useUIStore();
  const { createSession, isCreating } = useSessionStore();
  const [isHovered, setIsHovered] = useState(false);

  const handleNewChat = async () => {
    await createSession("New Chat");
  };

  return (
    <div
      className="h-full flex flex-col bg-slate-50 border-r border-slate-200"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold text-slate-900">SafeClaw</span>
      </div>

      {/* View Tabs */}
      <div className="flex border-b border-slate-200">
        {SIDEBAR_VIEWS.map((view) => (
          <button
            key={view.id}
            onClick={() => setSidebarView(view.id)}
            className={cn(
              "flex-1 py-2 text-xs font-medium transition-colors",
              sidebarView === view.id
                ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50/50"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
            )}
          >
            {view.label}
          </button>
        ))}
      </div>

      {/* View Content */}
      <div className="flex-1 overflow-hidden">
        <motion.div
          key={sidebarView}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
          className="h-full"
        >
          {sidebarView === "sessions" && (
            <div className="h-full flex flex-col">
              {/* New Chat Button */}
              <div className="p-3">
                <button
                  onClick={handleNewChat}
                  disabled={isCreating}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-4 py-2",
                    "bg-white border border-slate-200 rounded-lg",
                    "text-sm font-medium text-slate-700",
                    "hover:bg-slate-50 hover:border-slate-300",
                    "transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {isCreating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  New Chat
                </button>
              </div>

              {/* Session List */}
              <div className="flex-1 overflow-y-auto">
                <SessionList />
              </div>
            </div>
          )}

          {sidebarView === "skills" && <SkillTreePanel />}

          {sidebarView === "memory" && <MemoryPanel />}

          {sidebarView === "safety" && <SafetyPanel />}

          {sidebarView === "system" && <SystemPanel />}

          {sidebarView === "settings" && <SettingsPanel />}
        </motion.div>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-200">
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-slate-100">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs text-slate-600">All systems online</span>
        </div>
      </div>
    </div>
  );
}
