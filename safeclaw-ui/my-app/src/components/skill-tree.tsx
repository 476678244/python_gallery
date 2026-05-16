"use client";

import { motion } from "framer-motion";
import { 
  Folder, 
  FileCode, 
  ChevronRight, 
  ChevronDown,
  Check,
  X
} from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { cn } from "@/lib/utils";

interface SkillNode {
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

// Mock skill tree data - in real app, fetch from API
const MOCK_SKILL_TREE: SkillNode[] = [
  {
    id: "web-search",
    name: "web-search",
    path: "built_in/web-search",
    isFolder: false,
    enabled: true,
    expanded: false,
    children: [],
    skillEntry: {
      name: "web-search",
      description: "Search the web for information",
      version: "1.0.0",
      author: "SafeClaw"
    }
  },
  {
    id: "data-analyzer",
    name: "data-analyzer",
    path: "built_in/data-analyzer",
    isFolder: false,
    enabled: true,
    expanded: false,
    children: [],
    skillEntry: {
      name: "data-analyzer",
      description: "Analyze data and generate insights",
      version: "1.0.0",
      author: "SafeClaw"
    }
  },
  {
    id: "stock-13f",
    name: "stock_13f_analysis",
    path: "private_skills/stock_13f_analysis",
    isFolder: false,
    enabled: false,
    expanded: false,
    children: [],
    skillEntry: {
      name: "stock_13f_analysis",
      description: "Analyze 13F stock filings",
      version: "1.0.0",
      author: "SafeClaw"
    }
  },
  {
    id: "market-research",
    name: "market-researcher",
    path: "built_in/market-researcher",
    isFolder: false,
    enabled: true,
    expanded: false,
    children: [],
    skillEntry: {
      name: "market-researcher",
      description: "Research market trends and data",
      version: "1.0.0",
      author: "SafeClaw"
    }
  },
  {
    id: "price-tracker",
    name: "price-tracker",
    path: "built_in/price-tracker",
    isFolder: false,
    enabled: true,
    expanded: false,
    children: [],
    skillEntry: {
      name: "price-tracker",
      description: "Track prices and costs",
      version: "1.0.0",
      author: "SafeClaw"
    }
  },
];

interface SkillNodeItemProps {
  node: SkillNode;
  depth?: number;
}

function SkillNodeItem({ node, depth = 0 }: SkillNodeItemProps) {
  const { toggleSkill, expandNode, enabledSkills, skillTree } = useChatStore();
  
  const isEnabled = enabledSkills.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const paddingLeft = depth * 12;

  return (
    <div style={{ paddingLeft }}>
      <div className="flex items-center gap-1.5 py-1 px-1 rounded-md hover:bg-slate-100 group">
        {/* Expand/Collapse for folders */}
        {hasChildren ? (
          <button
            onClick={() => expandNode(node.id, !node.expanded)}
            className="p-0.5 rounded hover:bg-slate-200"
          >
            {node.expanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}

        {/* Toggle checkbox */}
        <button
          onClick={() => toggleSkill(node.id)}
          className={cn(
            "w-4 h-4 rounded border flex items-center justify-center transition-colors",
            isEnabled
              ? "bg-blue-500 border-blue-500"
              : "border-slate-300 hover:border-slate-400"
          )}
        >
          {isEnabled && <Check className="w-3 h-3 text-white" />}
        </button>

        {/* Icon */}
        {node.isFolder ? (
          <Folder className="w-4 h-4 text-amber-500" />
        ) : (
          <FileCode className="w-4 h-4 text-blue-500" />
        )}

        {/* Name */}
        <span className={cn(
          "text-xs truncate",
          isEnabled ? "text-slate-900" : "text-slate-500"
        )}>
          {node.name}
        </span>

        {/* Hover tooltip */}
        {node.skillEntry && (
          <div className="opacity-0 group-hover:opacity-100 absolute left-full ml-2 z-50 bg-slate-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap pointer-events-none transition-opacity">
            {node.skillEntry.description}
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && node.expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-0.5"
        >
          {node.children.map((child) => (
            <SkillNodeItem key={child.id} node={child} depth={depth + 1} />
          ))}
        </motion.div>
      )}
    </div>
  );
}

export function SkillTree() {
  const { skillTree, setSkillTree } = useChatStore();

  // Use mock data if no skill tree loaded
  const displayTree = skillTree.length > 0 ? skillTree : MOCK_SKILL_TREE;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-xs text-slate-500">56 skills available</span>
        <button className="text-xs text-blue-600 hover:text-blue-700">
          Manage
        </button>
      </div>
      
      <div className="space-y-0.5">
        {displayTree.map((node) => (
          <SkillNodeItem key={node.id} node={node} />
        ))}
      </div>
    </div>
  );
}
