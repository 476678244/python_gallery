/**
 * Parse /ppt Deck Outline structured reply.
 * SoT: docs/features/ppt-mode/methodology.md §7
 *
 * Headings may include a suffix (LLM often writes
 * `### Deck Outline（共 6 页）`); match by prefix, not exact line.
 */

export interface DeckArtifact {
  outline: string[];
  storyboard: string[];
  pending: string[];
  intro: string;
}

// `m`: look across full message (intro may precede headings).
// `\b`: allow LLM suffixes e.g. `### Deck Outline（共 6 页）`.
const OUTLINE_RE = /^###\s*Deck Outline\b/im;
const STORYBOARD_RE = /^###\s*Slide Storyboard\b/im;
const PENDING_RE = /^###\s*Pending confirmation\b/im;

export function looksLikeDeckArtifact(content: string): boolean {
  if (!content || !content.trim()) return false;
  return OUTLINE_RE.test(content);
}

function storyboardLine(trimmed: string): string | null {
  // Markdown table row: | 1 | title | bullets | visual |
  if (trimmed.startsWith("|")) {
    if (/^\|\s*-+/.test(trimmed)) return null; // separator
    const cells = trimmed
      .split("|")
      .map((c) => c.trim())
      .filter(Boolean);
    if (cells.length < 2) return null;
    // drop leading index-only noise; keep title + rest
    return cells.join(" · ");
  }
  const bullet = trimmed.replace(/^[-*]\s+/, "").replace(/^\d+[.)]\s+/, "");
  return bullet || null;
}

/**
 * Extract Deck Outline / Slide Storyboard / Pending confirmation.
 * Fail Fast: null if ### Deck Outline missing or empty outline+storyboard.
 */
export function parseDeckArtifact(content: string): DeckArtifact | null {
  if (!looksLikeDeckArtifact(content)) return null;

  const lines = content.replace(/\r\n/g, "\n").split("\n");
  let section: "intro" | "outline" | "storyboard" | "pending" = "intro";
  const intro: string[] = [];
  const outline: string[] = [];
  const storyboard: string[] = [];
  const pending: string[] = [];

  for (const raw of lines) {
    if (OUTLINE_RE.test(raw)) {
      section = "outline";
      continue;
    }
    if (STORYBOARD_RE.test(raw)) {
      section = "storyboard";
      continue;
    }
    if (PENDING_RE.test(raw)) {
      section = "pending";
      continue;
    }
    if (/^###\s+/.test(raw)) continue;

    const trimmed = raw.trim();
    if (!trimmed || trimmed === "---") continue;

    if (section === "intro") {
      intro.push(trimmed);
      continue;
    }

    if (section === "outline") {
      const bullet = trimmed.replace(/^[-*]\s+/, "").replace(/^\d+[.)]\s+/, "");
      // skip bold-only empties
      if (bullet) outline.push(bullet);
      continue;
    }
    if (section === "storyboard") {
      const line = storyboardLine(trimmed);
      if (line) storyboard.push(line);
      continue;
    }
    if (section === "pending") {
      const bullet = trimmed.replace(/^[-*]\s+/, "").replace(/^\d+[.)]\s+/, "");
      if (bullet) pending.push(bullet);
    }
  }

  if (outline.length === 0 && storyboard.length === 0) return null;

  return {
    outline,
    storyboard,
    pending,
    intro: intro.join("\n"),
  };
}
