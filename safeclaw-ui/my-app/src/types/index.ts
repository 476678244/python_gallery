export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    agent?: string;
    executionPath?: string[];
    processingTime?: number;
    thinking?: ThinkingStep[];
  };
}

export interface ThinkingStep {
  id: string;
  name: string;
  content: string;
  timestamp: Date;
  duration?: number;
  status: 'running' | 'completed' | 'error';
}

export interface SkillNode {
  id: string;
  name: string;
  path: string;
  isFolder: boolean;
  enabled: boolean;
  expanded: boolean;
  children: SkillNode[];
  skillEntry?: {
    name: string;
    description: string;
    version: string;
    author: string;
  };
}

export interface Session {
  id: string;
  title: string;
  messageCount: number;
  lastActivity: Date;
  isActive: boolean;
}

export interface ExecutionNode {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  duration?: number;
  children?: ExecutionNode[];
}

export interface ChatRequest {
  messages: { role: string; content: string }[];
  sessionId?: string;
  enabledSkills?: string[];
}

export interface ChatResponseChunk {
  content?: string;
  tool?: string;
  toolContent?: string;
  thinking?: string;
  done?: boolean;
}
