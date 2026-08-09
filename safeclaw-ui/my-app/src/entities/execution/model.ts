/**
 * Execution Entity - Domain Model
 * Represents agent execution flow and reasoning steps
 */

export type ExecutionStatus =
  | "pending"
  | "running"
  | "completed"
  | "error"
  | "cancelled"
  | "failed"
  | "redirected";
export type ExecutionStepType =
  | "reasoning"
  | "tool_call"
  | "model_call"
  | "context_retrieval"
  | "user_input"
  | "output"
  | "subagent";

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
  /** Actual names passed to create_deep_agent (not BM25 router). */
  skillsLoaded?: string[];
  /** Spawn brief — 走一步看三步 */
  agentName?: string;
  stepNow?: string;
  lookAhead?: string[];
  expectedOutput?: string;
  metadata?: {
    toolName?: string;
    modelName?: string;
    tokenCount?: number;
    contextSize?: number;
  };
}

export interface LLMCall {
  callId: string;
  callNumber: number;
  timestamp: Date;
  status: ExecutionStatus;
  // Execution path for this specific call
  steps: ExecutionStep[];
  // Skills for this specific call
  activeSkills?: string[];
  skillsInvoked?: string[];
  skillsLoaded?: string[];
  // Token counts
  promptTokens?: number;
  completionTokens?: number;
  // Timing
  durationMs?: number;
  // Response content (for reference)
  responsePreview?: string;
}

export interface ExecutionGraph {
  id: string;
  sessionId: string;
  messageId: string;
  status: ExecutionStatus;
  steps: ExecutionStep[];  // Legacy: overall steps
  rootStepId: string;
  startedAt: Date;
  completedAt?: Date;
  totalDuration?: number;
  // New: LLM calls with their own execution paths
  llmCalls: LLMCall[];
  // Current active call index for UI
  currentCallIndex: number;
  metadata?: {
    totalTokens?: number;
    skillsUsed?: string[];
    modelsUsed?: string[];
    totalCalls?: number;
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
    llmCalls: [],
    currentCallIndex: 0,
  };
}

// Factory for LLMCall
export function createLLMCall(
  callNumber: number,
  callId?: string
): LLMCall {
  return {
    callId: callId || crypto.randomUUID(),
    callNumber,
    timestamp: new Date(),
    status: "running",
    steps: [],
    activeSkills: [],
    skillsInvoked: [],
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
