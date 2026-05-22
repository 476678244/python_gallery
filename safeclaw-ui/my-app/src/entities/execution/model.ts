/**
 * Execution Entity - Domain Model
 * Represents agent execution flow and reasoning steps
 */

export type ExecutionStatus = "pending" | "running" | "completed" | "error" | "cancelled";
export type ExecutionStepType = "reasoning" | "tool_call" | "model_call" | "context_retrieval" | "user_input" | "output";

export interface ExecutionStep {
  id: string;
  name: string;
  type: ExecutionStepType;
  status: ExecutionStatus;
  startedAt?: Date;
  completedAt?: Date;
  duration?: number; // in seconds
  input?: unknown;
  output?: unknown;
  error?: string;
  parentId?: string;
  childrenIds?: string[];
  sub?: string;
  chips?: string[];
  activeSkills?: string[];
  skillsInvoked?: string[];
  metadata?: {
    toolName?: string;
    modelName?: string;
    tokenCount?: number;
    contextSize?: number;
  };
}

export interface ExecutionGraph {
  id: string;
  sessionId: string;
  messageId: string;
  status: ExecutionStatus;
  steps: ExecutionStep[];
  rootStepId: string;
  startedAt: Date;
  completedAt?: Date;
  totalDuration?: number;
  metadata?: {
    totalTokens?: number;
    skillsUsed?: string[];
    modelsUsed?: string[];
  };
}

export interface ExecutionPath {
  name: string;
  duration: number;
  type: ExecutionStepType;
  status: ExecutionStatus;
}

// Factory functions
export function createExecutionStep(
  name: string,
  type: ExecutionStepType,
  parentId?: string
): ExecutionStep {
  return {
    id: crypto.randomUUID(),
    name,
    type,
    status: "pending",
    parentId,
    childrenIds: [],
  };
}

export function createExecutionGraph(
  sessionId: string,
  messageId: string
): ExecutionGraph {
  const rootStep = createExecutionStep("Start", "reasoning");
  return {
    id: crypto.randomUUID(),
    sessionId,
    messageId,
    status: "running",
    steps: [rootStep],
    rootStepId: rootStep.id,
    startedAt: new Date(),
  };
}

// State transitions
export function startStep(step: ExecutionStep): ExecutionStep {
  return {
    ...step,
    status: "running",
    startedAt: new Date(),
  };
}

export function completeStep(step: ExecutionStep, output?: unknown): ExecutionStep {
  const completedAt = new Date();
  const duration = step.startedAt
    ? (completedAt.getTime() - step.startedAt.getTime()) / 1000
    : undefined;

  return {
    ...step,
    status: "completed",
    completedAt,
    duration,
    output,
  };
}

export function failStep(step: ExecutionStep, error: string): ExecutionStep {
  return {
    ...step,
    status: "error",
    error,
    completedAt: new Date(),
  };
}

// Utilities
export function getExecutionPath(graph: ExecutionGraph): ExecutionPath[] {
  return graph.steps.map((step) => ({
    name: step.name,
    duration: step.duration || 0,
    type: step.type,
    status: step.status,
  }));
}

export function getActiveSteps(graph: ExecutionGraph): ExecutionStep[] {
  return graph.steps.filter((s) => s.status === "running");
}

export function getCompletedSteps(graph: ExecutionGraph): ExecutionStep[] {
  return graph.steps.filter((s) => s.status === "completed");
}

export function calculateTotalDuration(graph: ExecutionGraph): number {
  if (graph.totalDuration) return graph.totalDuration;
  if (graph.completedAt && graph.startedAt) {
    return (graph.completedAt.getTime() - graph.startedAt.getTime()) / 1000;
  }
  return graph.steps.reduce((sum, step) => sum + (step.duration || 0), 0);
}
