/**
 * Skill Store - Business State Management
 * Handles skill tree, enabled/disabled state
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import { Skill, SkillTreeNode, getEnabledSkills } from "@/entities/skill";
import {
  apiGetSkillTree,
  apiToggleSkill,
  apiToggleFolder,
  apiRefreshSkills,
} from "@/features/skills/services/skill-api";

interface SkillState {
  // Data
  skillTree: SkillTreeNode[];
  flatSkills: Skill[];
  enabledSkillIds: Set<string>;
  expandedFolderIds: Set<string>;

  // Loading state
  isLoading: boolean;
  isToggling: boolean;
  error: string | null;

  // Stats
  totalSkills: number;
  builtinCount: number;
  privateCount: number;
  linkedCount: number;
}

interface SkillActions {
  // State setters
  setSkillTree: (tree: SkillTreeNode[]) => void;
  setEnabledSkills: (skillIds: string[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Tree operations
  loadSkills: () => Promise<void>;
  refreshSkills: () => Promise<void>;

  // Toggle operations
  toggleSkill: (skillId: string) => Promise<void>;
  toggleFolder: (folderId: string) => Promise<void>;
  enableSkill: (skillId: string) => Promise<void>;
  disableSkill: (skillId: string) => Promise<void>;
  enableAllInFolder: (folderId: string) => Promise<void>;
  disableAllInFolder: (folderId: string) => Promise<void>;

  // Folder expansion
  toggleFolderExpanded: (folderId: string) => void;
  expandFolder: (folderId: string) => void;
  collapseFolder: (folderId: string) => void;
  expandAll: () => void;
  collapseAll: () => void;

  // Queries
  isEnabled: (skillId: string) => boolean;
  isExpanded: (folderId: string) => boolean;
  getEnabledSkills: () => string[];
  getSkillById: (skillId: string) => Skill | undefined;
}

const initialSkillState: SkillState = {
  skillTree: [],
  flatSkills: [],
  enabledSkillIds: new Set(),
  expandedFolderIds: new Set(["built_in", "private_skills", "linked_skills"]),
  isLoading: false,
  isToggling: false,
  error: null,
  totalSkills: 0,
  builtinCount: 0,
  privateCount: 0,
  linkedCount: 0,
};

export const useSkillStore = create<SkillState & SkillActions>()(
  immer(
    persist(
      (set, get) => ({
        ...initialSkillState,

        setSkillTree: (tree) => set({ skillTree: tree }),
        setEnabledSkills: (skillIds) =>
          set({ enabledSkillIds: new Set(skillIds) }),
        setLoading: (isLoading) => set({ isLoading }),
        setError: (error) => set({ error }),

        loadSkills: async () => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiGetSkillTree();
            set({
              skillTree: response.tree,
              totalSkills: response.total,
              builtinCount: response.builtin,
              privateCount: response.private,
              linkedCount: response.linked,
            });

            // Extract enabled skills from tree
            const enabled = extractEnabledSkills(response.tree);
            set({ enabledSkillIds: new Set(enabled) });
          } catch (error) {
            const message =
              error instanceof Error ? error.message : "Failed to load skills";
            set({ error: message });
          } finally {
            set({ isLoading: false });
          }
        },

        refreshSkills: async () => {
          return get().loadSkills();
        },

        toggleSkill: async (skillId) => {
          const currentlyEnabled = get().enabledSkillIds.has(skillId);
          const newEnabled = !currentlyEnabled;

          // Optimistic update
          set((state) => {
            if (newEnabled) {
              state.enabledSkillIds.add(skillId);
            } else {
              state.enabledSkillIds.delete(skillId);
            }
          });

          set({ isToggling: true });
          try {
            await apiToggleSkill(skillId, newEnabled);
          } catch (error) {
            // Revert on error
            set((state) => {
              if (currentlyEnabled) {
                state.enabledSkillIds.add(skillId);
              } else {
                state.enabledSkillIds.delete(skillId);
              }
            });
            throw error;
          } finally {
            set({ isToggling: false });
          }
        },

        toggleFolder: async (folderId) => {
          // Determine new enabled state: if any child skill is currently enabled, disable all; otherwise enable all
          const childSkillIds = collectLeafSkillIds(get().skillTree, folderId);
          const anyEnabled = childSkillIds.some((id) => get().enabledSkillIds.has(id));
          const newEnabled = !anyEnabled;

          // Optimistic update: add/remove all child skill ids
          set((state) => {
            for (const id of childSkillIds) {
              if (newEnabled) {
                state.enabledSkillIds.add(id);
              } else {
                state.enabledSkillIds.delete(id);
              }
            }
          });

          set({ isToggling: true });
          try {
            await apiToggleFolder(folderId, newEnabled);
          } catch (error) {
            // Revert on error
            set((state) => {
              for (const id of childSkillIds) {
                if (anyEnabled) {
                  state.enabledSkillIds.add(id);
                } else {
                  state.enabledSkillIds.delete(id);
                }
              }
            });
            throw error;
          } finally {
            set({ isToggling: false });
          }
        },

        enableSkill: async (skillId) => {
          if (!get().enabledSkillIds.has(skillId)) {
            await get().toggleSkill(skillId);
          }
        },

        disableSkill: async (skillId) => {
          if (get().enabledSkillIds.has(skillId)) {
            await get().toggleSkill(skillId);
          }
        },

        enableAllInFolder: async (folderId) => {
          const childSkillIds = collectLeafSkillIds(get().skillTree, folderId);
          set((state) => {
            for (const id of childSkillIds) {
              state.enabledSkillIds.add(id);
            }
          });
          set({ isToggling: true });
          try {
            await apiToggleFolder(folderId, true);
          } finally {
            set({ isToggling: false });
          }
        },

        disableAllInFolder: async (folderId) => {
          const childSkillIds = collectLeafSkillIds(get().skillTree, folderId);
          set((state) => {
            for (const id of childSkillIds) {
              state.enabledSkillIds.delete(id);
            }
          });
          set({ isToggling: true });
          try {
            await apiToggleFolder(folderId, false);
          } finally {
            set({ isToggling: false });
          }
        },

        toggleFolderExpanded: (folderId) => {
          set((state) => {
            if (state.expandedFolderIds.has(folderId)) {
              state.expandedFolderIds.delete(folderId);
            } else {
              state.expandedFolderIds.add(folderId);
            }
          });
        },

        expandFolder: (folderId) => {
          set((state) => {
            state.expandedFolderIds.add(folderId);
          });
        },

        collapseFolder: (folderId) => {
          set((state) => {
            state.expandedFolderIds.delete(folderId);
          });
        },

        expandAll: () => {
          set((state) => {
            const allFolderIds = collectFolderIds(state.skillTree);
            state.expandedFolderIds = new Set(allFolderIds);
          });
        },

        collapseAll: () => {
          set((state) => {
            state.expandedFolderIds.clear();
          });
        },

        isEnabled: (skillId) => get().enabledSkillIds.has(skillId),
        isExpanded: (folderId) => get().expandedFolderIds.has(folderId),
        getEnabledSkills: () => Array.from(get().enabledSkillIds),
        getSkillById: (skillId) =>
          get().flatSkills.find((s) => s.id === skillId),
      }),
      {
        name: "safeclaw-skill-store",
        partialize: (state) => ({
          enabledSkillIds: Array.from(state.enabledSkillIds),
          expandedFolderIds: Array.from(state.expandedFolderIds),
        }),
        merge: (persisted, current) => ({
          ...current,
          ...(persisted as object),
          enabledSkillIds: new Set((persisted as { enabledSkillIds?: string[] }).enabledSkillIds ?? []),
          expandedFolderIds: new Set((persisted as { expandedFolderIds?: string[] }).expandedFolderIds ?? ["built_in", "private_skills", "linked_skills"]),
        }),
      }
    )
  )
);

// Helper functions
function extractEnabledSkills(nodes: SkillTreeNode[]): string[] {
  const enabled: string[] = [];

  for (const node of nodes) {
    if (!node.isFolder && node.enabled) {
      enabled.push(node.id);
    }
    if (node.children) {
      enabled.push(...extractEnabledSkills(node.children));
    }
  }

  return enabled;
}

function collectLeafSkillIds(nodes: SkillTreeNode[], folderId: string): string[] {
  function findAndCollect(nodes: SkillTreeNode[]): string[] | null {
    for (const node of nodes) {
      if (node.id === folderId) {
        return collectAllLeafIds(node.children ?? []);
      }
      if (node.children) {
        const result = findAndCollect(node.children);
        if (result !== null) return result;
      }
    }
    return null;
  }

  function collectAllLeafIds(nodes: SkillTreeNode[]): string[] {
    const ids: string[] = [];
    for (const node of nodes) {
      if (!node.isFolder) {
        ids.push(node.id);
      } else if (node.children) {
        ids.push(...collectAllLeafIds(node.children));
      }
    }
    return ids;
  }

  return findAndCollect(nodes) ?? [];
}

function collectFolderIds(nodes: SkillTreeNode[]): string[] {
  const ids: string[] = [];

  for (const node of nodes) {
    if (node.isFolder) {
      ids.push(node.id);
      if (node.children) {
        ids.push(...collectFolderIds(node.children));
      }
    }
  }

  return ids;
}
