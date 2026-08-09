/**
 * Execution Store - Business State Management
 * Handles agent execution graphs, thinking steps, reasoning flow
 */

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
  ExecutionGraph,
  ExecutionStep,
  ExecutionStepType,
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
  /** Stop-the-World latch (Halt). Cleared on next startExecution. */
  worldStopped: boolean;
}

interface ExecutionActions {
  // Execution lifecycle
  startExecution: (sessionId: string, messageId: string) => ExecutionGraph;
  completeExecution: (messageId: string, metadata?: {
    totalTokens?: number;
    skillsUsed?: string[];
    totalDuration?: number;
  }) => void;
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

  // SSE event handler
  handleExecutionStepEvent: (messageId: string, event: {
    step_id?: string;
    parent_step_id?: string;
    name?: string;
    step_type?: string;
    status?: string;
    duration?: number;
    sub?: string;
    chips?: string[];
    active_skills?: string[];
    skills_invoked?: string[];
    skills_loaded?: string[];
    agent_name?: string;
    step_now?: string;
    look_ahead?: string[];
    expected_output?: string;
    error?: string;
  }) => void;

  // Queries
  getExecution: (messageId: string) => ExecutionGraph | undefined;
  getActiveExecution: () => ExecutionGraph | undefined;
  getLatestExecution: () => ExecutionGraph | undefined;
  getExecutionPath: (messageId: string) => { name: string; duration: number }[];
  isExecutionComplete: (messageId: string) => boolean;

  // Remap execution messageId (frontend UUID → backend message_id)
  remapExecution: (oldMessageId: string, newMessageId: string) => void;

  /** Halt: mark all running steps cancelled (Stop the World). */
  haltActiveSteps: () => void;
  /** Steer: mark running steps redirected before USER_STEER inject. */
  redirectActiveSteps: () => void;

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
  worldStopped: false,
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
        state.worldStopped = false;
      });
      return graph;
    },

    completeExecution: (messageId, metadata) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (graph) {
          graph.status = "completed";
          graph.completedAt = new Date();
          graph.totalDuration = metadata?.totalDuration ??
            (graph.completedAt.getTime() - graph.startedAt.getTime()) / 1000;
          graph.metadata = {
            ...graph.metadata,
            totalTokens: metadata?.totalTokens,
            skillsUsed: metadata?.skillsUsed,
          };
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

    handleExecutionStepEvent: (messageId, event) => {
      set((state) => {
        const graph = state.activeExecutions[messageId];
        if (!graph) return;

        const stepId = event.step_id || crypto.randomUUID();
        const stepType = (event.step_type || "reasoning") as ExecutionStepType;
        const status = (event.status || "completed") as ExecutionStep["status"];

        const patchBrief = (step: ExecutionStep) => {
          if (event.agent_name) step.agentName = event.agent_name;
          if (event.step_now) step.stepNow = event.step_now;
          if (event.look_ahead) step.lookAhead = event.look_ahead;
          if (event.expected_output) step.expectedOutput = event.expected_output;
          if (event.error) step.error = event.error;
          if (event.parent_step_id) step.parentId = event.parent_step_id;
        };

        const linkParent = (childId: string, parentId?: string) => {
          if (!parentId) return;
          const parent = graph.steps.find((s) => s.id === parentId);
          if (!parent) return;
          if (!parent.childrenIds) parent.childrenIds = [];
          if (!parent.childrenIds.includes(childId)) parent.childrenIds.push(childId);
        };

        let existing = graph.steps.find((s) => s.id === stepId);

        if (status === "running") {
          if (!existing) {
            const newStep: ExecutionStep = {
              id: stepId,
              name: event.name || stepId,
              type: stepType,
              status: "running",
              startedAt: new Date(),
              sub: event.sub,
              chips: event.chips,
              activeSkills: event.active_skills,
              skillsInvoked: event.skills_invoked,
              skillsLoaded: event.skills_loaded,
              childrenIds: [],
            };
            patchBrief(newStep);
            graph.steps.push(newStep);
            linkParent(stepId, event.parent_step_id);
          } else {
            existing.status = "running";
            existing.startedAt = new Date();
            if (event.sub) existing.sub = event.sub;
            if (event.chips) existing.chips = event.chips;
            if (event.active_skills) existing.activeSkills = event.active_skills;
            if (event.skills_loaded) existing.skillsLoaded = event.skills_loaded;
            patchBrief(existing);
          }
        } else {
          // completed | failed | cancelled | redirected | error
          const mapped =
            status === "error" ? "error" : status;
          if (existing) {
            existing.status = mapped;
            existing.completedAt = new Date();
            existing.duration = event.duration;
            if (event.sub) existing.sub = event.sub;
            if (event.chips) existing.chips = event.chips;
            if (event.active_skills) existing.activeSkills = event.active_skills;
            if (event.skills_invoked) existing.skillsInvoked = event.skills_invoked;
            if (event.skills_loaded) existing.skillsLoaded = event.skills_loaded;
            patchBrief(existing);
          } else {
            const newStep: ExecutionStep = {
              id: stepId,
              name: event.name || stepId,
              type: stepType,
              status: mapped,
              completedAt: new Date(),
              duration: event.duration,
              sub: event.sub,
              chips: event.chips,
              skillsInvoked: event.skills_invoked,
              skillsLoaded: event.skills_loaded,
              childrenIds: [],
            };
            patchBrief(newStep);
            graph.steps.push(newStep);
            linkParent(stepId, event.parent_step_id);
          }
        }
      });
    },

    getActiveExecution: () => {
      const state = get();
      const entries = Object.values(state.activeExecutions);
      return entries[0]; // Return first active execution
    },

    getLatestExecution: () => {
      const state = get();
      // Prefer active, then most recent completed
      const active = Object.values(state.activeExecutions);
      if (active.length > 0) return active[0];
      const completed = Object.values(state.completedExecutions);
      if (completed.length === 0) return undefined;
      return completed[completed.length - 1];
    },

    getExecutionPath: (messageId) => {
      const graph = get().getExecution(messageId);
      if (!graph) return [];

      // Skip the auto-created root "Start" step
      return graph.steps
        .filter((s) => s.name !== "Start")
        .map((step) => ({
          name: step.name,
          duration: step.duration || 0,
        }));
    },

    isExecutionComplete: (messageId) => {
      const graph = get().getExecution(messageId);
      return graph?.status === "completed" || graph?.status === "error";
    },

    remapExecution: (oldMessageId, newMessageId) => {
      if (!newMessageId || oldMessageId === newMessageId) return;
      set((state) => {
        // Remap in active executions
        if (state.activeExecutions[oldMessageId]) {
          const graph = state.activeExecutions[oldMessageId];
          graph.messageId = newMessageId;
          state.activeExecutions[newMessageId] = graph;
          delete state.activeExecutions[oldMessageId];
        }
        // Remap in completed executions
        if (state.completedExecutions[oldMessageId]) {
          const graph = state.completedExecutions[oldMessageId];
          graph.messageId = newMessageId;
          state.completedExecutions[newMessageId] = graph;
          delete state.completedExecutions[oldMessageId];
        }
      });
    },

    haltActiveSteps: () => {
      set((state) => {
        // Latch even if stream already finished (Fail Fast / Halt idempotent)
        state.worldStopped = true;
        const graphs = [
          ...Object.values(state.activeExecutions),
          ...Object.values(state.completedExecutions),
        ];
        for (const graph of graphs) {
          for (const step of graph.steps) {
            if (step.status === "running") {
              step.status = "cancelled";
              step.completedAt = new Date();
              step.chips = [...(step.chips || []).filter((c) => c !== "running"), "halt"];
            }
          }
        }
        state.isThinking = false;
      });
    },

    redirectActiveSteps: () => {
      set((state) => {
        const graphs = [
          ...Object.values(state.activeExecutions),
          ...Object.values(state.completedExecutions),
        ];
        for (const graph of graphs) {
          for (const step of graph.steps) {
            if (step.status === "running") {
              step.status = "redirected";
              step.completedAt = new Date();
              step.chips = [
                ...(step.chips || []).filter((c) => c !== "running"),
                "redirect",
                "steer-main",
              ];
            }
          }
        }
        state.isThinking = false;
      });
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
