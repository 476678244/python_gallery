/**
 * Chat Workspace - Feature Root
 * 
 * The main application container that composes all features:
 * - Sidebar (sessions, skills, workspace)
 * - Chat Interface (messages, input, streaming)
 * - Right Panel (execution graph, context)
 * 
 * This is the composition root - no business logic here,
 * just feature composition.
 */

"use client";

import { useEffect } from "react";
import { useUIStore } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { useSkillStore } from "@/stores/skill-store";
import { Sidebar } from "@/features/sidebar/components/sidebar";
import { ChatContainer } from "@/features/chat/components/chat-container";
import { RightPanel } from "@/features/agent/components/right-panel";
import { cn } from "@/shared/utils/cn";

export function ChatWorkspace() {
  // Initialize data on mount
  useEffect(() => {
    useSessionStore.getState().loadSessions();
    useSkillStore.getState().loadSkills();
  }, []);

  // UI state
  const { sidebarOpen, rightPanelOpen } = useUIStore();

  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden">
      {/* Left Sidebar - Sessions & Skills */}
      <aside
        className={cn(
          "flex-shrink-0 transition-all duration-300 ease-in-out",
          sidebarOpen ? "w-64 opacity-100" : "w-0 opacity-0 overflow-hidden"
        )}
      >
        <Sidebar />
      </aside>

      {/* Center - Chat Interface */}
      <main className="flex-1 flex flex-col min-w-0">
        <ChatContainer />
      </main>

      {/* Right Panel - Execution & Context */}
      <aside
        className={cn(
          "flex-shrink-0 transition-all duration-300 ease-in-out",
          rightPanelOpen ? "w-80 opacity-100" : "w-0 opacity-0 overflow-hidden"
        )}
      >
        <RightPanel />
      </aside>
    </div>
  );
}
