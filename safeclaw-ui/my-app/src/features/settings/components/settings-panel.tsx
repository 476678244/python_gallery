/**
 * Settings Panel - Feature Component
 *
 * Business: Model selection, UI preferences
 * Responsibility: Settings display and persistence
 */

"use client";

import { useEffect, useState } from "react";
import { Settings, Check, Loader2 } from "lucide-react";
import { useUIStore, Theme } from "@/stores/ui-store";
import { cn } from "@/shared/utils/cn";

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
}

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: "bg-orange-100 text-orange-700",
  openai: "bg-green-100 text-green-700",
  qwen: "bg-blue-100 text-blue-700",
  google: "bg-red-100 text-red-700",
};

const THEMES: { id: Theme; label: string }[] = [
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "system", label: "System" },
];

export function SettingsPanel() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("qwen/qwen3.5-35b-a3b");
  const [isLoading, setIsLoading] = useState(false);
  const { theme, setTheme } = useUIStore();

  useEffect(() => {
    setIsLoading(true);
    fetch("/api/settings/models")
      .then((r) => r.json())
      .then((d) => setModels(d.models ?? []))
      .catch(() => setModels([]))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="h-full flex flex-col gap-4 p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Settings className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-700">Settings</span>
      </div>

      {/* Model Selection */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-slate-600 uppercase tracking-wide">LLM Model</p>
        {isLoading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
          </div>
        ) : (
          <div className="space-y-1.5">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model.id)}
                className={cn(
                  "w-full flex items-center justify-between p-2.5 rounded-lg border text-left transition-colors",
                  selectedModel === model.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 hover:bg-slate-50"
                )}
              >
                <div className="flex items-center gap-2">
                  <span className={cn("px-1.5 py-0.5 rounded text-xs font-medium", PROVIDER_COLORS[model.provider] ?? "bg-slate-100 text-slate-600")}>
                    {model.provider}
                  </span>
                  <span className="text-xs text-slate-700">{model.name}</span>
                </div>
                {selectedModel === model.id && (
                  <Check className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Theme */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-slate-600 uppercase tracking-wide">Theme</p>
        <div className="flex gap-2">
          {THEMES.map((t) => (
            <button
              key={t.id}
              onClick={() => setTheme(t.id)}
              className={cn(
                "flex-1 py-2 text-xs font-medium rounded-lg border transition-colors",
                theme === t.id
                  ? "border-blue-500 bg-blue-50 text-blue-600"
                  : "border-slate-200 text-slate-500 hover:bg-slate-50"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* About */}
      <div className="mt-auto pt-4 border-t border-slate-200 space-y-1">
        <p className="text-xs text-slate-400">SafeClaw Agent Workspace</p>
        <p className="text-xs text-slate-400">Version 1.0.0</p>
      </div>
    </div>
  );
}
