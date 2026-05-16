/**
 * Session Store - Business State Management
 * Handles session data, current session, CRUD operations
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import { Session, createSession, updateSessionActivity } from "@/entities/session";
import {
  apiListSessions,
  apiCreateSession,
  apiDeleteSession,
  apiArchiveSession,
} from "@/features/session/services/session-api";

interface SessionState {
  // Data
  sessions: Session[];
  currentSessionId: string | null;
  isLoading: boolean;
  isCreating: boolean;
  isDeleting: boolean;
  error: string | null;

  // Pagination
  hasMore: boolean;
  totalCount: number;
}

interface SessionActions {
  // State setters
  setSessions: (sessions: Session[]) => void;
  setCurrentSession: (sessionId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // CRUD operations
  createSession: (title?: string, model?: string) => Promise<Session>;
  deleteSession: (sessionId: string) => Promise<void>;
  archiveSession: (sessionId: string) => Promise<void>;
  loadSessions: () => Promise<void>;
  refreshSessions: () => Promise<void>;

  // Session management
  updateSessionTitle: (sessionId: string, title: string) => void;
  updateSessionSettings: (
    sessionId: string,
    settings: Partial<Session["settings"]>
  ) => void;
  incrementMessageCount: (sessionId: string) => void;
  getCurrentSession: () => Session | undefined;
  getSessionById: (sessionId: string) => Session | undefined;
}

const initialSessionState: SessionState = {
  sessions: [],
  currentSessionId: null,
  isLoading: false,
  isCreating: false,
  isDeleting: false,
  error: null,
  hasMore: false,
  totalCount: 0,
};

export const useSessionStore = create<SessionState & SessionActions>()(
  immer(
    persist(
      (set, get) => ({
        ...initialSessionState,

        setSessions: (sessions) => set({ sessions }),
        setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
        setLoading: (isLoading) => set({ isLoading }),
        setError: (error) => set({ error }),

        createSession: async (title, model) => {
          set({ isCreating: true, error: null });
          try {
            const newSession = await apiCreateSession({ title, model });
            set((state) => {
              state.sessions.unshift(newSession);
              state.currentSessionId = newSession.id;
              state.totalCount += 1;
            });
            return newSession;
          } catch (error) {
            const message = error instanceof Error ? error.message : "Failed to create session";
            set({ error: message });
            throw error;
          } finally {
            set({ isCreating: false });
          }
        },

        deleteSession: async (sessionId) => {
          set({ isDeleting: true, error: null });
          try {
            await apiDeleteSession(sessionId);
            set((state) => {
              state.sessions = state.sessions.filter((s) => s.id !== sessionId);
              state.totalCount -= 1;
              if (state.currentSessionId === sessionId) {
                state.currentSessionId = state.sessions[0]?.id || null;
              }
            });
          } catch (error) {
            const message = error instanceof Error ? error.message : "Failed to delete session";
            set({ error: message });
            throw error;
          } finally {
            set({ isDeleting: false });
          }
        },

        archiveSession: async (sessionId) => {
          // Similar to delete but marks as archived
          set((state) => {
            const session = state.sessions.find((s) => s.id === sessionId);
            if (session) {
              session.status = "archived";
            }
          });
        },

        loadSessions: async () => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiListSessions({ limit: 50 });
            set((state) => {
              state.sessions = response.sessions;
              state.totalCount = response.total;
              state.hasMore = response.hasMore;
              // If current session no longer exists, select the first available
              const ids = new Set(response.sessions.map((s) => s.id));
              if (state.currentSessionId && !ids.has(state.currentSessionId)) {
                state.currentSessionId = response.sessions[0]?.id ?? null;
              } else if (!state.currentSessionId && response.sessions.length > 0) {
                state.currentSessionId = response.sessions[0].id;
              }
            });
          } catch (error) {
            const message = error instanceof Error ? error.message : "Failed to load sessions";
            set({ error: message });
          } finally {
            set({ isLoading: false });
          }
        },

        refreshSessions: async () => {
          return get().loadSessions();
        },

        updateSessionTitle: (sessionId, title) => {
          set((state) => {
            const session = state.sessions.find((s) => s.id === sessionId);
            if (session) {
              session.title = title;
              session.updatedAt = new Date();
            }
          });
        },

        updateSessionSettings: (sessionId, settings) => {
          set((state) => {
            const session = state.sessions.find((s) => s.id === sessionId);
            if (session) {
              session.settings = { ...session.settings, ...settings };
              session.updatedAt = new Date();
            }
          });
        },

        incrementMessageCount: (sessionId) => {
          set((state) => {
            const session = state.sessions.find((s) => s.id === sessionId);
            if (session) {
              session.messageCount += 1;
              session.lastActivityAt = new Date();
              session.updatedAt = new Date();
            }
          });
        },

        getCurrentSession: () => {
          const { sessions, currentSessionId } = get();
          return sessions.find((s) => s.id === currentSessionId);
        },

        getSessionById: (sessionId) => {
          return get().sessions.find((s) => s.id === sessionId);
        },
      }),
      {
        name: "safeclaw-session-store",
        partialize: (state) => ({
          sessions: state.sessions,
          currentSessionId: state.currentSessionId,
        }),
      }
    )
  )
);
