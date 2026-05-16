/**
 * Skill Service - API Layer
 * Handles all skill-related API calls
 */

import { Skill, SkillTreeNode, createSkill, createSkillFolder } from "@/entities/skill";

// Types
export interface ListSkillsOptions {
  flat?: boolean;
  category?: "builtin" | "private" | "linked" | "all";
  enabledOnly?: boolean;
}

export interface ListSkillsResponse {
  tree: SkillTreeNode[];
  total: number;
  categories: number;
  builtin: number;
  private: number;
  linked: number;
}

export interface ToggleSkillRequest {
  skillId?: string;
  folderId?: string;
  enabled: boolean;
}

export interface SkillStatusResponse {
  success: boolean;
  skillId?: string;
  folderId?: string;
  enabled: boolean;
  affectedSkills?: string[];
}

// Service implementation
export class SkillService {
  private baseUrl: string;
  private cache: Map<string, ListSkillsResponse> = new Map();

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * Get skill tree hierarchy
   */
  async getSkillTree(options: ListSkillsOptions = {}): Promise<ListSkillsResponse> {
    const cacheKey = JSON.stringify(options);

    // Check cache for non-flat requests
    if (!options.flat && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const params = new URLSearchParams();
    if (options.flat) params.set("flat", "true");
    if (options.category && options.category !== "all") {
      params.set("category", options.category);
    }

    const response = await fetch(`${this.baseUrl}/skills?${params}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch skills: ${response.status}`);
    }

    const data: ListSkillsResponse = await response.json();

    // Cache the result
    if (!options.flat) {
      this.cache.set(cacheKey, data);
    }

    return data;
  }

  /**
   * Get flat list of all skills
   */
  async getSkillsList(options: Omit<ListSkillsOptions, "flat"> = {}): Promise<Skill[]> {
    const data = await this.getSkillTree({ ...options, flat: true });
    return this.transformNodesToSkills(data.tree);
  }

  /**
   * Toggle skill enabled state
   */
  async toggleSkill(skillId: string, enabled: boolean): Promise<SkillStatusResponse> {
    const response = await fetch(`${this.baseUrl}/skills`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ skillId, enabled }),
    });

    if (!response.ok) {
      throw new Error(`Failed to toggle skill: ${response.status}`);
    }

    // Invalidate cache
    this.cache.clear();

    return response.json();
  }

  /**
   * Toggle folder enabled state (affects all children)
   */
  async toggleFolder(folderId: string, enabled: boolean): Promise<SkillStatusResponse> {
    const response = await fetch(`${this.baseUrl}/skills`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ folderId, enabled }),
    });

    if (!response.ok) {
      throw new Error(`Failed to toggle folder: ${response.status}`);
    }

    // Invalidate cache
    this.cache.clear();

    return response.json();
  }

  /**
   * Get enabled skill IDs
   */
  async getEnabledSkillIds(): Promise<string[]> {
    const skills = await this.getSkillsList({ enabledOnly: true });
    return skills.filter((s) => s.enabled).map((s) => s.id);
  }

  /**
   * Refresh skill tree (clear cache and refetch)
   */
  async refreshSkills(): Promise<ListSkillsResponse> {
    this.cache.clear();
    return this.getSkillTree();
  }

  private transformNodesToSkills(nodes: SkillTreeNode[]): Skill[] {
    const skills: Skill[] = [];

    for (const node of nodes) {
      if (node.skillEntry) {
        skills.push({
          id: node.id,
          path: node.path,
          name: node.name,
          category: (node.category as Skill["category"]) || "builtin",
          status: "active",
          enabled: node.enabled,
          entry: node.skillEntry,
          isFolder: node.isFolder,
          expanded: node.expanded,
        });
      }

      if (node.children && node.children.length > 0) {
        skills.push(...this.transformNodesToSkills(node.children));
      }
    }

    return skills;
  }
}

// Singleton instance
export const skillService = new SkillService();

// Convenience API functions
export const apiGetSkillTree = (opts?: ListSkillsOptions) => skillService.getSkillTree(opts);
export const apiGetSkillsList = (opts?: Omit<ListSkillsOptions, "flat">) =>
  skillService.getSkillsList(opts);
export const apiToggleSkill = (id: string, enabled: boolean) =>
  skillService.toggleSkill(id, enabled);
export const apiToggleFolder = (id: string, enabled: boolean) =>
  skillService.toggleFolder(id, enabled);
export const apiRefreshSkills = () => skillService.refreshSkills();
