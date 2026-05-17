/**
 * Model Entity - Domain Model
 * Represents AI models available in the system
 */

export type ModelProvider = "openai" | "anthropic" | "google" | "local" | "custom";
export type ModelCapability = "chat" | "vision" | "code" | "reasoning" | "function_calling" | "json_mode";

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
    id: "qwen/qwen3.5-35b-a3b",
    name: "Qwen 3.5",
    provider: "lm-studio",
    description: "Powerful local model for complex reasoning",
    icon: "qwen",
    capabilities: {
      maxTokens: 32768,
      contextWindow: 128000,
      supportedModes: ["chat", "vision", "code", "reasoning", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
    isDefault: true,
  },
  {
    id: "gemma-4b",
    name: "Gemma 4B",
    provider: "lm-studio",
    description: "Fast and efficient for most tasks",
    icon: "gemma",
    capabilities: {
      maxTokens: 8192,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "openai",
    description: "OpenAI cloud model",
    icon: "openai",
    capabilities: {
      maxTokens: 4096,
      contextWindow: 128000,
      supportedModes: ["chat", "code", "function_calling", "json_mode"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
  },
  {
    id: "claude-opus-4-7",
    name: "Claude Opus",
    provider: "anthropic",
    description: "Anthropic cloud model",
    icon: "anthropic",
    capabilities: {
      maxTokens: 8192,
      contextWindow: 200000,
      supportedModes: ["chat", "code", "reasoning", "function_calling"],
      supportsStreaming: true,
      supportsSystemPrompt: true,
    },
    isEnabled: true,
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
