/**
 * Global agent model selection — single source of truth for UI.
 * Persisted server-side in agent_config.json via /api/settings/model.
 *
 * Fail Fast: never invent a model id when the server did not provide one.
 */

import { create } from "zustand";
import { getModelById } from "@/entities/model";

interface ModelState {
  /** Globally selected model id from backend; null until first successful load. */
  globalModelId: string | null;
  loaded: boolean;
  error: string | null;
  loadGlobalModel: () => Promise<string>;
  setGlobalModel: (modelId: string) => Promise<void>;
}

function fail(context: string, detail: string): never {
  const message = `[ModelStore] ${context}\n${detail}`;
  console.error(message);
  throw new Error(message);
}

export const useModelStore = create<ModelState>((set) => ({
  globalModelId: null,
  loaded: false,
  error: null,

  loadGlobalModel: async () => {
    const res = await fetch("/api/settings/model");
    if (!res.ok) {
      const message = `Failed to load global model: HTTP ${res.status}`;
      set({ error: message, loaded: true, globalModelId: null });
      fail("loadGlobalModel", `Expected: HTTP 200 from /api/settings/model\n  Actual: ${res.status}`);
    }
    const data = await res.json();
    if (typeof data.model !== "string" || !data.model.trim()) {
      const message = "Global model missing or empty in /api/settings/model response";
      set({ error: message, loaded: true, globalModelId: null });
      fail(
        "loadGlobalModel",
        `Expected: non-empty string field "model"\n  Actual: ${JSON.stringify(data)}`
      );
    }
    const model = data.model.trim();
    if (!getModelById(model)) {
      const message = `Unknown global model id from server: ${model}`;
      set({ error: message, loaded: true, globalModelId: null });
      fail(
        "loadGlobalModel",
        `Expected: id in AVAILABLE_MODELS\n  Actual: ${model}`
      );
    }
    set({ globalModelId: model, loaded: true, error: null });
    return model;
  },

  setGlobalModel: async (modelId: string) => {
    const model = modelId.trim();
    if (!model) {
      fail("setGlobalModel", "model must not be empty");
    }
    if (!getModelById(model)) {
      fail("setGlobalModel", `Unknown model id: ${model}`);
    }
    const res = await fetch("/api/settings/model", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
    if (!res.ok) {
      const message = `Failed to persist global model: HTTP ${res.status}`;
      set({ error: message });
      fail("setGlobalModel", `PUT /api/settings/model failed\n  Status: ${res.status}\n  Model: ${model}`);
    }
    set({ globalModelId: model, loaded: true, error: null });
  },
}));

/**
 * Resolve display/chat model: session override → global.
 * Fail Fast: does not invent a product default when both are missing.
 */
export function resolveActiveModelId(
  sessionModel: string | undefined,
  globalModelId: string | null
): string {
  if (typeof sessionModel === "string" && sessionModel.trim()) {
    return sessionModel.trim();
  }
  if (typeof globalModelId === "string" && globalModelId.trim()) {
    return globalModelId.trim();
  }
  fail(
    "resolveActiveModelId",
    `No active model resolved\n` +
      `  sessionModel: ${String(sessionModel)}\n` +
      `  globalModelId: ${String(globalModelId)}\n` +
      `  Expected: session.settings.model or loaded /settings/model`
  );
}
