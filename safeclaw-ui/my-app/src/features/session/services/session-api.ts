/**
 * Session Service - API Layer
 * Handles all session-related API calls
 */

import { Session, createSession } from "@/entities/session";

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
    return {
      ...(s as unknown as Session),
      title: (s.title as string) ?? "New Chat",
      status: (s.status as Session["status"]) ?? "active",
      messageCount: (s.message_count as number) ?? (s.messageCount as number) ?? 0,
      settings: (s.settings as Session["settings"]) ?? {},
      createdAt: s.created_at || s.createdAt ? new Date((s.created_at ?? s.createdAt) as string) : new Date(),
      updatedAt: s.updated_at || s.updatedAt ? new Date((s.updated_at ?? s.updatedAt) as string) : new Date(),
      lastActivityAt: s.last_activity_at || s.lastActivityAt
        ? new Date((s.last_activity_at ?? s.lastActivityAt) as string)
        : new Date(),
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
export const apiArchiveSession = (id: string) => sessionService.archiveSession(id);
