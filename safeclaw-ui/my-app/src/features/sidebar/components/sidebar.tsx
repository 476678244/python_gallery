/**
 * Sidebar Feature Component
 * 
 * Business: Session management, Skill tree, Workspace navigation
 * Responsibility: Compose sidebar sub-features
 */

"use client";

import { useState } from "react";
import { ChevronDown, Plus, Shield, Loader2, Cpu } from "lucide-react";
import { useSessionStore } from "@/stores/session-store";
import { SessionList } from "./session-list";
import { SkillTreePanel } from "@/features/skills/components/skill-tree-panel";
import { cn } from "@/shared/utils/cn";

// ── Collapsible Section wrapper ───────────────────────────────────
function SbSection({
  icon,
  title,
  badge,
  defaultOpen = true,
  children,
}: {
  icon: string;
  title: string;
  badge?: string | number;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-slate-200">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3.5 py-2.5 sticky top-0 bg-white z-10 hover:bg-slate-50 transition-colors"
      >
        <span className="text-sm w-4 text-center flex-shrink-0">{icon}</span>
        <span className="flex-1 text-left text-[11.5px] font-bold uppercase tracking-[0.4px] text-slate-500">
          {title}
        </span>
        {badge !== undefined && (
          <span className="text-[10px] font-semibold px-1.5 py-px rounded-full bg-slate-200 text-slate-500">
            {badge}
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-3 h-3 text-slate-400 flex-shrink-0 transition-transform duration-200",
            !open && "-rotate-90"
          )}
        />
      </button>
      {open && <div>{children}</div>}
    </div>
  );
}

// ── Model card ────────────────────────────────────────────────────
const SIDEBAR_MODELS = [
  { id: "qwen3.5-9b-vlm",       name: "Qwen3.5 9B",      sub: "9B · Q4_K_M · Loaded" },
  { id: "gemma-4-e4b",          name: "Gemma 4 E4B",     sub: "7.5B · Q6_K · 6.71 GB" },
  { id: "gemma-4-31b",          name: "Gemma 4 31B",     sub: "31B · Q4_K_M · 18.52 GB" },
  { id: "qwen3.6-27b",          name: "Qwen3.6 27B",     sub: "27B · Q4_K_M · 16.28 GB" },
  { id: "qwen/qwen3.5-35b-a3b", name: "Qwen3.5 35B A3B", sub: "35B-A3B · Q4_K_M · 20.56 GB" },
];

function ModelSection() {
  const { currentSessionId, sessions, updateSessionSettings } = useSessionStore();
  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const selectedModel = currentSession?.settings?.model ?? "qwen3.5-9b-vlm";

  const handleSelect = (modelId: string) => {
    if (currentSessionId) {
      updateSessionSettings(currentSessionId, { model: modelId });
    }
  };

  return (
    <div className="p-2 space-y-1">
      {SIDEBAR_MODELS.map((m) => (
        <button
          key={m.id}
          onClick={() => handleSelect(m.id)}
          className={cn(
            "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all",
            selectedModel === m.id
              ? "bg-blue-50 border border-blue-200"
              : "hover:bg-slate-50 border border-transparent"
          )}
        >
          <Cpu className={cn("w-4 h-4 flex-shrink-0", selectedModel === m.id ? "text-blue-500" : "text-slate-400")} />
          <div className="flex-1 min-w-0">
            <p className={cn("text-xs font-semibold truncate", selectedModel === m.id ? "text-blue-700" : "text-slate-700")}>
              {m.name}
            </p>
            <p className="text-[10px] text-slate-400">{m.sub}</p>
          </div>
          {selectedModel === m.id && (
            <span className="text-[10px] font-bold text-blue-500">✓</span>
          )}
        </button>
      ))}
    </div>
  );
}

// ── Tool Tree (static mock) ───────────────────────────────────────
function ToolTreeSection() {
  const tools = [
    { folder: "Built-in", items: ["web_search", "read_file", "write_file"] },
    { folder: "Custom",   items: ["market_data", "price_tracker"] },
  ];
  const [openFolders, setOpenFolders] = useState<Record<string, boolean>>({ "Built-in": true, "Custom": false });

  return (
    <div className="p-2 space-y-0.5">
      {tools.map((t) => (
        <div key={t.folder}>
          <button
            onClick={() => setOpenFolders((s) => ({ ...s, [t.folder]: !s[t.folder] }))}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 transition-colors"
          >
            <span className="text-xs">{openFolders[t.folder] ? "📂" : "📁"}</span>
            <span className="flex-1 text-xs font-medium text-slate-600 text-left">{t.folder}</span>
            <ChevronDown className={cn("w-3 h-3 text-slate-400 transition-transform", !openFolders[t.folder] && "-rotate-90")} />
          </button>
          {openFolders[t.folder] && (
            <div className="ml-4 space-y-0.5">
              {t.items.map((item) => (
                <div key={item} className="flex items-center gap-2 px-2 py-1 rounded text-xs text-slate-500 hover:bg-slate-50">
                  <span className="text-[10px]">🔧</span>
                  {item}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main Sidebar ──────────────────────────────────────────────────
export function Sidebar() {
  const { createSession, isCreating, sessions } = useSessionStore();

  return (
    <div className="h-full flex flex-col bg-white border-r border-slate-200">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-slate-200 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold text-slate-900 text-sm">SafeClaw</span>
      </div>

      {/* Scrollable sections */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">

        {/* ① Chats */}
        <SbSection icon="💬" title="Chats" badge={sessions.length} defaultOpen={true}>
          <div className="px-3 py-2">
            <button
              onClick={() => createSession("New Chat")}
              disabled={isCreating}
              className={cn(
                "w-full flex items-center justify-center gap-1.5 py-1.5 px-3",
                "border border-dashed border-slate-300 rounded-lg",
                "text-xs font-medium text-slate-500",
                "hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50",
                "transition-all disabled:opacity-50"
              )}
            >
              {isCreating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              New Chat
            </button>
          </div>
          <SessionList />
        </SbSection>

        {/* ② Skill Tree */}
        <SbSection icon="🛠" title="Skill Tree" defaultOpen={true}>
          <SkillTreePanel />
        </SbSection>

        {/* ③ Tool Tree */}
        <SbSection icon="🔧" title="Tool Tree" defaultOpen={false}>
          <ToolTreeSection />
        </SbSection>

        {/* ④ Model */}
        <SbSection icon="🤖" title="Model" defaultOpen={false}>
          <ModelSection />
        </SbSection>

      </div>

      {/* Footer */}
      <div className="flex items-center gap-2.5 px-3.5 py-2.5 border-t border-slate-200 flex-shrink-0">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
          <span className="text-[10px] font-bold text-white">N</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-800 truncate">Nicole</p>
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
            <span className="text-[10px] text-slate-400">All systems online</span>
          </div>
        </div>
      </div>
    </div>
  );
}
