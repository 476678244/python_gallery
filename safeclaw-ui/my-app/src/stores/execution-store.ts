/**
 * Execution Store - Business State Management
 * Handles agent execution graphs, thinking steps, reasoning flow
 */

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
  ExecutionGraph,
  ExecutionStep,
  createExecutionGraph,
  startStep,
  completeStep,
  failStep,
} from "@/entities/execution";

interface ExecutionState {
  // Active executions by message ID
  activeExecutions: Record<string, ExecutionGraph>;
  // Completed executions (kept for history)
  completedExecutions: Record<string, ExecutionGraph>;
  // Current thinking state
  currentThinkingStep: string | null;
  thinkingSteps: string[];
  isThinking: boolean;
}

interface ExecutionActions {
  // Execution lifecycle
  startExecution: (sessionId: string, messageId: string) => ExecutionGraph;
  completeExecution: (messageId: string) => void;
  failExecution: (messageId: string, error: string) => void;

  // Step management
  addStep: (
    messageId: string,
    name: string,
    type: ExecutionStep["type"],
    parentId?: string
  ) => ExecutionStep;
  startStep: (messageId: string, stepId: string) => void;
  completeStep: (messageId: string, stepId: string, output?: unknown) => void;
  failStep: (messageId: string, stepId: string, error: string) => void;

  // Thinking state
  setThinking: (isThinking: boolean) => void;
  addThinkingStep: (stepName: string) => void;
  completeThinkingStep: (stepName: string) => void;
  clearThinking: () => void;

  // Queries
  getExecution: (messageId: string) => ExecutionGraph | undefined;
  getActiveExecution: () => ExecutionGraph | undefined;
  getExecutionPath: (messageId: string) => { name: string; duration: number }[];
  isExecutionComplete: (messageId: string) => boolean;

  // Cleanup
  clearExecution: (messageId: string) => void;
  clearAllExecutions: () => void;
}

const initialExecutionState: ExecutionState = {
  activeExecutions: {},
  completedExecutions: {},
  currentThinkingStep: null,
  thinkingSteps: [],
  isThinking: false,
};

export const useExecutionStore = create<ExecutionState & ExecutionActions>()(
  immer((set, get) => ({
    ...initialExecutionState,

    startExecution: (sessionId, messageId) => {
      const graph = createExecutionGraph(sessionId, messageId);
      set((state) => {
        state.activeExecutions[messageId] = graph;
        state.isThinking = true;
        state.thinkingSteps = [];
      });
      return graph;
    },

    completeExecution: (messageId) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          graph.status = "completed";
          graph.completedAt = new Date();
          graph.totalDuration =
            (graph.completedAt.getTime() - graph.startedAt.getTime()) / 1000;
          state.completedExecutions[messageId] = graph;
          delete state.activeExecutions[messageId];
        }
        state.isThinking = false;
        state.currentThinkingStep = null;
      });
    },

    failExecution: (messageId, error) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          graph.status = "error";
          graph.completedAt = new Date();
          state.completedExecutions[messageId] = graph;
          delete state.activeExecutions[messageId];
        }
        state.isThinking = false;
        state.currentThinkingStep = null;
      });
    },

    addStep: (messageId, name, type, parentId) => {
      const step: ExecutionStep = {
        id: crypto.randomUUID(),
        name,
        type,
        status: "pending",
        parentId,
        childrenIds: [],
      };

      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          graph.steps.push(step);
          if (parentId) {
            const parent = graph.steps.find((s) => s.id === parentId);
            if (parent) {
              parent.childrenIds = parent.childrenIds || [];
              parent.childrenIds.push(step.id);
            }
          }
        }
      });

      return step;
    },

    startStep: (messageId, stepId) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          const step = graph.steps.find((s) => s.id === stepId);
          if (step) {
            Object.assign(step, startStep(step));
          }
        }
      });
    },

    completeStep: (messageId, stepId, output) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          const step = graph.steps.find((s) => s.id === stepId);
          if (step) {
            Object.assign(step, completeStep(step, output));
          }
        }
      });
    },

    failStep: (messageId, stepId, error) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          const step = graph.steps.find((s) => s.id === stepId);
          if (step) {
            Object.assign(step, failStep(step, error));
          }
        }
      });
    },

    setThinking: (isThinking) => set({ isThinking }),

    addThinkingStep: (stepName) => {
      set((state) => {
        state.thinkingSteps.push(stepName);
        state.currentThinkingStep = stepName;
      });
    },

    completeThinkingStep: (stepName) => {
      set((state) => {
        const index = state.thinkingSteps.indexOf(stepName);
        if (index > -1) {
          // Move to next step or clear
          if (index < state.thinkingSteps.length - 1) {
            state.currentThinkingStep = state.thinkingSteps[index + 1];
          } else {
            state.currentThinkingStep = null;
          }
        }
      });
    },

    clearThinking: () =>
      set({
        currentThinkingStep: null,
        thinkingSteps: [],
        isThinking: false,
      }),

    getExecution: (messageId) => {
      const state = get();
      return (
        state.activeExecutions[messageId] ||
        state.completedExecutions[messageId]
      );
    },

    getActiveExecution: () => {
      const state = get();
      const entries = Object.values(state.activeExecutions);
      return entries[0]; // Return first active execution
    },

    getExecutionPath: (messageId) => {
      const graph = get().getExecution(messageId);
      if (!graph) return [];

      return graph.steps.map((step) => ({
        name: step.name,
        duration: step.duration || 0,
      }));
    },

    isExecutionComplete: (messageId) => {
      const graph = get().getExecution(messageId);
      return graph?.status === "completed" || graph?.status === "error";
    },

    clearExecution: (messageId) => {
      set((state) => {
        delete state.activeExecutions[messageId];
        delete state.completedExecutions[messageId];
      });
    },

    clearAllExecutions: () => {
      set({
        activeExecutions: {},
        completedExecutions: {},
        isThinking: false,
        currentThinkingStep: null,
        thinkingSteps: [],
      });
    },
  }))
);
