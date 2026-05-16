"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { SkillNode } from "@/types";

interface SkillsResponse {
  tree: SkillNode[];
  total: number;
  categories: number;
  builtin: number;
  private: number;
  linked: number;
}

interface SkillsFlatResponse {
  skills: SkillNode[];
  total: number;
}

// GET /api/skills
async function fetchSkills(): Promise<SkillsResponse> {
  const response = await fetch("/api/skills");
  if (!response.ok) {
    throw new Error("Failed to fetch skills");
  }
  return response.json();
}

// GET /api/skills?flat=true
async function fetchSkillsFlat(): Promise<SkillsFlatResponse> {
  const response = await fetch("/api/skills?flat=true");
  if (!response.ok) {
    throw new Error("Failed to fetch skills");
  }
  return response.json();
}

// POST /api/skills (toggle)
async function toggleSkill({
  skillId,
  enabled,
}: {
  skillId: string;
  enabled: boolean;
}): Promise<{ success: boolean; skillId: string; enabled: boolean }> {
  const response = await fetch("/api/skills", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ skillId, enabled }),
  });
  if (!response.ok) {
    throw new Error("Failed to toggle skill");
  }
  return response.json();
}

// POST /api/skills (toggle folder)
async function toggleFolder({
  folderId,
  enabled,
}: {
  folderId: string;
  enabled: boolean;
}): Promise<{ success: boolean; folderId: string; enabled: boolean }> {
  const response = await fetch("/api/skills", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ folderId, enabled }),
  });
  if (!response.ok) {
    throw new Error("Failed to toggle folder");
  }
  return response.json();
}

export function useSkills() {
  const queryClient = useQueryClient();

  const skillsQuery = useQuery({
    queryKey: ["skills"],
    queryFn: fetchSkills,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const skillsFlatQuery = useQuery({
    queryKey: ["skills", "flat"],
    queryFn: fetchSkillsFlat,
    staleTime: 5 * 60 * 1000,
    enabled: false, // Don't fetch automatically
  });

  const toggleSkillMutation = useMutation({
    mutationFn: toggleSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  const toggleFolderMutation = useMutation({
    mutationFn: toggleFolder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  return {
    // Queries
    skills: skillsQuery.data?.tree || [],
    skillsSummary: {
      total: skillsQuery.data?.total || 0,
      categories: skillsQuery.data?.categories || 0,
      builtin: skillsQuery.data?.builtin || 0,
      private: skillsQuery.data?.private || 0,
      linked: skillsQuery.data?.linked || 0,
    },
    isLoading: skillsQuery.isLoading,
    isError: skillsQuery.isError,
    error: skillsQuery.error,

    // Mutations
    toggleSkill: toggleSkillMutation.mutate,
    toggleFolder: toggleFolderMutation.mutate,
    isToggling: toggleSkillMutation.isPending || toggleFolderMutation.isPending,

    // Refetch
    refetch: skillsQuery.refetch,
  };
}
