/**
 * Message Entity - Domain Model
 * Core business entity for chat messages
 */

export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface MessageMetadata {
  agent?: string;
  model?: string;
  processingTime?: number;
  executionPath?: string[];
  skillsUsed?: string[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  toolCalls?: ToolCall[];
  thinkingSteps?: ThinkingStep[];
}

export interface ToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
  result?: unknown;
}

export interface ThinkingStep {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "error";
  duration?: number;
  startedAt?: Date;
  completedAt?: Date;
  details?: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  sessionId?: string;
  metadata?: MessageMetadata;
  parentId?: string; // For threaded conversations
  version?: number; // For message editing
}

// Factory functions
export function createMessage(
  role: MessageRole,
  content: string,
  sessionId?: string,
  metadata?: Partial<MessageMetadata>
): Message {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: new Date(),
    sessionId,
    metadata: metadata as MessageMetadata | undefined,
  };
}

export function createUserMessage(
  content: string,
  sessionId?: string
): Message {
  return createMessage("user", content, sessionId);
}

export function createAssistantMessage(
  content: string,
  sessionId?: string,
  metadata?: Partial<MessageMetadata>
): Message {
  return createMessage("assistant", content, sessionId, metadata);
}

// Utilities
export function isStreamingMessage(message: Message): boolean {
  return message.role === "assistant" && message.content === "";
}

export function getMessageDisplayTime(message: Message): string {
  return message.timestamp.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
