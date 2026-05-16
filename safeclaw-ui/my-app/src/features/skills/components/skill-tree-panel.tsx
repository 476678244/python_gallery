/**
 * Skill Tree Panel - Feature Component
 * 
 * Business: Skill management, enable/disable, organization
 * Responsibility: Skill tree rendering and interaction
 */

"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { Folder, FileCode, ChevronRight, ChevronDown, Loader2 } from "lucide-react";
import { useSkillStore } from "@/stores/skill-store";
import { SkillTreeNode } from "@/entities/skill";
import { cn } from "@/shared/utils/cn";
import { Switch } from "@/shared/components/ui/switch";

function isFolderEnabled(node: SkillTreeNode, enabledSkillIds: Set<string>): boolean {
  if (!node.children || node.children.length === 0) return false;
  return node.children.some((child) =>
    child.isFolder
      ? isFolderEnabled(child, enabledSkillIds)
      : enabledSkillIds.has(child.id)
  );
}

export function SkillTreePanel() {
  const { 
    skillTree, 
    isLoading, 
    expandedFolderIds,
    loadSkills 
  } = useSkillStore();

  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-2">
      <div className="space-y-1">
        {skillTree.map((node) => (
          <SkillNodeItem key={node.id} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
}

interface SkillNodeItemProps {
  node: SkillTreeNode;
  depth: number;
}

function SkillNodeItem({ node, depth }: SkillNodeItemProps) {
  const { 
    isEnabled,
    enabledSkillIds,
    toggleSkill, 
    toggleFolder, 
    isExpanded, 
    toggleFolderExpanded,
    isToggling 
  } = useSkillStore();

  const enabled = node.isFolder ? isFolderEnabled(node, enabledSkillIds) : isEnabled(node.id);
  const expanded = isExpanded(node.id);
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = async () => {
    if (node.isFolder) {
      await toggleFolder(node.id);
    } else {
      await toggleSkill(node.id);
    }
  };

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md",
          "hover:bg-slate-100 transition-colors group",
          depth > 0 && "ml-4"
        )}
      >
        {/* Expand/Collapse button for folders */}
        {node.isFolder ? (
          <button
            onClick={() => toggleFolderExpanded(node.id)}
            className="p-0.5 rounded hover:bg-slate-200 transition-colors"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-500" />
            )}
          </button>
        ) : (
          <span className="w-5" /> // Spacer for alignment
        )}

        {/* Icon */}
        {node.isFolder ? (
          <Folder className="w-4 h-4 text-blue-500" />
        ) : (
          <FileCode className="w-4 h-4 text-slate-500" />
        )}

        {/* Name */}
        <span className={cn(
          "flex-1 text-sm truncate",
          node.isFolder ? "font-medium text-slate-700" : "text-slate-600",
          !enabled && !node.isFolder && "text-slate-400"
        )}>
          {node.name}
        </span>

        {/* Toggle Switch */}
        <Switch
          checked={enabled}
          onCheckedChange={handleToggle}
          disabled={isToggling}
          size="sm"
        />
      </div>

      {/* Children */}
      {node.isFolder && expanded && hasChildren && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-1"
        >
          {node.children!.map((child) => (
            <SkillNodeItem key={child.id} node={child} depth={depth + 1} />
          ))}
        </motion.div>
      )}
    </div>
  );
}
