/**
 * Parse Plan-mode structured reply (ModePolicy addendum).
 * SoT: docs/features/agent-modes/methodology.md § Plan
 */

export interface PlanArtifact {
  steps: string[];
  risks: string[];
  pending: string[];
  /** Non-heading prose before ### Plan (optional intro). */
  intro: string;
}

/** True when content looks like a Plan-mode structured artifact. */
export function looksLikePlanArtifact(content: string): boolean {
  if (!content || !content.trim()) return false;
  return /^###\s*Plan\s*$/im.test(content);
}

/**
 * Extract Plan / Risks / Pending confirmation sections.
 * Fail Fast: returns null if ### Plan is missing or has zero steps.
 */
export function parsePlanArtifact(content: string): PlanArtifact | null {
  if (!looksLikePlanArtifact(content)) return null;

  const lines = content.replace(/\r\n/g, "\n").split("\n");
  let section: "intro" | "plan" | "risks" | "pending" = "intro";
  const intro: string[] = [];
  const steps: string[] = [];
  const risks: string[] = [];
  const pending: string[] = [];

  for (const raw of lines) {
    const heading = raw.match(/^###\s*(Plan|Risks|Pending confirmation)\s*$/i);
    if (heading) {
      const h = heading[1].toLowerCase();
      if (h === "plan") section = "plan";
      else if (h === "risks") section = "risks";
      else section = "pending";
      continue;
    }
    // Skip other ### headings without leaving current section bag
    if (/^###\s+/.test(raw)) continue;

    const trimmed = raw.trim();
    if (!trimmed) continue;

    if (section === "intro") {
      intro.push(trimmed);
      continue;
    }

    const bullet = trimmed.replace(/^[-*]\s+/, "").replace(/^\d+[.)]\s+/, "");
    if (section === "plan") {
      if (bullet) steps.push(bullet);
    } else if (section === "risks") {
      if (bullet) risks.push(bullet);
    } else if (section === "pending") {
      if (bullet) pending.push(bullet);
    }
  }

  if (steps.length === 0) return null;

  return {
    steps,
    risks,
    pending,
    intro: intro.join("\n"),
  };
}
