"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, 
  Bot, 
  BarChart3, 
  Globe, 
  Cpu, 
  CheckCircle2, 
  Clock,
  Zap,
  Layers,
  FileText,
  Settings
} from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { cn } from "@/lib/utils";

type TabId = 'agent' | 'skills' | 'context';

const TABS = [
  { id: 'agent' as TabId, label: 'Agent Brain', icon: Bot },
  { id: 'skills' as TabId, label: 'Skills', icon: Layers },
  { id: 'context' as TabId, label: 'Context', icon: FileText },
];

// Mock execution graph data
const EXECUTION_STEPS = [
  {
    id: 'user-query',
    name: 'User Query',
    description: 'Analyze the global market for Porsche Macan tires',
    status: 'completed' as const,
    duration: 0.1,
    icon: FileText,
    color: 'bg-blue-500',
  },
  {
    id: 'intent',
    name: 'Intent Classification',
    description: 'Market Analysis',
    status: 'completed' as const,
    duration: 0.3,
    icon: Bot,
    color: 'bg-green-500',
  },
  {
    id: 'skill-matching',
    name: 'Skill Matching',
    description: '5 skills matched',
    status: 'completed' as const,
    duration: 0.5,
    icon: Layers,
    color: 'bg-green-500',
  },
  {
    id: 'tool-routing',
    name: 'Tool Routing',
    description: 'Web Search + Data Analysis',
    status: 'completed' as const,
    duration: 0.4,
    icon: Globe,
    color: 'bg-green-500',
  },
  {
    id: 'model-selection',
    name: 'Model Selection',
    description: 'Gemma 4B',
    status: 'completed' as const,
    duration: 0.2,
    icon: Cpu,
    color: 'bg-purple-500',
  },
  {
    id: 'execution',
    name: 'Execution',
    description: '5/5 steps completed',
    status: 'completed' as const,
    duration: 9.2,
    icon: Zap,
    color: 'bg-green-500',
  },
  {
    id: 'final-response',
    name: 'Final Response',
    description: 'Market analysis report',
    status: 'completed' as const,
    duration: 0.3,
    icon: CheckCircle2,
    color: 'bg-blue-500',
  },
];

const SKILLS_USED = [
  { name: 'web-search', icon: Globe, duration: 1.2, color: 'text-blue-500' },
  { name: 'data-analyzer', icon: BarChart3, duration: 2.1, color: 'text-amber-500' },
  { name: 'market-researcher', icon: Zap, duration: 1.8, color: 'text-purple-500' },
  { name: 'price-tracker', icon: FileText, duration: 2.3, color: 'text-green-500' },
  { name: 'trend-analyzer', icon: Bot, duration: 1.6, color: 'text-cyan-500' },
];

const CONTEXT_ITEMS = [
  { label: 'Web Results', value: '24 sources', icon: Globe },
  { label: 'Market Data', value: '2024 Q4', icon: BarChart3 },
  { label: 'User Preferences', value: 'Tire focus', icon: Settings },
];

function ExecutionGraph() {
  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Execution Graph</h3>
      <div className="space-y-3">
        {EXECUTION_STEPS.map((step, index) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="relative"
          >
            {/* Connection line */}
            {index < EXECUTION_STEPS.length - 1 && (
              <div className="absolute left-4 top-8 w-0.5 h-6 bg-slate-200" />
            )}
            
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className={`w-8 h-8 rounded-full ${step.color} flex items-center justify-center flex-shrink-0`}>
                <step.icon className="w-4 h-4 text-white" />
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900">{step.name}</span>
                  {step.duration > 0 && (
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {step.duration}s
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">{step.description}</p>
              </div>
              
              {/* Status */}
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function SkillsPanel() {
  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Skills Used (5)</h3>
      <div className="space-y-2">
        {SKILLS_USED.map((skill) => (
          <motion.div
            key={skill.name}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <skill.icon className={`w-4 h-4 ${skill.color}`} />
              <span className="text-sm text-slate-700">{skill.name}</span>
            </div>
            <span className="text-xs text-slate-400">{skill.duration}s</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function ContextPanel() {
  const { messages } = useChatStore();
  const lastMessage = messages[messages.length - 1];
  
  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Context</h3>
      <div className="space-y-3">
        {CONTEXT_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center justify-between p-2 rounded-lg bg-slate-50">
            <div className="flex items-center gap-2">
              <item.icon className="w-4 h-4 text-slate-500" />
              <span className="text-sm text-slate-700">{item.label}</span>
            </div>
            <span className="text-xs font-medium text-slate-900">{item.value}</span>
          </div>
        ))}
      </div>
      
      {/* Session Overview */}
      <div className="mt-6 p-3 rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-100">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">Session Overview</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-slate-500">Model</p>
            <p className="text-sm font-medium text-slate-900">Gemma 4 4B</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Status</p>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-medium text-green-600">Completed</span>
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-500">Duration</p>
            <p className="text-sm font-medium text-slate-900">9.2s</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Tokens</p>
            <p className="text-sm font-medium text-slate-900">12,842</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function RightPanel() {
  const [activeTab, setActiveTab] = useState<TabId>('agent');

  return (
    <aside className="w-80 flex-shrink-0 border-l border-slate-200 bg-white flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition-colors",
              activeTab === tab.id
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'agent' && <ExecutionGraph />}
            {activeTab === 'skills' && <SkillsPanel />}
            {activeTab === 'context' && <ContextPanel />}
          </motion.div>
        </AnimatePresence>
      </ScrollArea>
    </aside>
  );
}
