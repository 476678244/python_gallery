/**
 * Agent execution mode — session sticky (≠ SlashMode palette).
 * SoT: docs/features/agent-modes/methodology.md + ppt-mode
 */

export type AgentMode =
  | "ask"
  | "agent"
  | "plan"
  | "safe"
  | "debug"
  | "subagent"
  | "ppt";

export const AGENT_MODES: AgentMode[] = [
  "ask",
  "agent",
  "plan",
  "safe",
  "debug",
  "subagent",
  "ppt",
];

export const DEFAULT_AGENT_MODE: AgentMode = "agent";

export function isAgentMode(value: unknown): value is AgentMode {
  return typeof value === "string" && (AGENT_MODES as string[]).includes(value);
}

export function parseAgentMode(value: unknown): AgentMode {
  if (isAgentMode(value)) return value;
  return DEFAULT_AGENT_MODE;
}

/** Policy chips for UI (create / update / delete). */
export function modeWriteChips(mode: AgentMode): {
  create: boolean;
  update: boolean;
  delete: boolean;
  observability: "default" | "full" | "subagent" | "ppt";
} {
  switch (mode) {
    case "ask":
    case "plan":
      return { create: false, update: false, delete: false, observability: "default" };
    case "safe":
      return { create: true, update: false, delete: false, observability: "default" };
    case "ppt":
      return { create: true, update: false, delete: false, observability: "ppt" };
    case "debug":
      return { create: true, update: true, delete: true, observability: "full" };
    case "subagent":
      return { create: true, update: true, delete: true, observability: "subagent" };
    case "agent":
    default:
      return { create: true, update: true, delete: true, observability: "default" };
  }
}
