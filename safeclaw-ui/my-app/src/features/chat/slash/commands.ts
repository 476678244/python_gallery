/**
 * Slash command registry — single source of truth for chat input `/` commands.
 */

export type SlashPickerMode = "model" | "skill";
export type SlashMode = "command" | "help" | SlashPickerMode | null;

export interface SlashCommandDef {
  id: string;
  name: string;
  description: string;
  /** picker: opens a list; action: runs on select; help: shows full command list */
  kind: "picker" | "action" | "help";
  aliases?: string[];
  /** When true, action accepts trailing text args (e.g. /remember …) */
  acceptsArgs?: boolean;
}

export const SLASH_COMMANDS: SlashCommandDef[] = [
  {
    id: "help",
    name: "help",
    description: "List available slash commands",
    kind: "help",
    aliases: ["?"],
  },
  {
    id: "model",
    name: "model",
    description: "Switch AI model for this session",
    kind: "picker",
  },
  {
    id: "skill",
    name: "skill",
    description: "Browse and insert an enabled skill",
    kind: "picker",
  },
  {
    id: "remember",
    name: "remember",
    description: "Save text into long-term memory",
    kind: "action",
    acceptsArgs: true,
  },
  {
    id: "memory",
    name: "memory",
    description: "Open memory panel or search memories",
    kind: "action",
    acceptsArgs: true,
  },
  {
    id: "clear",
    name: "clear",
    description: "Clear messages in the current chat",
    kind: "action",
  },
  {
    id: "new",
    name: "new",
    description: "Start a new chat session",
    kind: "action",
  },
];

export function filterCommands(prefix: string): SlashCommandDef[] {
  const p = prefix.toLowerCase().trim();
  if (!p) return [...SLASH_COMMANDS];
  return SLASH_COMMANDS.filter(
    (c) =>
      c.name.startsWith(p) ||
      (c.aliases ?? []).some((a) => a.startsWith(p) || a === p) ||
      c.description.toLowerCase().includes(p)
  );
}

export function findCommand(nameOrAlias: string): SlashCommandDef | undefined {
  const key = nameOrAlias.toLowerCase();
  return SLASH_COMMANDS.find(
    (c) => c.name === key || (c.aliases ?? []).includes(key)
  );
}

/**
 * Parse text after `/` into slash UI mode + filter.
 * - `/` or `/he` → command palette
 * - `/help` → full help list
 * - `/model flash` → model picker
 * - `/skill pdf` → skill picker
 * - `/remember text` → action with args
 * - `/pdf` (no reserved command) → legacy bare skill autocomplete
 */
export function parseSlashCommand(afterSlash: string): {
  mode: SlashMode;
  filter: string;
  commandId?: string;
  args?: string;
} {
  const raw = afterSlash;
  const lower = raw.toLowerCase();

  if (lower.includes("\n")) {
    return { mode: null, filter: "" };
  }

  // Named command with optional args: /model, /model x, /model:x, /?
  for (const cmd of SLASH_COMMANDS) {
    const names = [cmd.name, ...(cmd.aliases ?? [])];
    for (const n of names) {
      const exact = lower === n;
      const spaced = lower.startsWith(`${n} `);
      const colon = lower.startsWith(`${n}:`);
      if (!exact && !spaced && !colon) continue;

      const args = colon
        ? raw.slice(n.length + 1)
        : spaced
          ? raw.slice(n.length).trimStart()
          : "";

      if (cmd.kind === "help") {
        return { mode: "help", filter: "", commandId: cmd.id, args: "" };
      }
      if (cmd.kind === "picker") {
        return {
          mode: cmd.id as SlashPickerMode,
          filter: args,
          commandId: cmd.id,
          args,
        };
      }
      // action: palette focused on command name; args carried separately
      return {
        mode: "command",
        filter: cmd.name,
        commandId: cmd.id,
        args,
      };
    }
  }

  // Partial / empty token → command palette (discovery)
  if (!lower.includes(" ")) {
    const matching = filterCommands(lower);
    if (lower === "" || matching.length > 0) {
      return { mode: "command", filter: lower };
    }
    // Legacy: bare skill name after /
    return { mode: "skill", filter: lower };
  }

  return { mode: null, filter: "" };
}
