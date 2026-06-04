/**
 * Settings Panel - Feature Component
 *
 * Business: Model selection, UI preferences
 * Responsibility: Settings display and persistence
 */

"use client";

import { useEffect, useState } from "react";
import { Settings, Check, Loader2, Server, Wifi, WifiOff } from "lucide-react";
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

  // LM Studio endpoint settings
  const [baseUrl, setBaseUrl] = useState("");
  const [reachable, setReachable] = useState<boolean | null>(null);
  const [isSavingUrl, setIsSavingUrl] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);

  const loadModels = () => {
    setIsLoading(true);
    fetch("/api/settings/models")
      .then((r) => r.json())
      .then((d) => setModels(d.models ?? []))
      .catch(() => setModels([]))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadModels();
    fetch("/api/settings/llm")
      .then((r) => r.json())
      .then((d) => {
        setBaseUrl(d.base_url ?? "");
        setReachable(d.reachable ?? null);
      })
      .catch(() => setReachable(null));
  }, []);

  const handleSaveUrl = async () => {
    setIsSavingUrl(true);
    setUrlError(null);
    try {
      const res = await fetch("/api/settings/llm", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: baseUrl.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setUrlError(data.detail ?? "Failed to update endpoint");
        setReachable(false);
      } else {
        setBaseUrl(data.base_url ?? baseUrl);
        setReachable(data.reachable ?? false);
        if (data.error) setUrlError(data.error);
        loadModels();
      }
    } catch (e) {
      setUrlError(e instanceof Error ? e.message : "Network error");
      setReachable(false);
    } finally {
      setIsSavingUrl(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-4 p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Settings className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-700">Settings</span>
      </div>

      {/* LM Studio Endpoint */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-slate-600 uppercase tracking-wide">LM Studio Endpoint</p>
          {reachable === true && (
            <span className="flex items-center gap-1 text-[10px] font-medium text-green-600">
              <Wifi className="w-3 h-3" /> Connected
            </span>
          )}
          {reachable === false && (
            <span className="flex items-center gap-1 text-[10px] font-medium text-red-500">
              <WifiOff className="w-3 h-3" /> Unreachable
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="http://192.168.1.100:1234/v1"
            className="flex-1 min-w-0 px-2 py-1.5 text-xs rounded-lg border border-slate-200 focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSaveUrl}
            disabled={isSavingUrl || !baseUrl.trim()}
            className={cn(
              "px-2.5 py-1.5 text-xs font-medium rounded-lg transition-colors flex-shrink-0",
              isSavingUrl || !baseUrl.trim()
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600"
            )}
          >
            {isSavingUrl ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save"}
          </button>
        </div>
        {urlError && <p className="text-[10px] text-red-500">{urlError}</p>}
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
