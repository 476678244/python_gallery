"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  ChevronDown, 
  Globe, 
  Bot,
  Sparkles,
  Search
} from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

const MODELS = [
  { id: "gemma-4b", name: "Gemma 4B", icon: Bot },
  { id: "qwen-35b", name: "Qwen 3.5 35B", icon: Sparkles },
  { id: "gpt-oss", name: "GPT-OSS 20B", icon: Bot },
];

export function ChatHeader() {
  const { selectedModel, setSelectedModel } = useChatStore();
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);

  const currentModel = MODELS.find(m => m.id === selectedModel) || MODELS[0];

  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-4">
      {/* Left - Chat Title */}
      <div className="flex items-center gap-2">
        <h1 className="font-medium text-slate-900">Analyze Macan tire market</h1>
        <ChevronDown className="w-4 h-4 text-slate-400" />
      </div>

      {/* Right - Model & Tools */}
      <div className="flex items-center gap-3">
        {/* Model Selector */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2 text-slate-700">
              <currentModel.icon className="w-4 h-4" />
              <span className="text-sm">{currentModel.name}</span>
              <ChevronDown className="w-3 h-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {MODELS.map((model) => (
              <DropdownMenuItem 
                key={model.id}
                onClick={() => setSelectedModel(model.id)}
                className="gap-2"
              >
                <model.icon className="w-4 h-4" />
                {model.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Web Search Toggle */}
        <button
          onClick={() => setWebSearchEnabled(!webSearchEnabled)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
            webSearchEnabled 
              ? "bg-green-100 text-green-700" 
              : "bg-slate-100 text-slate-600"
          }`}
        >
          <Globe className="w-3 h-3" />
          <span>Web Search</span>
          <motion.div
            className="w-1.5 h-1.5 rounded-full"
            animate={{ 
              backgroundColor: webSearchEnabled ? "#22c55e" : "#94a3b8",
              scale: webSearchEnabled ? [1, 1.2, 1] : 1
            }}
            transition={{ duration: 0.3, repeat: webSearchEnabled ? Infinity : 0, repeatDelay: 1 }}
          />
        </button>
      </div>
    </header>
  );
}
