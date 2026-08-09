/**
 * Session Service - API Layer
 * Handles all session-related API calls
 */

import { Session } from "@/entities/session";

// Types
export interface ListSessionsOptions {
  limit?: number;
  offset?: number;
  status?: "active" | "archived" | "all";
}

export interface ListSessionsResponse {
  sessions: Session[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface CreateSessionRequest {
  title?: string;
  model?: string;
  workspaceId?: string;
}

export interface UpdateSessionRequest {
  title?: string;
  settings?: Partial<Session["settings"]>;
  status?: Session["status"];
}

// Service implementation
export class SessionService {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * List all sessions with pagination
   */
  async listSessions(options: ListSessionsOptions = {}): Promise<ListSessionsResponse> {
    const { limit = 20, offset = 0, status = "active" } = options;

    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      ...(status !== "all" && { status }),
    });

    const response = await fetch(`${this.baseUrl}/sessions?${params}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch sessions: ${response.status}`);
    }

    const data = await response.json();

    // Transform date strings to Date objects
    return {
      sessions: data.sessions.map(this.parseSessionDates),
      total: data.total,
      limit: data.limit,
      offset: data.offset,
      hasMore: data.total > offset + data.sessions.length,
    };
  }

  /**
   * Get a single session by ID
   */
  async getSession(sessionId: string): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Session not found: ${sessionId}`);
      }
      throw new Error(`Failed to fetch session: ${response.status}`);
    }

    const data = await response.json();
    return this.parseSessionDates(data.session);
  }

  /**
   * Create a new session
   */
  async createSession(request: CreateSessionRequest = {}): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.status}`);
    }

    const data = await response.json();
    return this.parseSessionDates(data.session);
  }

  /**
   * Update an existing session
   */
  async updateSession(
    sessionId: string,
    request: UpdateSessionRequest
  ): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to update session: ${response.status}`);
    }

    const data = await response.json();
    return this.parseSessionDates(data.session);
  }

  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/sessions?id=${sessionId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to delete session: ${response.status}`);
    }
  }

  /**
   * Delete all sessions + persisted messages (one-click clear).
   */
  async clearAllSessions(): Promise<{ deletedCount: number; deletedIds: string[] }> {
    const response = await fetch(`${this.baseUrl}/sessions/all`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(
        `[session-api] clearAllSessions failed (Fail Fast)\n` +
          `  Status: ${response.status}\n` +
          `  Body: ${detail.slice(0, 300)}`
      );
    }
    const data = (await response.json()) as {
      deleted_count?: number;
      deleted_ids?: string[];
    };
    return {
      deletedCount: data.deleted_count ?? 0,
      deletedIds: data.deleted_ids ?? [],
    };
  }

  /**
   * Archive a session (soft delete)
   */
  async archiveSession(sessionId: string): Promise<Session> {
    return this.updateSession(sessionId, { status: "archived" });
  }

  /**
   * Update session activity timestamp
   */
  async updateActivity(sessionId: string): Promise<void> {
    await this.updateSession(sessionId, {});
  }

  private parseSessionDates(raw: Record<string, unknown>): Session {
    const s = raw as Record<string, unknown>;
    if (!s.id || typeof s.id !== "string") {
      throw new Error(
        `[session-api] Session missing id (Fail Fast)\n  Actual: ${JSON.stringify(raw).slice(0, 200)}`
      );
    }
    const settings = s.settings as Session["settings"] | undefined;
    if (!settings || typeof settings !== "object") {
      throw new Error(
        `[session-api] Session missing settings (Fail Fast)\n  id: ${s.id}`
      );
    }
    if (typeof settings.model !== "string" || !settings.model.trim()) {
      throw new Error(
        `[session-api] Session missing settings.model (Fail Fast)\n` +
          `  id: ${s.id}\n` +
          `  settings: ${JSON.stringify(settings)}`
      );
    }
    if (!s.created_at && !s.createdAt) {
      throw new Error(
        `[session-api] Session missing created_at (Fail Fast)\n  id: ${s.id}`
      );
    }
    return {
      ...(s as unknown as Session),
      id: s.id,
      title: (s.title as string) || "New Chat",
      status: (s.status as Session["status"]) || "active",
      messageCount: (s.message_count as number) ?? (s.messageCount as number) ?? 0,
      settings,
      createdAt: new Date((s.created_at ?? s.createdAt) as string),
      updatedAt: new Date((s.updated_at ?? s.updatedAt ?? s.created_at ?? s.createdAt) as string),
      lastActivityAt: new Date(
        (s.last_activity_at ?? s.lastActivityAt ?? s.updated_at ?? s.created_at ?? s.createdAt) as string
      ),
    };
  }
}

// Singleton instance
export const sessionService = new SessionService();

// Convenience API functions
export const apiListSessions = (opts?: ListSessionsOptions) => sessionService.listSessions(opts);
export const apiGetSession = (id: string) => sessionService.getSession(id);
export const apiCreateSession = (req?: CreateSessionRequest) => sessionService.createSession(req);
export const apiUpdateSession = (id: string, req: UpdateSessionRequest) =>
  sessionService.updateSession(id, req);
export const apiDeleteSession = (id: string) => sessionService.deleteSession(id);
export const apiClearAllSessions = () => sessionService.clearAllSessions();
export const apiArchiveSession = (id: string) => sessionService.archiveSession(id);
