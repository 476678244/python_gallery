/**
 * Session Entity - Domain Model
 * Represents a chat conversation session
 */

import { Message } from "@/entities/message";
import type { AgentMode } from "@/entities/agent-mode";
import { DEFAULT_AGENT_MODE } from "@/entities/agent-mode";

export type SessionStatus = "active" | "archived" | "deleted";

export interface SessionSettings {
  model?: string;
  enabledSkills?: string[];
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  /** Session-sticky agent mode (ask|agent|plan|safe|debug|subagent|ppt). */
  mode?: AgentMode;
}

export interface Session {
  id: string;
  title: string;
  status: SessionStatus;
  messageCount: number;
  settings: SessionSettings;
  createdAt: Date;
  updatedAt: Date;
  lastActivityAt: Date;
  workspaceId?: string;
  tags?: string[];
}

// Factory functions
export function createSession(
  title: string = "New Chat",
  settings: Partial<SessionSettings> = {}
): Session {
  if (!settings.model?.trim()) {
    throw new Error(
      "[createSession] settings.model is required (Fail Fast)\n" +
        "  Do not invent a local default — pass the global selected model."
    );
  }
  const now = new Date();
  return {
    id: crypto.randomUUID(),
    title,
    status: "active",
    messageCount: 0,
    settings: {
      model: settings.model.trim(),
      enabledSkills: [],
      temperature: 0.7,
      maxTokens: 4096,
      mode: DEFAULT_AGENT_MODE,
      ...settings,
    },
    createdAt: now,
    updatedAt: now,
    lastActivityAt: now,
  };
}

export function updateSessionActivity(session: Session): Session {
  return {
    ...session,
    lastActivityAt: new Date(),
    updatedAt: new Date(),
  };
}

export function incrementMessageCount(session: Session): Session {
  return {
    ...session,
    messageCount: session.messageCount + 1,
    lastActivityAt: new Date(),
    updatedAt: new Date(),
  };
}

export function archiveSession(session: Session): Session {
  return {
    ...session,
    status: "archived",
    updatedAt: new Date(),
  };
}

// Utilities
export function getSessionDisplayTitle(session: Session): string {
  if (session.title && session.title !== "New Chat") {
    return session.title;
  }
  return "Untitled Chat";
}

export function formatSessionTime(session: Session): string {
  const now = new Date();
  const raw = session.lastActivityAt;
  if (!raw) return "";
  const lastActivity = raw instanceof Date ? raw : new Date(raw);
  if (isNaN(lastActivity.getTime())) return "";
  const diffMs = now.getTime() - lastActivity.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return (lastActivity instanceof Date ? lastActivity : new Date(lastActivity)).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}
