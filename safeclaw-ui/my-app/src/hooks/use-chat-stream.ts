"use client";

import { useCallback, useRef, useState } from "react";
import { Message } from "@/types";

interface ChatRequest {
  messages: { role: string; content: string }[];
  sessionId?: string;
  enabledSkills?: string[];
  model?: string;
}

interface StreamEvent {
  type: "thinking" | "content" | "done" | "error";
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

interface UseChatStreamOptions {
  onThinking?: (step: string, status: "running" | "completed", duration?: number) => void;
  onContent?: (content: string, delta: string) => void;
  onComplete?: (data: {
    sessionId: string;
    messageId: string;
    content: string;
    usage: StreamEvent["usage"];
    timing: StreamEvent["timing"];
    executionPath: StreamEvent["executionPath"];
    skillsUsed: StreamEvent["skillsUsed"];
  }) => void;
  onError?: (error: string) => void;
}

export function useChatStream(options: UseChatStreamOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (request: ChatRequest) => {
      setIsStreaming(true);
      setStreamingContent("");

      try {
        abortControllerRef.current = new AbortController();

        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let accumulatedContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event: StreamEvent = JSON.parse(line.slice(6));

                switch (event.type) {
                  case "thinking":
                    options.onThinking?.(
                      event.step || "",
                      event.status || "running",
                      event.duration
                    );
                    break;

                  case "content":
                    if (event.content) {
                      accumulatedContent = event.content;
                      setStreamingContent(accumulatedContent);
                      options.onContent?.(
                        event.content,
                        event.delta || ""
                      );
                    }
                    break;

                  case "done":
                    options.onComplete?.({
                      sessionId: event.sessionId || "",
                      messageId: event.messageId || "",
                      content: accumulatedContent,
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
                      executionPath: event.executionPath || [],
                      skillsUsed: event.skillsUsed || [],
                    });
                    setIsStreaming(false);
                    return;

                  case "error":
                    options.onError?.(event.error || "Unknown error");
                    setIsStreaming(false);
                    return;
                }
              } catch (e) {
                console.error("Failed to parse SSE event:", e);
              }
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          console.log("Stream aborted");
        } else {
          console.error("Chat stream error:", error);
          options.onError?.(
            error instanceof Error ? error.message : "Unknown error"
          );
        }
        setIsStreaming(false);
      }
    },
    [options]
  );

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return {
    sendMessage,
    abort,
    isStreaming,
    streamingContent,
  };
}
