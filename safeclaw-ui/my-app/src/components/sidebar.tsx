"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Plus, 
  MessageSquare, 
  Settings, 
  Shield,
  ChevronDown,
  Trash2,
  Folder,
  TreePine,
  MoreVertical,
  Loader2
} from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { useSessions } from "@/hooks/use-sessions";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import { cn } from "@/lib/utils";
import { SkillTree } from "./skill-tree";

export function Sidebar() {
  const [sessionsOpen, setSessionsOpen] = useState(true);
  const [skillsOpen, setSkillsOpen] = useState(true);
  
  const { 
    currentSessionId, 
    createSession: createLocalSession, 
    setCurrentSession 
  } = useChatStore();

  const { sessions, isLoading, createSession, deleteSession, isCreating } = useSessions();

  return (
    <aside className="w-64 flex-shrink-0 border-r border-slate-200 bg-slate-50 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold text-slate-900">SafeClaw</span>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* New Chat Button */}
          <Button 
            onClick={() => {
              createLocalSession();
              createSession({ title: "New Chat" });
            }}
            className="w-full justify-start gap-2"
            variant="outline"
            disabled={isCreating}
          >
            {isCreating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            New Chat
          </Button>

          {/* Sessions Section */}
          <Collapsible open={sessionsOpen} onOpenChange={setSessionsOpen}>
            <CollapsibleTrigger className="flex items-center justify-between w-full px-2 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                <span>Sessions</span>
              </div>
              <motion.div
                animate={{ rotate: sessionsOpen ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-4 h-4" />
              </motion.div>
            </CollapsibleTrigger>
            
            <CollapsibleContent>
              <AnimatePresence>
                <div className="mt-1 space-y-0.5">
                  {isLoading ? (
                    <div className="px-2 py-3 text-xs text-slate-400 text-center">
                      <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                    </div>
                  ) : sessions.length === 0 ? (
                    <div className="px-2 py-3 text-xs text-slate-400 text-center">
                      No sessions yet
                    </div>
                  ) : (
                    sessions.map((session) => (
                      <motion.div
                        key={session.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        className="group relative"
                      >
                        <button
                          onClick={() => setCurrentSession(session.id)}
                          className={cn(
                            "w-full flex items-center justify-between px-2 py-2 text-sm rounded-md transition-all",
                            currentSessionId === session.id
                              ? "bg-blue-50 text-blue-700 border border-blue-200"
                              : "text-slate-600 hover:bg-slate-100"
                          )}
                        >
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <span className="truncate">{session.title}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-slate-400 flex-shrink-0">
                              {session.messageCount}
                            </span>
                            {/* Delete button - visible on hover */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteSession(session.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 hover:text-red-600 transition-all"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </button>
                      </motion.div>
                    ))
                  )}
                </div>
              </AnimatePresence>
            </CollapsibleContent>
          </Collapsible>

          {/* Workspaces */}
          <div className="space-y-1">
            <div className="px-2 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Workspaces
            </div>
            {[
              { name: "Coupaing Research", color: "bg-green-500" },
              { name: "Macan Tire Analysis", color: "bg-amber-500" },
              { name: "Agent Development", color: "bg-blue-500" },
            ].map((workspace) => (
              <button
                key={workspace.name}
                className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
              >
                <div className={`w-2 h-2 rounded-full ${workspace.color}`} />
                <span className="truncate">{workspace.name}</span>
              </button>
            ))}
            <button className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors">
              <Plus className="w-4 h-4" />
              <span>New Workspace</span>
            </button>
          </div>

          {/* Skill Tree Section */}
          <Collapsible open={skillsOpen} onOpenChange={setSkillsOpen}>
            <CollapsibleTrigger className="flex items-center justify-between w-full px-2 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors">
              <div className="flex items-center gap-2">
                <TreePine className="w-4 h-4" />
                <span>Skills</span>
              </div>
              <motion.div
                animate={{ rotate: skillsOpen ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-4 h-4" />
              </motion.div>
            </CollapsibleTrigger>
            
            <CollapsibleContent>
              <div className="mt-2">
                <SkillTree />
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </ScrollArea>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-slate-200 space-y-1">
        <button className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md transition-colors">
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </button>
        <div className="flex items-center gap-2 px-2 py-1.5">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">Junho</p>
            <p className="text-xs text-slate-500">Pro Plan</p>
          </div>
          <MoreVertical className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    </aside>
  );
}
