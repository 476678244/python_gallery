"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Session } from "@/types";

interface SessionsResponse {
  sessions: Session[];
  total: number;
  limit: number;
  offset: number;
}

interface CreateSessionRequest {
  title?: string;
  model?: string;
}

// GET /api/sessions
async function fetchSessions(
  limit = 20,
  offset = 0
): Promise<SessionsResponse> {
  const response = await fetch(
    `/api/sessions?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch sessions");
  }
  return response.json();
}

// POST /api/sessions
async function createSession(
  data: CreateSessionRequest
): Promise<{ session: Session; success: boolean }> {
  const response = await fetch("/api/sessions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error("Failed to create session");
  }
  return response.json();
}

// DELETE /api/sessions?id=xxx
async function deleteSession(sessionId: string): Promise<{ success: boolean; deletedId: string }> {
  const response = await fetch(`/api/sessions?id=${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete session");
  }
  return response.json();
}

export function useSessions() {
  const queryClient = useQueryClient();

  const sessionsQuery = useQuery({
    queryKey: ["sessions"],
    queryFn: () => fetchSessions(),
    staleTime: 30 * 1000, // 30 seconds
  });

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });

  return {
    // Queries
    sessions: sessionsQuery.data?.sessions || [],
    total: sessionsQuery.data?.total || 0,
    isLoading: sessionsQuery.isLoading,
    isError: sessionsQuery.isError,
    error: sessionsQuery.error,

    // Mutations
    createSession: createSessionMutation.mutate,
    deleteSession: deleteSessionMutation.mutate,
    isCreating: createSessionMutation.isPending,
    isDeleting: deleteSessionMutation.isPending,

    // Refetch
    refetch: sessionsQuery.refetch,
  };
}
