"use client";

import { useChatStore } from "@/stores/chat-store";
import { Sidebar } from "./sidebar";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { RightPanel } from "./right-panel";

export function ChatLayout() {
  const currentSessionId = useChatStore((state) => state.currentSessionId);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white">
      {/* Left Sidebar - Sessions & Skills */}
      <Sidebar />

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col min-w-0">
        <ChatHeader />
        
        <div className="flex-1 overflow-hidden">
          {currentSessionId ? (
            <MessageList />
          ) : (
            <div className="flex h-full items-center justify-center text-slate-400">
              <div className="text-center">
                <div className="text-4xl mb-4">🛡️</div>
                <p className="text-lg font-medium">Welcome to SafeClaw</p>
                <p className="text-sm">Start a new chat to begin</p>
              </div>
            </div>
          )}
        </div>

        <ChatInput />
      </div>

      {/* Right Panel - Execution Graph & Context */}
      <RightPanel />
    </div>
  );
}
