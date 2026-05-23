/**
 * Skill Entity - Domain Model
 * Represents an AI skill/tool in the system
 */

export type SkillCategory = "builtin" | "private" | "linked" | "marketplace";
export type SkillStatus = "active" | "disabled" | "error" | "loading";

export interface SkillEntry {
  name: string;
  description: string;
  version: string;
  author: string;
  tags?: string[];
  icon?: string;
  dependencies?: string[];
  permissions?: string[];
}

export interface Skill {
  id: string;
  path: string;
  name: string;
  category: SkillCategory;
  status: SkillStatus;
  enabled: boolean;
  entry: SkillEntry;
  children?: Skill[]; // For hierarchical skills (folders)
  parentId?: string;
  isFolder: boolean;
  expanded?: boolean;
  loadedAt?: Date;
  lastUsedAt?: Date;
}

export interface SkillTreeNode {
  id: string;
  name: string;
  path: string;
  isFolder: boolean;
  enabled: boolean;
  expanded: boolean;
  children: SkillTreeNode[];
  skillEntry?: SkillEntry;
  category?: SkillCategory;
}

// Factory functions
export function createSkill(
  path: string,
  entry: SkillEntry,
  category: SkillCategory = "builtin",
  parentId?: string
): Skill {
  return {
    id: `skill-${path.replace(/\//g, "-")}`,
    path,
    name: entry.name,
    category,
    status: "active",
    enabled: true,
    entry,
    parentId,
    isFolder: false,
    expanded: false,
  };
}

export function createSkillFolder(
  path: string,
  name: string,
  category: SkillCategory,
  children: Skill[] = []
): Skill {
  return {
    id: `folder-${path.replace(/\//g, "-")}`,
    path,
    name,
    category,
    status: "active",
    enabled: true,
    entry: {
      name,
      description: `${name} skill collection`,
      version: "1.0.0",
      author: "system",
    },
    children,
    isFolder: true,
    expanded: true,
  };
}

// Utilities
export function flattenSkills(skills: Skill[]): Skill[] {
  const result: Skill[] = [];
  for (const skill of skills) {
    result.push(skill);
    if (skill.children) {
      result.push(...flattenSkills(skill.children));
    }
  }
  return result;
}

export function getEnabledSkills(skills: Skill[]): string[] {
  return flattenSkills(skills)
    .filter((s) => !s.isFolder && s.enabled)
    .map((s) => s.id);
}

export function findSkillById(skills: Skill[], id: string): Skill | undefined {
  for (const skill of skills) {
    if (skill.id === id) return skill;
    if (skill.children) {
      const found = findSkillById(skill.children, id);
      if (found) return found;
    }
  }
  return undefined;
}

export function toggleSkillEnabled(skill: Skill): Skill {
  return {
    ...skill,
    enabled: !skill.enabled,
  };
}
