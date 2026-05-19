/**
 * Chat Service - API Layer
 * Handles all chat-related API calls and stream processing
 */

import { Message, createAssistantMessage } from "@/entities/message";
import { ExecutionGraph, createExecutionGraph, ExecutionStep } from "@/entities/execution";

// Types
export interface ChatStreamRequest {
  messages: { role: string; content: string }[];
  sessionId?: string;
  enabledSkills?: string[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface ChatStreamEvent {
  type: "thinking" | "content" | "done" | "error" | "execution_step";
  // execution_step fields
  step_id?: string;
  step_type?: string;
  sub?: string;
  chips?: string[];
  skills_invoked?: string[];
  // common fields
  step?: string;
  name?: string;
  status?: "running" | "completed";
  duration?: number;
  content?: string;
  delta?: string;
  sessionId?: string;
  messageId?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  timing?: {
    startTime: number;
    endTime: number;
    totalDuration: number;
  };
  executionPath?: { name: string; duration: number }[];
  skillsUsed?: { name: string; duration: number }[];
  error?: string;
}

export interface ChatStreamCallbacks {
  onThinking?: (step: string, status: "running" | "completed", duration?: number) => void;
  onExecutionStep?: (event: ChatStreamEvent) => void;
  onContent?: (content: string, delta: string) => void;
  onExecutionUpdate?: (graph: ExecutionGraph) => void;
  onComplete?: (data: {
    message: Message;
    executionGraph: ExecutionGraph;
    usage: ChatStreamEvent["usage"];
    timing: ChatStreamEvent["timing"];
  }) => void;
  onError?: (error: string) => void;
}

// Service implementation
export class ChatService {
  private baseUrl: string;
  private abortController: AbortController | null = null;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * Send a chat message and stream the response
   */
  async streamChat(
    request: ChatStreamRequest,
    callbacks: ChatStreamCallbacks
  ): Promise<void> {
    // Abort any existing request
    this.abort();

    this.abortController = new AbortController();
    let executionGraph: ExecutionGraph | null = null;
    let accumulatedContent = "";
    let messageId = "";

    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const raw = JSON.parse(line.slice(6));
              // Map snake_case backend fields to camelCase
              const event: ChatStreamEvent = {
                ...raw,
                sessionId: raw.session_id ?? raw.sessionId,
                messageId: raw.message_id ?? raw.messageId,
                executionPath: raw.execution_path ?? raw.executionPath,
                skillsUsed: raw.skills_used ?? raw.skillsUsed,
                usage: raw.usage ? {
                  promptTokens: raw.usage.prompt_tokens ?? raw.usage.promptTokens ?? 0,
                  completionTokens: raw.usage.completion_tokens ?? raw.usage.completionTokens ?? 0,
                  totalTokens: raw.usage.total_tokens ?? raw.usage.totalTokens ?? 0,
                } : undefined,
                timing: raw.timing ? {
                  startTime: raw.timing.start_time ?? raw.timing.startTime ?? 0,
                  endTime: raw.timing.end_time ?? raw.timing.endTime ?? 0,
                  totalDuration: raw.timing.total_duration ?? raw.timing.totalDuration ?? 0,
                } : undefined,
              };
              this.handleEvent(event, callbacks, {
                executionGraph,
                accumulatedContent,
                messageId,
                request,
                onUpdate: (updates) => {
                  if (updates.executionGraph) executionGraph = updates.executionGraph;
                  if (updates.content !== undefined) accumulatedContent = updates.content;
                  if (updates.messageId) messageId = updates.messageId;
                },
              });
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Stream aborted");
        return;
      }

      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      callbacks.onError?.(errorMessage);
      throw error;
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Abort the current streaming request
   */
  abort(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Check if currently streaming
   */
  get isStreaming(): boolean {
    return this.abortController !== null;
  }

  private handleEvent(
    event: ChatStreamEvent,
    callbacks: ChatStreamCallbacks,
    context: {
      executionGraph: ExecutionGraph | null;
      accumulatedContent: string;
      messageId: string;
      request: ChatStreamRequest;
      onUpdate: (updates: {
        executionGraph?: ExecutionGraph;
        content?: string;
        messageId?: string;
      }) => void;
    }
  ): void {
    switch (event.type) {
      case "thinking": {
        callbacks.onThinking?.(event.step || "", event.status || "running", event.duration);

        // Update execution graph with thinking steps
        if (!context.executionGraph && event.step) {
          const graph = createExecutionGraph(
            context.request.sessionId || "temp",
            context.messageId || crypto.randomUUID()
          );
          context.onUpdate({ executionGraph: graph });
          callbacks.onExecutionUpdate?.(graph);
        }
        break;
      }

      case "execution_step": {
        callbacks.onExecutionStep?.(event);
        // Also emit as thinking step for the streaming indicator
        if (event.status === "running") {
          callbacks.onThinking?.(event.name || event.step_id || "", "running");
        }
        break;
      }

      case "content": {
        if (event.content) {
          context.onUpdate({ content: event.content });
          callbacks.onContent?.(event.content, event.delta || "");
        }
        break;
      }

      case "done": {
        context.onUpdate({ messageId: event.messageId || "" });

        const message = createAssistantMessage(
          context.accumulatedContent,
          event.sessionId,
          {
            usage: event.usage,
            processingTime: event.timing?.totalDuration,
            executionPath: event.executionPath?.map((p) => p.name),
            skillsUsed: event.skillsUsed?.map((s) => s.name),
          }
        );

        // Create final execution graph
        const finalGraph = this.buildExecutionGraphFromEvent(event);

        callbacks.onComplete?.({
          message,
          executionGraph: finalGraph,
          usage: event.usage || {
            promptTokens: 0,
            completionTokens: 0,
            totalTokens: 0,
          },
          timing: event.timing || {
            startTime: Date.now(),
            endTime: Date.now(),
            totalDuration: 0,
          },
        });
        break;
      }

      case "error": {
        callbacks.onError?.(event.error || "Unknown error");
        break;
      }
    }
  }

  private buildExecutionGraphFromEvent(event: ChatStreamEvent): ExecutionGraph {
    const graph = createExecutionGraph(
      event.sessionId || "temp",
      event.messageId || crypto.randomUUID()
    );

    // Add execution path steps from the done event
    if (event.executionPath) {
      for (const path of event.executionPath) {
        const step: ExecutionStep = {
          id: crypto.randomUUID(),
          name: path.name,
          type: "reasoning",
          status: "completed",
          duration: path.duration,
        };
        graph.steps.push(step);
      }
    }

    graph.status = "completed";
    graph.completedAt = new Date();
    graph.totalDuration = event.timing?.totalDuration;
    graph.metadata = {
      totalTokens: event.usage?.totalTokens,
      skillsUsed: event.skillsUsed?.map((s) => s.name),
    };

    return graph;
  }
}

// Singleton instance
export const chatService = new ChatService();

// Hook-friendly function
export async function streamChat(
  request: ChatStreamRequest,
  callbacks: ChatStreamCallbacks
): Promise<void> {
  return chatService.streamChat(request, callbacks);
}

export function abortChat(): void {
  chatService.abort();
}
