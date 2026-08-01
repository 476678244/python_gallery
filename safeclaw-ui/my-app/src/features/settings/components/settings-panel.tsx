/**
 * Settings Panel - Feature Component
 *
 * Business: Model selection, UI preferences
 * Responsibility: Settings display and persistence
 */

"use client";

import { useEffect, useState } from "react";
import { Settings, Check, Loader2, Server, Wifi, WifiOff, KeyRound } from "lucide-react";
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
  deepseek: "bg-slate-900 text-white",
  "lm-studio": "bg-violet-100 text-violet-700",
};

const THEMES: { id: Theme; label: string }[] = [
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "system", label: "System" },
];

export function SettingsPanel() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [selectedModelError, setSelectedModelError] = useState<string | null>(null);
  const { theme, setTheme } = useUIStore();

  // LM Studio endpoint settings
  const [baseUrl, setBaseUrl] = useState("");
  const [reachable, setReachable] = useState<boolean | null>(null);
  const [isSavingUrl, setIsSavingUrl] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);

  // DeepSeek API key settings
  const [deepseekKey, setDeepseekKey] = useState("");
  const [deepseekConfigured, setDeepseekConfigured] = useState(false);
  const [deepseekHint, setDeepseekHint] = useState<string | null>(null);
  const [isSavingKey, setIsSavingKey] = useState(false);
  const [keyError, setKeyError] = useState<string | null>(null);

  const loadModels = async () => {
    setIsLoading(true);
    setModelsError(null);
    try {
      const r = await fetch("/api/settings/models");
      if (!r.ok) {
        throw new Error(
          `[SettingsPanel] Failed to load models\n  Status: ${r.status}`
        );
      }
      const d = await r.json();
      const list = d.models;
      if (!Array.isArray(list) || list.length === 0) {
        throw new Error(
          `[SettingsPanel] /settings/models returned empty list\n  Actual: ${JSON.stringify(d)}`
        );
      }
      setModels(list);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to load models";
      setModelsError(message);
      setModels([]);
      console.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadModels();
    void fetch("/api/settings/model")
      .then(async (r) => {
        if (!r.ok) {
          throw new Error(
            `[SettingsPanel] Failed to load selected model\n  Status: ${r.status}`
          );
        }
        const d = await r.json();
        if (typeof d.model !== "string" || !d.model.trim()) {
          throw new Error(
            `[SettingsPanel] Selected model missing\n  Actual: ${JSON.stringify(d)}`
          );
        }
        setSelectedModel(d.model.trim());
        setSelectedModelError(null);
      })
      .catch((e) => {
        const message = e instanceof Error ? e.message : "Failed to load selected model";
        setSelectedModelError(message);
        setSelectedModel(null);
        console.error(message);
      });
    fetch("/api/settings/llm")
      .then((r) => r.json())
      .then((d) => {
        setBaseUrl(d.base_url ?? "");
        setReachable(d.reachable ?? null);
      })
      .catch((e) => {
        setReachable(null);
        setUrlError(e instanceof Error ? e.message : "Failed to load LLM settings");
      });
    fetch("/api/settings/deepseek")
      .then((r) => r.json())
      .then((d) => {
        setDeepseekConfigured(d.configured ?? false);
        setDeepseekHint(d.api_key_hint ?? null);
      })
      .catch((e) => {
        setKeyError(e instanceof Error ? e.message : "Failed to load DeepSeek settings");
      });
  }, []);

  const handleSaveDeepseekKey = async () => {
    if (!deepseekKey.trim()) return;
    setIsSavingKey(true);
    setKeyError(null);
    try {
      const res = await fetch("/api/settings/deepseek", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: deepseekKey.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setKeyError(data.detail ?? "Failed to save API key");
      } else {
        setDeepseekConfigured(data.configured);
        setDeepseekHint(data.api_key_hint);
        setDeepseekKey("");
      }
    } catch (e) {
      setKeyError(e instanceof Error ? e.message : "Network error");
    } finally {
      setIsSavingKey(false);
    }
  };

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
        {modelsError && (
          <p data-testid="settings-models-error" className="text-[11px] text-red-600 whitespace-pre-wrap">
            {modelsError}
          </p>
        )}
        {selectedModelError && (
          <p data-testid="settings-selected-model-error" className="text-[11px] text-red-600 whitespace-pre-wrap">
            {selectedModelError}
          </p>
        )}
        {isLoading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
          </div>
        ) : (
          <div className="space-y-1.5">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => {
                  void (async () => {
                    setSelectedModel(model.id);
                    const res = await fetch("/api/settings/model", {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ model: model.id }),
                    });
                    if (!res.ok) {
                      const message =
                        `[SettingsPanel] Failed to persist model\n` +
                        `  Status: ${res.status}\n` +
                        `  Model: ${model.id}`;
                      setSelectedModelError(message);
                      console.error(message);
                      window.alert(message);
                      throw new Error(message);
                    }
                    setSelectedModelError(null);
                  })().catch((err) => {
                    console.error(err);
                  });
                }}
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

      {/* DeepSeek API Key */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-slate-600 uppercase tracking-wide">DeepSeek API Key</p>
          {deepseekConfigured && (
            <span className="flex items-center gap-1 text-[10px] font-medium text-green-600">
              <Check className="w-3 h-3" /> Saved {deepseekHint}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <KeyRound className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <input
            type="password"
            value={deepseekKey}
            onChange={(e) => setDeepseekKey(e.target.value)}
            placeholder={deepseekConfigured ? "Enter new key to replace" : "sk-..."}
            className="flex-1 min-w-0 px-2 py-1.5 text-xs rounded-lg border border-slate-200 focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSaveDeepseekKey}
            disabled={isSavingKey || !deepseekKey.trim()}
            className={cn(
              "px-2.5 py-1.5 text-xs font-medium rounded-lg transition-colors flex-shrink-0",
              isSavingKey || !deepseekKey.trim()
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600"
            )}
          >
            {isSavingKey ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save"}
          </button>
        </div>
        <p className="text-[10px] text-slate-400">Stored in ~/.safeclaw_secrets.json — never committed to git.</p>
        {keyError && <p className="text-[10px] text-red-500">{keyError}</p>}
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
