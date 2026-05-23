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

import { useEffect, useState } from "react";
import { useUIStore } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { useSkillStore } from "@/stores/skill-store";
import { Sidebar } from "@/features/sidebar/components/sidebar";
import { ChatContainer } from "@/features/chat/components/chat-container";
import { RightPanel } from "@/components/right-panel";
import { cn } from "@/shared/utils/cn";

export function ChatWorkspace() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    useSessionStore.getState().loadSessions();
    useSkillStore.getState().loadSkills();
  }, []);

  // Safe access to store - use getState to avoid hook issues during initialization
  const [sidebarOpen, setSidebarOpenState] = useState(true);

  useEffect(() => {
    // Subscribe to store changes after mount
    const unsub = useUIStore.subscribe((state) => {
      if (state && state.sidebarOpen !== undefined) {
        setSidebarOpenState(state.sidebarOpen);
      }
    });
    // Set initial value safely
    const initialState = useUIStore.getState();
    if (initialState && initialState.sidebarOpen !== undefined) {
      setSidebarOpenState(initialState.sidebarOpen);
    }
    return unsub;
  }, []);

  // Prevent hydration mismatch - render neutral state until mounted
  if (!mounted) {
    return (
      <div className="flex h-screen w-full bg-slate-50 overflow-hidden">
        <aside className="flex-shrink-0 w-64">
          <div className="h-full bg-white border-r border-slate-200" />
        </aside>
        <main className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 bg-slate-50" />
        </main>
        <div className="w-11 bg-slate-50 border-l border-slate-200" />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden">
      {/* Left Sidebar */}
      <aside
        className={cn(
          "flex-shrink-0 transition-all duration-300 ease-in-out",
          sidebarOpen ? "w-64 opacity-100" : "w-0 opacity-0 overflow-hidden"
        )}
      >
        <Sidebar />
      </aside>

      {/* Center - Chat */}
      <main className="flex-1 flex flex-col min-w-0">
        <ChatContainer />
      </main>

      {/* Right - Icon rail + accordion panels (self-contained) */}
      <RightPanel />
    </div>
  );
}
