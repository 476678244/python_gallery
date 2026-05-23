/**
 * Message Store - Business State Management
 * Handles chat messages, streaming state
 */

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
  Message,
  createUserMessage,
  createAssistantMessage,
  ThinkingStep,
} from "@/entities/message";

interface MessageState {
  // Messages by session (plain Record for Zustand reactivity)
  messagesBySession: Record<string, Message[]>;
  // Current streaming state
  isStreaming: boolean;
  streamingContent: string;
  streamingMessageId: string | null;
  // Current session
  currentSessionId: string | null;
}

interface MessageActions {
  // Message CRUD
  addMessage: (message: Message) => void;
  addUserMessage: (content: string, sessionId?: string) => Message;
  addAssistantMessage: (
    content: string,
    sessionId?: string,
    metadata?: Message["metadata"]
  ) => Message;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  deleteMessage: (messageId: string) => void;
  clearMessages: (sessionId?: string) => void;

  // Streaming
  startStreaming: (sessionId: string) => string;
  appendStreamingContent: (content: string) => void;
  completeStreaming: (finalContent?: string) => Message | null;
  cancelStreaming: () => void;

  // Session management
  setCurrentSession: (sessionId: string | null) => void;
  getMessagesForSession: (sessionId: string) => Message[];
  getCurrentMessages: () => Message[];

  // Queries
  getMessageById: (messageId: string) => Message | undefined;
  getLastMessage: (sessionId?: string) => Message | undefined;
  hasMessages: (sessionId?: string) => boolean;
}

const initialMessageState: MessageState = {
  messagesBySession: {},
  isStreaming: false,
  streamingContent: "",
  streamingMessageId: null,
  currentSessionId: null,
};

export const useMessageStore = create<MessageState & MessageActions>()(
  immer((set, get) => ({
    ...initialMessageState,

    addMessage: (message) => {
      set((state) => {
        const sessionId = message.sessionId || "default";
        if (!state.messagesBySession[sessionId]) {
          state.messagesBySession[sessionId] = [];
        }
        state.messagesBySession[sessionId].push(message);
      });
    },

    addUserMessage: (content, sessionId) => {
      const message = createUserMessage(content, sessionId);
      get().addMessage(message);
      return message;
    },

    addAssistantMessage: (content, sessionId, metadata) => {
      const message = createAssistantMessage(content, sessionId, metadata);
      get().addMessage(message);
      return message;
    },

    updateMessage: (messageId, updates) => {
      set((state) => {
        for (const messages of Object.values(state.messagesBySession)) {
          const message = messages.find((m) => m.id === messageId);
          if (message) {
            Object.assign(message, updates);
            break;
          }
        }
      });
    },

    deleteMessage: (messageId) => {
      set((state) => {
        for (const [sessionId, messages] of Object.entries(state.messagesBySession)) {
          const index = messages.findIndex((m) => m.id === messageId);
          if (index > -1) {
            messages.splice(index, 1);
            break;
          }
        }
      });
    },

    clearMessages: (sessionId) => {
      set((state) => {
        if (sessionId) {
          delete state.messagesBySession[sessionId];
        } else {
          state.messagesBySession = {};
        }
      });
    },

    startStreaming: (sessionId) => {
      const messageId = crypto.randomUUID();
      set({
        isStreaming: true,
        streamingContent: "",
        streamingMessageId: messageId,
        currentSessionId: sessionId,
      });
      return messageId;
    },

    appendStreamingContent: (content) => {
      set((state) => {
        state.streamingContent += content;
      });
    },

    completeStreaming: (finalContent) => {
      const state = get();
      if (!state.streamingMessageId || !state.currentSessionId) return null;

      const content = finalContent || state.streamingContent;
      const message = createAssistantMessage(
        content,
        state.currentSessionId,
        {}
      );

      // Update message ID to match streaming ID
      message.id = state.streamingMessageId;

      set((s) => {
        if (!s.currentSessionId) return;

        if (!s.messagesBySession[s.currentSessionId]) {
          s.messagesBySession[s.currentSessionId] = [];
        }
        s.messagesBySession[s.currentSessionId].push(message);

        s.isStreaming = false;
        s.streamingContent = "";
        s.streamingMessageId = null;
      });

      return message;
    },

    cancelStreaming: () => {
      set({
        isStreaming: false,
        streamingContent: "",
        streamingMessageId: null,
      });
    },

    setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),

    getMessagesForSession: (sessionId) => {
      return get().messagesBySession[sessionId] || [];
    },

    getCurrentMessages: () => {
      const { currentSessionId, messagesBySession } = get();
      if (!currentSessionId) return [];
      return messagesBySession[currentSessionId] || [];
    },

    getMessageById: (messageId) => {
      for (const messages of Object.values(get().messagesBySession)) {
        const message = messages.find((m) => m.id === messageId);
        if (message) return message;
      }
      return undefined;
    },

    getLastMessage: (sessionId) => {
      const messages = sessionId
        ? get().messagesBySession[sessionId]
        : get().getCurrentMessages();
      return messages?.[messages.length - 1];
    },

    hasMessages: (sessionId) => {
      const messages = sessionId
        ? get().messagesBySession[sessionId]
        : get().getCurrentMessages();
      return (messages?.length || 0) > 0;
    },
  }))
);
