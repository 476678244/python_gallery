/**
 * Sidebar Feature Component
 *
 * Business: Session management, Skill tree, Workspace navigation
 * Responsibility: Compose sidebar sub-features
 */

"use client";

import { useState, useEffect } from "react";
import { ChevronDown, Plus, Shield, Loader2, Cpu } from "lucide-react";
import { useSessionStore } from "@/stores/session-store";
import { useModelStore, resolveActiveModelId } from "@/stores/model-store";
import { SessionList } from "./session-list";
import { SkillTreePanel } from "@/features/skills/components/skill-tree-panel";
import { AVAILABLE_MODELS } from "@/entities/model";
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
    <div className="border-b border-slate-100">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 px-3 py-2.5 hover:bg-slate-50 transition-colors"
      >
        <span className="text-sm">{icon}</span>
        <span className="flex-1 text-left text-xs font-semibold text-slate-600 uppercase tracking-wide">
          {title}
        </span>
        {badge !== undefined && (
          <span className="text-[10px] font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
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

// ── Model card (derived from the single source of truth) ─────────
const SIDEBAR_MODELS = AVAILABLE_MODELS
  .filter((m) => m.isEnabled)
  .map((m) => ({ id: m.id, name: m.name, sub: m.description ?? "" }));

function ModelSection() {
  const { currentSessionId, sessions, updateSessionSettings } = useSessionStore();
  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const { globalModelId, loadGlobalModel, setGlobalModel, loaded, error } = useModelStore();

  useEffect(() => {
    void loadGlobalModel().catch((err) => {
      console.error("[ModelSection] Failed to load global model", err);
    });
  }, [loadGlobalModel]);

  if (error) {
    return (
      <p data-testid="model-load-error" className="px-3 py-2 text-[11px] text-red-600 whitespace-pre-wrap">
        {error}
      </p>
    );
  }
  if (!loaded || !globalModelId) {
    return (
      <p className="px-3 py-2 text-[11px] text-slate-400">Loading global model…</p>
    );
  }

  const selectedModel = resolveActiveModelId(
    currentSession?.settings?.model,
    globalModelId
  );

  const handleSelect = async (modelId: string) => {
    if (currentSessionId) {
      updateSessionSettings(currentSessionId, { model: modelId });
    }
    await setGlobalModel(modelId);
  };

  return (
    <div className="p-2 space-y-1">
      {SIDEBAR_MODELS.map((m) => (
        <button
          key={m.id}
          onClick={() => {
            void handleSelect(m.id).catch((err) => {
              console.error("[ModelSection] Failed to select model", err);
              window.alert(err instanceof Error ? err.message : "Failed to select model");
            });
          }}
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
  const { loadGlobalModel } = useModelStore();

  const handleNewChat = async () => {
    // Fail Fast: refuse New Chat if global model cannot be loaded.
    const model = await loadGlobalModel();
    await createSession("New Chat", model);
  };

  return (
    <div data-testid="sidebar" className="h-full flex flex-col bg-white border-r border-slate-200">
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
              onClick={() => {
                void handleNewChat().catch((err) => {
                  console.error("[Sidebar] New Chat failed (Fail Fast)", err);
                  window.alert(
                    err instanceof Error
                      ? err.message
                      : "[Sidebar] New Chat failed: unknown error"
                  );
                });
              }}
              disabled={isCreating}
              data-testid="new-chat-button"
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
