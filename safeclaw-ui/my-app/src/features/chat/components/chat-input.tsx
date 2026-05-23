/**
 * Chat Input - Feature Component
 * 
 * Business: Message input, quick actions, file attachments, slash commands
 * Responsibility: Input handling, validation, submission, file upload, skill autocomplete
 */

"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Send, Paperclip, Mic, Plus, Code, FileText, Sparkles, X, File, Command, Check } from "lucide-react";
import { useMessageStore } from "@/stores/message-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useSkillStore } from "@/stores/skill-store";
import { streamChat } from "@/features/chat/services/chat-api";
import { cn } from "@/shared/utils/cn";

const QUICK_ACTIONS = [
  { icon: Sparkles, label: "Research", color: "text-purple-500" },
  { icon: FileText, label: "Analyze", color: "text-blue-500" },
  { icon: Code, label: "Code", color: "text-amber-500" },
  { icon: Plus, label: "Context", color: "text-slate-500" },
];

export interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
}

export interface SkillSuggestion {
  id: string;
  name: string;
  description?: string;
  category?: string;
}

interface ChatInputProps {
  sessionId?: string | null;
  disabled?: boolean;
  onFileUpload?: (files: UploadedFile[]) => void;
}

import { useSessionStore } from "@/stores/session-store";

export function ChatInput({ sessionId: sessionIdProp, disabled: disabledProp, onFileUpload }: ChatInputProps) {
  // Get session from store if not provided via props
  const { currentSessionId } = useSessionStore();
  const sessionId = sessionIdProp ?? currentSessionId;
  const disabled = disabledProp ?? !sessionId;
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showSkillDropdown, setShowSkillDropdown] = useState(false);
  const [skillFilter, setSkillFilter] = useState("");
  const [selectedSkillIndex, setSelectedSkillIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const skillDropdownRef = useRef<HTMLDivElement>(null);

  // Get enabled skills from skill store
  const { enabledSkillIds, flatSkills, loadSkills } = useSkillStore();
  
  // Load skills on mount
  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  // Get all enabled skills as suggestions
  const enabledSkills: SkillSuggestion[] = flatSkills
    .filter(skill => enabledSkillIds.has(skill.id) && !skill.isFolder)
    .map(skill => ({
      id: skill.id,
      name: skill.name,
      description: skill.entry?.description,
      category: skill.category,
    }));

  // Filter skills based on input
  const filteredSkills = skillFilter
    ? enabledSkills.filter(skill =>
        skill.name.toLowerCase().includes(skillFilter.toLowerCase()) ||
        skill.description?.toLowerCase().includes(skillFilter.toLowerCase())
      )
    : enabledSkills;

  const {
    addUserMessage,
    startStreaming,
    appendStreamingContent,
    completeStreaming,
    cancelStreaming,
    isStreaming,
    getMessagesForSession,
  } = useMessageStore();

  const {
    startExecution,
    addThinkingStep,
    completeThinkingStep,
    setThinking,
    completeExecution,
    handleExecutionStepEvent,
  } = useExecutionStore();

  const handleSubmit = useCallback(async () => {
    if ((!input.trim() && uploadedFiles.length === 0) || isStreaming || !sessionId) return;

    const content = input.trim();
    const files = [...uploadedFiles];
    
    // Reset state
    setInput("");
    setUploadedFiles([]);
    setShowSkillDropdown(false);

    // Add user message (with file references if any)
    const messageContent = files.length > 0
      ? `${content}\n\n[Attached files: ${files.map(f => f.name).join(", ")}]`
      : content;
    const userMessage = addUserMessage(messageContent, sessionId);
    
    // Notify parent about file uploads
    if (files.length > 0 && onFileUpload) {
      onFileUpload(files);
    }

    // Get all messages for context
    const messages = getMessagesForSession(sessionId);
    const apiMessages = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    // Start streaming
    const streamingId = startStreaming(sessionId);
    startExecution(sessionId, streamingId);
    setThinking(true);

    // Stream chat
    await streamChat(
      {
        messages: apiMessages,
        sessionId: sessionId,
      },
      {
        onThinking: (step) => {
          addThinkingStep(step);
        },
        onExecutionStep: (event) => {
          handleExecutionStepEvent(streamingId, event);
        },
        onContent: (content) => {
          // Content updates handled in store
        },
        onComplete: (data) => {
          completeStreaming(data.message.content);
          completeExecution(streamingId, {
            totalTokens: data.usage?.totalTokens,
            skillsUsed: data.executionGraph?.metadata?.skillsUsed,
            totalDuration: data.timing?.totalDuration,
          });
          setThinking(false);
          // Persist after state update is flushed
          setTimeout(() => {
            const allMessages = getMessagesForSession(sessionId!);
            fetch(`/api/sessions/${sessionId}/messages`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                messages: allMessages.map((m) => ({
                  ...m,
                  timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp,
                })),
              }),
            }).catch(() => {});
          }, 0);
        },
        onError: (error) => {
          console.error("Chat error:", error);
          cancelStreaming();
          setThinking(false);
        },
      }
    );
  }, [
    input,
    isStreaming,
    sessionId,
    addUserMessage,
    getMessagesForSession,
    startStreaming,
    startExecution,
    setThinking,
    addThinkingStep,
    completeStreaming,
    completeExecution,
    cancelStreaming,
    handleExecutionStepEvent,
  ]);

  // File upload handlers - Uploads files to /tmp/uploaded
  const handleFileSelect = useCallback(async (files: FileList | null) => {
    if (!files) return;
    
    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // Upload files to /tmp/uploaded
    for (const uploadedFile of newFiles) {
      try {
        const formData = new FormData();
        formData.append('file', uploadedFile.file);
        formData.append('path', `/tmp/uploaded/${uploadedFile.name}`);
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          console.error(`Failed to upload ${uploadedFile.name}: HTTP ${response.status} - ${errorText}`);
        } else {
          const result = await response.json().catch(() => ({ success: true }));
          console.log(`Uploaded ${uploadedFile.name} to /tmp/uploaded/`, result);
        }
      } catch (error) {
        console.error(`Error uploading ${uploadedFile.name}:`, error);
      }
    }
  }, []);

  const handleRemoveFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  const handlePaperclipClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    // Handle file drop - upload to /tmp/uploaded
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleFileSelect(files);
    }
  }, [handleFileSelect]);

  // Slash command handlers
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart;
    
    setInput(value);
    
    // Check for slash command trigger
    const beforeCursor = value.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");
    
    if (lastSlashIndex !== -1) {
      const afterSlash = beforeCursor.slice(lastSlashIndex + 1);
      // Show dropdown if we're at a word boundary after slash (no spaces)
      if (!afterSlash.includes(" ") && !afterSlash.includes("\n")) {
        setSkillFilter(afterSlash);
        setShowSkillDropdown(true);
        setSelectedSkillIndex(0);
      } else {
        setShowSkillDropdown(false);
      }
    } else {
      setShowSkillDropdown(false);
    }
  }, []);

  const handleSkillSelect = useCallback((skill: SkillSuggestion) => {
    const cursorPos = textareaRef.current?.selectionStart || 0;
    const beforeCursor = input.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");
    
    if (lastSlashIndex !== -1) {
      const beforeSlash = input.slice(0, lastSlashIndex);
      const afterCursor = input.slice(cursorPos);
      const newValue = `${beforeSlash}/${skill.name}${afterCursor}`;
      setInput(newValue);
      setShowSkillDropdown(false);
      
      // Restore focus and set cursor position
      setTimeout(() => {
        if (textareaRef.current) {
          const newPos = lastSlashIndex + skill.name.length + 1;
          textareaRef.current.setSelectionRange(newPos, newPos);
          textareaRef.current.focus();
        }
      }, 0);
    }
  }, [input]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Handle skill dropdown navigation
    if (showSkillDropdown) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedSkillIndex(prev => 
          prev < filteredSkills.length - 1 ? prev + 1 : prev
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedSkillIndex(prev => prev > 0 ? prev - 1 : 0);
        return;
      }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (filteredSkills[selectedSkillIndex]) {
          handleSkillSelect(filteredSkills[selectedSkillIndex]);
        }
        return;
      }
      if (e.key === "Escape") {
        setShowSkillDropdown(false);
        return;
      }
    }
    
    // Normal submit
    if (e.key === "Enter" && !e.shiftKey && !showSkillDropdown) {
      e.preventDefault();
      handleSubmit();
    }
  }, [showSkillDropdown, filteredSkills, selectedSkillIndex, handleSkillSelect, handleSubmit]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (skillDropdownRef.current && !skillDropdownRef.current.contains(e.target as Node)) {
        setShowSkillDropdown(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div 
      className="border-t border-slate-200 bg-white p-4"
    >
      {/* Quick Actions */}
      <div className="flex gap-2 mb-3 overflow-x-auto">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs",
              "bg-slate-100 hover:bg-slate-200 transition-colors",
              "text-slate-600 whitespace-nowrap"
            )}
          >
            <action.icon className={cn("w-3.5 h-3.5", action.color)} />
            <span>{action.label}</span>
          </button>
        ))}
      </div>

      {/* Uploaded Files Preview */}
      {uploadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg text-sm"
            >
              <File className="w-4 h-4 text-slate-500" />
              <span className="text-slate-700 truncate max-w-[150px]">{file.name}</span>
              <span className="text-slate-400 text-xs">{formatFileSize(file.size)}</span>
              <button
                onClick={() => handleRemoveFile(file.id)}
                className="p-0.5 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area — entire box is the drop target */}
      <div
        className={cn(
          "relative flex items-end gap-2 rounded-xl border p-3 transition-all",
          isFocused
            ? "border-blue-500 ring-2 ring-blue-500/20"
            : "border-slate-200 hover:border-slate-300",
          isDragging && "border-blue-500 border-dashed bg-blue-50"
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* Drag overlay inside input area */}
        {isDragging && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-blue-50/80 pointer-events-none">
            <div className="flex items-center gap-2">
              <File className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-blue-600">Drop files here</span>
            </div>
          </div>
        )}

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={(e) => handleFileSelect(e.target.files)}
          className="hidden"
          accept="*/*"
        />

        {/* Attachment Button */}
        <button
          onClick={handlePaperclipClick}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          title="Upload files to /tmp/uploaded"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Text Input with Skill Dropdown */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={disabled ? "Select a session to start chatting..." : "Ask anything... Use / for skills"}
            disabled={disabled || isStreaming}
            rows={1}
            className={cn(
              "w-full resize-none bg-transparent outline-none",
              "text-slate-900 placeholder:text-slate-400",
              "min-h-[24px] max-h-[200px]"
            )}
            style={{ height: "auto" }}
          />
          
          {/* Skill Suggestion Dropdown */}
          {showSkillDropdown && filteredSkills.length > 0 && (
            <div
              ref={skillDropdownRef}
              className="absolute bottom-full left-0 mb-2 w-80 max-h-64 overflow-y-auto bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50"
            >
              <div className="px-3 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Available Skills ({filteredSkills.length})
              </div>
              {filteredSkills.map((skill, index) => (
                <button
                  key={skill.id}
                  onClick={() => handleSkillSelect(skill)}
                  className={cn(
                    "w-full px-3 py-2 flex items-start gap-3 text-left transition-colors",
                    index === selectedSkillIndex
                      ? "bg-blue-50 text-blue-900"
                      : "hover:bg-slate-50 text-slate-700"
                  )}
                >
                  <div className={cn(
                    "w-6 h-6 rounded flex items-center justify-center shrink-0",
                    index === selectedSkillIndex ? "bg-blue-100" : "bg-slate-100"
                  )}>
                    {index === selectedSkillIndex ? (
                      <Check className="w-3.5 h-3.5 text-blue-600" />
                    ) : (
                      <Command className="w-3.5 h-3.5 text-slate-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{skill.name}</div>
                    {skill.description && (
                      <div className="text-xs text-slate-500 truncate mt-0.5">
                        {skill.description}
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
          
          {/* No skills found */}
          {showSkillDropdown && skillFilter && filteredSkills.length === 0 && (
            <div className="absolute bottom-full left-0 mb-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-4 px-3 z-50">
              <p className="text-sm text-slate-500 text-center">No skills found matching "{skillFilter}"</p>
            </div>
          )}
        </div>

        {/* Voice & Send */}
        <div className="flex items-center gap-1">
          <button
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Voice input"
          >
            <Mic className="w-5 h-5" />
          </button>

          <button
            onClick={handleSubmit}
            disabled={(!input.trim() && uploadedFiles.length === 0) || disabled || isStreaming}
            className={cn(
              "p-2 rounded-lg transition-colors",
              (input.trim() || uploadedFiles.length > 0) && !disabled && !isStreaming
                ? "bg-blue-500 text-white hover:bg-blue-600"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
