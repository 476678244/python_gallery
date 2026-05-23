/**
 * Model Entity - Domain Model
 * Represents AI models available in the system
 */

export type ModelProvider = "openai" | "anthropic" | "google" | "local" | "custom" | "lm-studio";
export type ModelCapability = "chat" | "vision" | "code" | "reasoning" | "function_calling" | "json_mode" | "embeddings";

export interface ModelPricing {
  inputPricePer1K: number; // USD
  outputPricePer1K: number; // USD
  currency: string;
}

export interface ModelCapabilities {
  maxTokens: number;
  contextWindow: number;
  supportedModes: ModelCapability[];
  supportsStreaming: boolean;
  supportsSystemPrompt: boolean;
}

export interface Model {
  id: string;
  name: string;
  provider: ModelProvider;
  version?: string;
  description?: string;
  icon?: string;
  capabilities: ModelCapabilities;
  pricing?: ModelPricing;
  isEnabled: boolean;
  isDefault?: boolean;
  config?: {
    baseUrl?: string;
    apiKeyRequired?: boolean;
    customHeaders?: Record<string, string>;
  };
}

// Predefined models — IDs must match backend /settings/models and sidebar SIDEBAR_MODELS
export const AVAILABLE_MODELS: Model[] = [
  {
    id: "qwen3.5-9b-vlm",
    name: "Qwen3.5 9B",
    provider: "lm-studio",
    description: "Currently loaded · 9B · Q4_K_M · Context 262144",
    icon: "qwen",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 262144,
      supportedModes: ["chat", "vision", "code", "reasoning", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
    isDefault: true,
  },
  {
    id: "gemma-4-e4b",
    name: "Gemma 4 E4B",
    provider: "lm-studio",
    description: "Google · 7.5B · Q6_K · 6.71 GB",
    icon: "gemma",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "gemma-4-31b",
    name: "Gemma 4 31B",
    provider: "lm-studio",
    description: "Google · 31B · Q4_K_M · 18.52 GB",
    icon: "gemma",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "qwen3.6-27b",
    name: "Qwen3.6 27B",
    provider: "lm-studio",
    description: "Qwen · 27B · Q4_K_M · 16.28 GB",
    icon: "qwen",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "reasoning", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "qwen/qwen3.5-35b-a3b",
    name: "Qwen3.5 35B A3B",
    provider: "lm-studio",
    description: "Qwen · 35B-A3B · Q4_K_M · 20.56 GB",
    icon: "qwen",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "reasoning", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "nomic-embed-text-v1.5",
    name: "Nomic Embed v1.5",
    provider: "lm-studio",
    description: "nomic-ai · Embedding · Q4_K_M · 80.21 MB",
    icon: "nomic",
    capabilities: {
      maxTokens: 8192,
      contextWindow: 8192,
      supportedModes: ["embeddings"],
      supportsStreaming: false,
      supportsSystemPrompt: false,
    },
    isEnabled: false,
  },
];

// Utilities
export function getDefaultModel(): Model {
  return AVAILABLE_MODELS.find((m) => m.isDefault) || AVAILABLE_MODELS[0];
}

export function getModelById(id: string): Model | undefined {
  return AVAILABLE_MODELS.find((m) => m.id === id);
}

export function getEnabledModels(): Model[] {
  return AVAILABLE_MODELS.filter((m) => m.isEnabled);
}

export function supportsCapability(model: Model, capability: ModelCapability): boolean {
  return model.capabilities.supportedModes.includes(capability);
}
