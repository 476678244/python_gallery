/**
 * Chat Header - Feature Component
 *
 * Business: Session title, model selection, web search toggle
 * Responsibility: Header UI and controls
 */

"use client";

import { useState, useEffect } from "react";
import { Session } from "@/entities/session";
import { AVAILABLE_MODELS, getEnabledModels, getModelById, Model } from "@/entities/model";
import { useSessionStore } from "@/stores/session-store";
import { useModelStore, resolveActiveModelId } from "@/stores/model-store";
import { useUIStore } from "@/stores/ui-store";
import { Globe, PanelRight, ChevronDown } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface ChatHeaderProps {
  session?: Session;
  messageCount: number;
}

export function ChatHeader({ session, messageCount }: ChatHeaderProps) {
  const { updateSessionSettings } = useSessionStore();
  const { globalModelId, loadGlobalModel, setGlobalModel, loaded, error } = useModelStore();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    void loadGlobalModel().catch((err) => {
      console.error("[ChatHeader] Failed to load global model", err);
    });
  }, [loadGlobalModel]);

  // Safe store access - use default values during SSR/hydration
  const { openPanelKeys, railToggle } = useUIStore();
  const safeOpenPanelKeys = mounted ? openPanelKeys : [];
  const rightPanelOpen = safeOpenPanelKeys.some((k) => !k.startsWith("!"));

  const handleModelChange = async (model: Model) => {
    if (session) {
      updateSessionSettings(session.id, { model: model.id });
    }
    await setGlobalModel(model.id);
  };

  let modelControl: React.ReactNode;
  if (error) {
    modelControl = (
      <span data-testid="header-model-error" className="text-xs text-red-600 max-w-[220px] truncate" title={error}>
        Model error
      </span>
    );
  } else if (!loaded || !globalModelId) {
    modelControl = (
      <span className="text-xs text-slate-400">Loading model…</span>
    );
  } else {
    const activeModelId = resolveActiveModelId(session?.settings?.model, globalModelId);
    const currentModel = getModelById(activeModelId);
    if (!currentModel) {
      throw new Error(
        `[ChatHeader] Unknown model id\n` +
          `  Actual: ${activeModelId}\n` +
          `  Expected: id in AVAILABLE_MODELS`
      );
    }
    modelControl = (
      <div className="relative">
        <select
          data-testid="header-model-select"
          value={currentModel.id}
          onChange={(e) => {
            const model = AVAILABLE_MODELS.find((m) => m.id === e.target.value);
            if (!model) {
              throw new Error(
                `[ChatHeader] Selected unknown model\n  Actual: ${e.target.value}`
              );
            }
            void handleModelChange(model).catch((err) => {
              console.error("[ChatHeader] Failed to change model", err);
              window.alert(err instanceof Error ? err.message : "Failed to change model");
            });
          }}
          className={cn(
            "appearance-none pl-3 pr-8 py-1.5 text-sm rounded-lg",
            "bg-slate-100 text-slate-700",
            "hover:bg-slate-200 transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          )}
        >
          {getEnabledModels().map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
      </div>
    );
  }

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white">
      {/* Left - Session Info */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="font-semibold text-slate-900">
            {mounted ? (session?.title || "New Chat") : "New Chat"}
          </h1>
          <p className="text-xs text-slate-500">
            {messageCount} {messageCount === 1 ? "message" : "messages"}
          </p>
        </div>
      </div>

      {/* Right - Controls */}
      <div className="flex items-center gap-3">
        {modelControl}

        {/* Web Search Toggle */}
        <button
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm",
            "transition-colors",
            "bg-slate-100 text-slate-600 hover:bg-slate-200"
          )}
        >
          <Globe className="w-4 h-4" />
          <span>Web</span>
        </button>

        {/* Right Panel Toggle */}
        <button
          onClick={() => railToggle("exec")}
          className={cn(
            "p-2 rounded-lg transition-colors",
            rightPanelOpen
              ? "bg-blue-100 text-blue-600"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          )}
        >
          <PanelRight className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
