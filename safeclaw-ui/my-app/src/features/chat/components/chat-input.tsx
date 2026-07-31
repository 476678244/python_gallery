/**
 * Chat Input - Feature Component
 * 
 * Business: Message input, quick actions, file attachments, slash commands
 * Responsibility: Input handling, validation, submission, file upload, skill autocomplete
 */

"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { Send, Paperclip, Mic, Plus, Code, FileText, Sparkles, X, File, Command, Check, Cpu } from "lucide-react";
import { useMessageStore } from "@/stores/message-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useSkillStore } from "@/stores/skill-store";
import { streamChat } from "@/features/chat/services/chat-api";
import { getEnabledModels, type Model } from "@/entities/model";
import { cn } from "@/shared/utils/cn";

type SlashMode = "skill" | "model" | "command" | null;

/** Parse text after `/` into slash-command mode + filter. */
function parseSlashCommand(afterSlash: string): { mode: SlashMode; filter: string } {
  const raw = afterSlash;
  const lower = raw.toLowerCase();

  if (lower === "model" || lower.startsWith("model ") || lower.startsWith("model:")) {
    const filter = lower.startsWith("model:")
      ? raw.slice("model:".length)
      : raw.slice("model".length).trimStart();
    return { mode: "model", filter };
  }

  // Partial "/m" "/mo" "/mod" "/mode" → suggest the model command
  if (lower.length > 0 && !lower.includes(" ") && "model".startsWith(lower)) {
    return { mode: "command", filter: lower };
  }

  if (!raw.includes(" ") && !raw.includes("\n")) {
    return { mode: "skill", filter: raw };
  }

  return { mode: null, filter: "" };
}

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

// Read a File as a base64 data URL (e.g. "data:image/jpeg;base64,...")
function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
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
  const { currentSessionId, sessions, updateSessionSettings } = useSessionStore();
  const sessionId = sessionIdProp ?? currentSessionId;
  const disabled = disabledProp ?? !sessionId;
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [slashMode, setSlashMode] = useState<SlashMode>(null);
  const [slashFilter, setSlashFilter] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const slashDropdownRef = useRef<HTMLDivElement>(null);

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

  const enabledModels = useMemo(
    () => getEnabledModels().filter((m) => !m.capabilities.supportedModes.includes("embeddings")),
    []
  );

  const currentModelId =
    sessions.find((s) => s.id === sessionId)?.settings?.model ?? enabledModels[0]?.id;

  // Filter skills based on input (skill slash mode)
  const filteredSkills = slashFilter
    ? enabledSkills.filter(
        (skill) =>
          skill.name.toLowerCase().includes(slashFilter.toLowerCase()) ||
          skill.description?.toLowerCase().includes(slashFilter.toLowerCase())
      )
    : enabledSkills;

  const filteredModels = slashFilter
    ? enabledModels.filter((m) => {
        const q = slashFilter.toLowerCase();
        return (
          m.name.toLowerCase().includes(q) ||
          m.id.toLowerCase().includes(q) ||
          m.provider.toLowerCase().includes(q) ||
          (m.description?.toLowerCase().includes(q) ?? false)
        );
      })
    : enabledModels;

  const showSlashDropdown = slashMode !== null;
  const slashItemCount =
    slashMode === "model"
      ? filteredModels.length
      : slashMode === "command"
        ? 1
        : slashMode === "skill"
          ? filteredSkills.length
          : 0;

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
    remapExecution,
    handleExecutionStepEvent,
  } = useExecutionStore();

  const handleSubmit = useCallback(async () => {
    if ((!input.trim() && uploadedFiles.length === 0) || isStreaming || !sessionId) return;

    const content = input.trim();
    const files = [...uploadedFiles];
    
    // Reset state
    setInput("");
    setUploadedFiles([]);
    setSlashMode(null);

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
    const apiMessages: { role: string; content: any }[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    // Inject image attachments as multimodal content into the last user message
    // so vision-capable models (VLM) can actually "see" them.
    const imageFiles = files.filter((f) => f.type.startsWith("image/"));
    if (imageFiles.length > 0 && apiMessages.length > 0) {
      try {
        const imageParts = await Promise.all(
          imageFiles.map(async (f) => ({
            type: "image_url",
            image_url: { url: await readFileAsDataUrl(f.file) },
          }))
        );
        const lastIdx = apiMessages.length - 1;
        apiMessages[lastIdx] = {
          role: apiMessages[lastIdx].role,
          content: [
            ...(content ? [{ type: "text", text: content }] : []),
            ...imageParts,
          ],
        };
      } catch (err) {
        console.error("Failed to encode image attachments:", err);
      }
    }

    // Start streaming
    const streamingId = startStreaming(sessionId);
    startExecution(sessionId, streamingId);
    setThinking(true);

    // Stream chat
    // Resolve current model from session settings
    const currentSession = sessions.find((s) => s.id === sessionId);
    const currentModel = currentSession?.settings?.model;

    await streamChat(
      {
        messages: apiMessages,
        sessionId: sessionId,
        model: currentModel,
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
          // Remap execution to backend's message_id so PromptInspectPanel
          // can fetch /llm-calls/{backend_msg_id} correctly
          const backendMsgId = data.executionGraph?.messageId;
          if (backendMsgId && backendMsgId !== streamingId) {
            remapExecution(streamingId, backendMsgId);
          }
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
    sessions,
    addUserMessage,
    getMessagesForSession,
    startStreaming,
    startExecution,
    setThinking,
    addThinkingStep,
    completeStreaming,
    completeExecution,
    remapExecution,
    cancelStreaming,
    handleExecutionStepEvent,
  ]);

  // File upload handlers — files land under WORKSPACE_DIR/uploaded/
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
    
    // Upload into workspace/uploaded/ (server confines paths to WORKSPACE_DIR)
    for (const uploadedFile of newFiles) {
      try {
        const formData = new FormData();
        formData.append("file", uploadedFile.file);
        formData.append("path", `uploaded/${uploadedFile.name}`);

        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorText = await response.text().catch(() => "Unknown error");
          console.error(`Failed to upload ${uploadedFile.name}: HTTP ${response.status} - ${errorText}`);
        } else {
          const result = await response.json().catch(() => ({ success: true }));
          console.log(`Uploaded ${uploadedFile.name} to workspace/uploaded/`, result);
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
    
    // Handle file drop — upload to workspace/uploaded
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

    const beforeCursor = value.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");

    if (lastSlashIndex === -1) {
      setSlashMode(null);
      return;
    }

    // Only treat as slash command when `/` starts a token (start or after whitespace)
    if (lastSlashIndex > 0 && !/\s/.test(beforeCursor[lastSlashIndex - 1])) {
      setSlashMode(null);
      return;
    }

    const afterSlash = beforeCursor.slice(lastSlashIndex + 1);
    if (afterSlash.includes("\n")) {
      setSlashMode(null);
      return;
    }

    const parsed = parseSlashCommand(afterSlash);
    setSlashMode(parsed.mode);
    setSlashFilter(parsed.filter);
    setSelectedIndex(0);
  }, []);

  const clearSlashCommandFromInput = useCallback(() => {
    const cursorPos = textareaRef.current?.selectionStart || input.length;
    const beforeCursor = input.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");
    if (lastSlashIndex === -1) {
      setInput("");
      setSlashMode(null);
      return;
    }
    const beforeSlash = input.slice(0, lastSlashIndex);
    // Drop the rest of the slash token (through end of line / remaining filter)
    const after = input.slice(cursorPos);
    const rest = after.startsWith("\n") ? after : after.replace(/^[^\n]*/, "");
    const next = `${beforeSlash}${rest}`.replace(/[ \t]+$/g, "");
    setInput(next);
    setSlashMode(null);
    setTimeout(() => {
      if (textareaRef.current) {
        const pos = beforeSlash.length;
        textareaRef.current.setSelectionRange(pos, pos);
        textareaRef.current.focus();
      }
    }, 0);
  }, [input]);

  const handleSkillSelect = useCallback((skill: SkillSuggestion) => {
    const cursorPos = textareaRef.current?.selectionStart || 0;
    const beforeCursor = input.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");

    if (lastSlashIndex !== -1) {
      const beforeSlash = input.slice(0, lastSlashIndex);
      const afterCursor = input.slice(cursorPos);
      const newValue = `${beforeSlash}/${skill.name}${afterCursor}`;
      setInput(newValue);
      setSlashMode(null);

      setTimeout(() => {
        if (textareaRef.current) {
          const newPos = lastSlashIndex + skill.name.length + 1;
          textareaRef.current.setSelectionRange(newPos, newPos);
          textareaRef.current.focus();
        }
      }, 0);
    }
  }, [input]);

  const handleModelSelect = useCallback(
    (model: Model) => {
      if (sessionId) {
        updateSessionSettings(sessionId, { model: model.id });
      }
      fetch("/api/settings/model", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: model.id }),
      }).catch(() => {});
      clearSlashCommandFromInput();
    },
    [sessionId, updateSessionSettings, clearSlashCommandFromInput]
  );

  const handleCommandSelect = useCallback(() => {
    // Expand "/m…" into "/model " and open model picker
    const cursorPos = textareaRef.current?.selectionStart || input.length;
    const beforeCursor = input.slice(0, cursorPos);
    const lastSlashIndex = beforeCursor.lastIndexOf("/");
    if (lastSlashIndex === -1) return;
    const beforeSlash = input.slice(0, lastSlashIndex);
    const afterCursor = input.slice(cursorPos);
    const newValue = `${beforeSlash}/model ${afterCursor}`;
    setInput(newValue);
    setSlashMode("model");
    setSlashFilter("");
    setSelectedIndex(0);
    setTimeout(() => {
      if (textareaRef.current) {
        const pos = lastSlashIndex + "/model ".length;
        textareaRef.current.setSelectionRange(pos, pos);
        textareaRef.current.focus();
      }
    }, 0);
  }, [input]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (showSlashDropdown && slashItemCount > 0) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedIndex((prev) => (prev < slashItemCount - 1 ? prev + 1 : prev));
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          return;
        }
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          if (slashMode === "model" && filteredModels[selectedIndex]) {
            handleModelSelect(filteredModels[selectedIndex]);
          } else if (slashMode === "command") {
            handleCommandSelect();
          } else if (slashMode === "skill" && filteredSkills[selectedIndex]) {
            handleSkillSelect(filteredSkills[selectedIndex]);
          }
          return;
        }
        if (e.key === "Escape") {
          setSlashMode(null);
          return;
        }
      }

      if (e.key === "Enter" && !e.shiftKey && !showSlashDropdown) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [
      showSlashDropdown,
      slashItemCount,
      slashMode,
      filteredModels,
      filteredSkills,
      selectedIndex,
      handleModelSelect,
      handleCommandSelect,
      handleSkillSelect,
      handleSubmit,
    ]
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (slashDropdownRef.current && !slashDropdownRef.current.contains(e.target as Node)) {
        setSlashMode(null);
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
          title="Upload files to workspace/uploaded"
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
            placeholder={
              disabled
                ? "Select a session to start chatting..."
                : "Ask anything... / for skills, /model to switch model"
            }
            disabled={disabled || isStreaming}
            rows={1}
            className={cn(
              "w-full resize-none bg-transparent outline-none",
              "text-slate-900 placeholder:text-slate-400",
              "min-h-[24px] max-h-[200px]"
            )}
            style={{ height: "auto" }}
          />

          {/* Slash: command hint (e.g. /mo → model) */}
          {slashMode === "command" && (
            <div
              ref={slashDropdownRef}
              data-testid="slash-command-dropdown"
              className="absolute bottom-full left-0 mb-2 w-80 max-h-64 overflow-y-auto bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50"
            >
              <div className="px-3 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Commands
              </div>
              <button
                onClick={handleCommandSelect}
                className={cn(
                  "w-full px-3 py-2 flex items-start gap-3 text-left transition-colors",
                  selectedIndex === 0 ? "bg-blue-50 text-blue-900" : "hover:bg-slate-50 text-slate-700"
                )}
              >
                <div className="w-6 h-6 rounded flex items-center justify-center shrink-0 bg-blue-100">
                  <Cpu className="w-3.5 h-3.5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">/model</div>
                  <div className="text-xs text-slate-500 truncate mt-0.5">
                    Switch AI model for this session
                  </div>
                </div>
              </button>
            </div>
          )}

          {/* Slash: model picker */}
          {slashMode === "model" && filteredModels.length > 0 && (
            <div
              ref={slashDropdownRef}
              data-testid="model-autocomplete-dropdown"
              className="absolute bottom-full left-0 mb-2 w-80 max-h-64 overflow-y-auto bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50"
            >
              <div className="px-3 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Switch Model ({filteredModels.length})
              </div>
              {filteredModels.map((model, index) => (
                <button
                  key={model.id}
                  onClick={() => handleModelSelect(model)}
                  className={cn(
                    "w-full px-3 py-2 flex items-start gap-3 text-left transition-colors",
                    index === selectedIndex
                      ? "bg-blue-50 text-blue-900"
                      : "hover:bg-slate-50 text-slate-700"
                  )}
                >
                  <div
                    className={cn(
                      "w-6 h-6 rounded flex items-center justify-center shrink-0",
                      index === selectedIndex || model.id === currentModelId
                        ? "bg-blue-100"
                        : "bg-slate-100"
                    )}
                  >
                    {model.id === currentModelId ? (
                      <Check className="w-3.5 h-3.5 text-blue-600" />
                    ) : (
                      <Cpu className="w-3.5 h-3.5 text-slate-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">
                      {model.name}
                      {model.id === currentModelId && (
                        <span className="ml-2 text-[10px] font-bold text-blue-500">active</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500 truncate mt-0.5">
                      {model.provider}
                      {model.description ? ` · ${model.description}` : ""}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {slashMode === "model" && slashFilter && filteredModels.length === 0 && (
            <div
              ref={slashDropdownRef}
              className="absolute bottom-full left-0 mb-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-4 px-3 z-50"
            >
              <p className="text-sm text-slate-500 text-center">
                No models matching &quot;{slashFilter}&quot;
              </p>
            </div>
          )}

          {/* Slash: skill suggestion dropdown */}
          {slashMode === "skill" && filteredSkills.length > 0 && (
            <div
              ref={slashDropdownRef}
              data-testid="skill-autocomplete-dropdown"
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
                    index === selectedIndex
                      ? "bg-blue-50 text-blue-900"
                      : "hover:bg-slate-50 text-slate-700"
                  )}
                >
                  <div
                    className={cn(
                      "w-6 h-6 rounded flex items-center justify-center shrink-0",
                      index === selectedIndex ? "bg-blue-100" : "bg-slate-100"
                    )}
                  >
                    {index === selectedIndex ? (
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

          {slashMode === "skill" && slashFilter && filteredSkills.length === 0 && (
            <div className="absolute bottom-full left-0 mb-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-4 px-3 z-50">
              <p className="text-sm text-slate-500 text-center">
                No skills found matching &quot;{slashFilter}&quot;
              </p>
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
