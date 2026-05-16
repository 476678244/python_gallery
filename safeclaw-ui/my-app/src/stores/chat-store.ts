import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Message, Session, SkillNode } from '@/types';

interface ChatState {
  // Messages
  messages: Message[];
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  clearMessages: () => void;
  
  // Input
  input: string;
  setInput: (input: string) => void;
  attachments: File[];
  setAttachments: (attachments: File[]) => void;
  
  // Streaming
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
  currentStreamingContent: string;
  setCurrentStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  
  // Sessions
  sessions: Session[];
  currentSessionId: string | null;
  setSessions: (sessions: Session[]) => void;
  setCurrentSession: (id: string) => void;
  createSession: () => string;
  
  // Skills
  skillTree: SkillNode[];
  enabledSkills: Set<string>;
  setSkillTree: (tree: SkillNode[]) => void;
  toggleSkill: (skillId: string) => void;
  toggleFolder: (folderId: string) => void;
  expandNode: (nodeId: string, expanded: boolean) => void;
  
  // Model
  selectedModel: string;
  setSelectedModel: (model: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Messages
      messages: [],
      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),
      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map(m => m.id === id ? { ...m, ...updates } : m)
      })),
      clearMessages: () => set({ messages: [] }),
      
      // Input
      input: '',
      setInput: (input) => set({ input }),
      attachments: [],
      setAttachments: (attachments) => set({ attachments }),
      
      // Streaming
      isStreaming: false,
      setIsStreaming: (isStreaming) => set({ isStreaming }),
      currentStreamingContent: '',
      setCurrentStreamingContent: (content) => set({ currentStreamingContent: content }),
      appendStreamingContent: (chunk) => set((state) => ({ 
        currentStreamingContent: state.currentStreamingContent + chunk 
      })),
      
      // Sessions
      sessions: [],
      currentSessionId: null,
      setSessions: (sessions) => set({ sessions }),
      setCurrentSession: (id) => set({ currentSessionId: id }),
      createSession: () => {
        const id = crypto.randomUUID();
        const newSession: Session = {
          id,
          title: 'New Chat',
          messageCount: 0,
          lastActivity: new Date(),
          isActive: true,
        };
        set((state) => ({
          sessions: [newSession, ...state.sessions.map(s => ({ ...s, isActive: false }))],
          currentSessionId: id,
          messages: [],
        }));
        return id;
      },
      
      // Skills
      skillTree: [],
      enabledSkills: new Set(),
      setSkillTree: (tree) => set({ skillTree: tree }),
      toggleSkill: (skillId) => set((state) => {
        const newEnabled = new Set(state.enabledSkills);
        if (newEnabled.has(skillId)) {
          newEnabled.delete(skillId);
        } else {
          newEnabled.add(skillId);
        }
        return { enabledSkills: newEnabled };
      }),
      toggleFolder: (folderId) => set((state) => {
        const toggleNode = (nodes: SkillNode[]): SkillNode[] => {
          return nodes.map(node => {
            if (node.id === folderId) {
              const newEnabled = !node.enabled;
              return {
                ...node,
                enabled: newEnabled,
                children: toggleChildren(node.children, newEnabled),
              };
            }
            return { ...node, children: toggleNode(node.children) };
          });
        };
        const toggleChildren = (children: SkillNode[], enabled: boolean): SkillNode[] => {
          return children.map(child => ({
            ...child,
            enabled,
            children: child.children ? toggleChildren(child.children, enabled) : [],
          }));
        };
        return { skillTree: toggleNode(state.skillTree) };
      }),
      expandNode: (nodeId, expanded) => set((state) => {
        const expandNode = (nodes: SkillNode[]): SkillNode[] => {
          return nodes.map(node => {
            if (node.id === nodeId) {
              return { ...node, expanded };
            }
            return { ...node, children: expandNode(node.children) };
          });
        };
        return { skillTree: expandNode(state.skillTree) };
      }),
      
      // Model
      selectedModel: 'qwen/qwen3.5-35b-a3b',
      setSelectedModel: (model) => set({ selectedModel: model }),
    }),
    {
      name: 'safeclaw-chat-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        selectedModel: state.selectedModel,
        enabledSkills: Array.from(state.enabledSkills),
      }),
    }
  )
);
