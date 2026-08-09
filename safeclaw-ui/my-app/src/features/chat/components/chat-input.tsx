/**
 * Chat Input - Feature Component
 * 
 * Business: Message input, quick actions, file attachments, slash commands
 * Responsibility: Input handling, validation, submission, file upload, skill autocomplete
 */

"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import {
  Send,
  Paperclip,
  Mic,
  Plus,
  Code,
  FileText,
  Sparkles,
  X,
  File,
  Command,
  Check,
  Cpu,
  HelpCircle,
  Eraser,
  MessageSquarePlus,
  Wrench,
  Brain,
  type LucideIcon,
} from "lucide-react";
import { useMessageStore } from "@/stores/message-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useSkillStore } from "@/stores/skill-store";
import { useUIStore } from "@/stores/ui-store";
import { streamChat } from "@/features/chat/services/chat-api";
import {
  SEND_PROMPT_EVENT,
  type SendPromptDetail,
} from "@/features/chat/lib/send-prompt-event";
import { getEnabledModels, getModelById, type Model } from "@/entities/model";
import { useModelStore, resolveActiveModelId } from "@/stores/model-store";
import {
  SLASH_COMMANDS,
  MODE_SLASH_IDS,
  filterCommands,
  parseSlashCommand,
  type SlashCommandDef,
  type SlashMode,
} from "@/features/chat/slash/commands";
import {
  isAgentMode,
  modeWriteChips,
  parseAgentMode,
  type AgentMode,
} from "@/entities/agent-mode";
import { cn } from "@/shared/utils/cn";

const COMMAND_ICONS: Record<string, LucideIcon> = {
  help: HelpCircle,
  ask: HelpCircle,
  agent: Sparkles,
  plan: FileText,
  safe: Check,
  debug: Code,
  subagent: Wrench,
  ppt: FileText,
  loop: Command,
  model: Cpu,
  skill: Wrench,
  remember: Brain,
  memory: Brain,
  clear: Eraser,
  new: MessageSquarePlus,
};

/** Parse `/loop [interval] prompt` — interval like 30s, 5m, 2h. */
function parseLoopArgs(args: string): { intervalMs: number; prompt: string } | null {
  const trimmed = args.trim();
  if (!trimmed) return null;
  const m = trimmed.match(/^(\d+)\s*([smhd])\s+(.+)$/i);
  if (m) {
    const n = parseInt(m[1], 10);
    const unit = m[2].toLowerCase();
    const mult =
      unit === "s" ? 1000 : unit === "m" ? 60_000 : unit === "h" ? 3_600_000 : 86_400_000;
    return { intervalMs: Math.max(n * mult, 5000), prompt: m[3].trim() };
  }
  // default 5m if no interval
  return { intervalMs: 5 * 60_000, prompt: trimmed };
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
import { useDeckPreviewStore } from "@/stores/deck-preview-store";

export function ChatInput({ sessionId: sessionIdProp, disabled: disabledProp, onFileUpload }: ChatInputProps) {
  // Get session from store if not provided via props
  const { currentSessionId, sessions, updateSessionSettings, createSession } = useSessionStore();
  const { globalModelId, loadGlobalModel, setGlobalModel, loaded: modelLoaded, error: modelError } =
    useModelStore();
  const sessionId = sessionIdProp ?? currentSessionId;
  const disabled = disabledProp ?? !sessionId;

  useEffect(() => {
    void loadGlobalModel().catch((err) => {
      console.error("[ChatInput] Failed to load global model", err);
    });
  }, [loadGlobalModel]);
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [slashMode, setSlashMode] = useState<SlashMode>(null);
  const [slashFilter, setSlashFilter] = useState("");
  const [slashArgs, setSlashArgs] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [slashNotice, setSlashNotice] = useState<string | null>(null);
  const railToggle = useUIStore((s) => s.railToggle);
  const isPanelOpen = useUIStore((s) => s.isPanelOpen);
  const applyObservabilityPack = useUIStore((s) => s.applyObservabilityPack);
  const loopTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const loopDoneConditionRef = useRef<string>("");
  const [loopStatus, setLoopStatus] = useState<string | null>(null);
  /** Pending loop awaiting human confirmation of done/stop condition (Fail Fast). */
  const [loopConfirm, setLoopConfirm] = useState<{
    intervalMs: number;
    prompt: string;
    doneCondition: string;
  } | null>(null);

  const sessionMode: AgentMode = parseAgentMode(
    sessions.find((s) => s.id === sessionId)?.settings?.mode
  );
  const writeChips = modeWriteChips(sessionMode);

  // Re-apply pack on mount / session switch / reload (ppt/debug/subagent sticky)
  useEffect(() => {
    if (!sessionId) return;
    applyObservabilityPack(writeChips.observability);
  }, [sessionId, sessionMode, applyObservabilityPack, writeChips.observability]);

  const stopLoop = useCallback(() => {
    if (loopTimerRef.current) {
      clearInterval(loopTimerRef.current);
      loopTimerRef.current = null;
    }
    loopDoneConditionRef.current = "";
    setLoopStatus(null);
    setLoopConfirm(null);
  }, []);

  useEffect(() => () => stopLoop(), [stopLoop]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const slashDropdownRef = useRef<HTMLDivElement>(null);
  const noticeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  const sessionModel = sessions.find((s) => s.id === sessionId)?.settings?.model;
  const currentModelId =
    modelLoaded && !modelError && (sessionModel || globalModelId)
      ? resolveActiveModelId(sessionModel, globalModelId)
      : null;
  const currentModel = currentModelId ? getModelById(currentModelId) ?? null : null;
  if (currentModelId && !currentModel) {
    throw new Error(
      `[ChatInput] Unknown model id\n` +
        `  Actual: ${currentModelId}\n` +
        `  Expected: id in AVAILABLE_MODELS`
    );
  }

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

  const filteredCommands = useMemo(() => {
    if (slashMode === "help") return SLASH_COMMANDS;
    if (slashMode === "command") return filterCommands(slashFilter);
    return [];
  }, [slashMode, slashFilter]);

  const showSlashDropdown = slashMode !== null;
  const slashItemCount =
    slashMode === "model"
      ? filteredModels.length
      : slashMode === "skill"
        ? filteredSkills.length
        : slashMode === "command" || slashMode === "help"
          ? filteredCommands.length
          : 0;

  const showNotice = useCallback((message: string) => {
    setSlashNotice(message);
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setSlashNotice(null), 2500);
  }, []);

  const {
    addUserMessage,
    startStreaming,
    appendStreamingContent,
    completeStreaming,
    cancelStreaming,
    isStreaming,
    getMessagesForSession,
    clearMessages,
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

  const sendPromptContent = useCallback(
    async (rawContent: string, files: UploadedFile[] = []) => {
      if (isStreaming || !sessionId) return;
      const content = rawContent.trim();
      if (!content && files.length === 0) return;

      // Fail Fast before mutating UI / starting stream
      if (!currentModelId) {
        const message =
          `[ChatInput] Refuse to stream: model not resolved\n` +
          `  sessionId: ${sessionId}\n` +
          `  modelLoaded: ${modelLoaded}\n` +
          `  modelError: ${modelError}\n` +
          `  globalModelId: ${globalModelId}`;
        console.error(message);
        window.alert(message);
        throw new Error(message);
      }

      const messageContent =
        files.length > 0
          ? `${content}\n\n[Attached files: ${files.map((f) => f.name).join(", ")}]`
          : content;
      addUserMessage(messageContent, sessionId);

      if (files.length > 0 && onFileUpload) {
        onFileUpload(files);
      }

      const messages = getMessagesForSession(sessionId);
      const apiMessages: { role: string; content: any }[] = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const imageFiles = files.filter((f) => f.type.startsWith("image/"));
      if (imageFiles.length > 0 && apiMessages.length > 0) {
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
      }

      const streamingId = startStreaming(sessionId);
      startExecution(sessionId, streamingId);
      setThinking(true);

      await streamChat(
        {
          messages: apiMessages,
          sessionId: sessionId,
          model: currentModelId,
          mode: sessionMode,
        },
        {
          onThinking: (step) => {
            addThinkingStep(step);
          },
          onExecutionStep: (event) => {
            handleExecutionStepEvent(streamingId, event);
          },
          onPptPreview: (event) => {
            useDeckPreviewStore.getState().applyPreviewEvent({
              deck_id: event.deck_id,
              version: event.version,
              pptx_path: event.pptx_path,
              preview_urls: event.preview_urls,
              error: event.error,
            });
          },
          onContent: () => {
            // Content updates handled in store
          },
          onComplete: (data) => {
            completeStreaming(data.message.content);
            completeExecution(streamingId, {
              totalTokens: data.usage?.totalTokens,
              skillsUsed: data.executionGraph?.metadata?.skillsUsed,
              totalDuration: data.timing?.totalDuration,
            });
            const backendMsgId = data.executionGraph?.messageId;
            if (backendMsgId && backendMsgId !== streamingId) {
              remapExecution(streamingId, backendMsgId);
            }
            setThinking(false);
            setTimeout(() => {
              const allMessages = getMessagesForSession(sessionId!);
              void fetch(`/api/sessions/${sessionId}/messages`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  messages: allMessages.map((m) => ({
                    ...m,
                    timestamp:
                      m.timestamp instanceof Date
                        ? m.timestamp.toISOString()
                        : m.timestamp,
                  })),
                }),
              })
                .then(async (r) => {
                  if (!r.ok) {
                    const detail = await r.text();
                    throw new Error(
                      `[ChatInput] Persist messages failed (Fail Fast)\n` +
                        `  sessionId: ${sessionId}\n` +
                        `  Status: ${r.status}\n` +
                        `  Body: ${detail.slice(0, 200)}`
                    );
                  }
                })
                .catch((err) => {
                  console.error(err);
                  window.alert(
                    err instanceof Error ? err.message : "Failed to persist messages"
                  );
                });
            }, 0);
          },
          onError: (error) => {
            console.error("Chat error:", error);
            cancelStreaming();
            setThinking(false);
          },
        }
      );
    },
    [
      isStreaming,
      sessionId,
      onFileUpload,
      currentModelId,
      sessionMode,
      modelLoaded,
      modelError,
      globalModelId,
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
    ]
  );

  const handleSubmit = useCallback(async () => {
    if ((!input.trim() && uploadedFiles.length === 0) || isStreaming || !sessionId) return;
    const content = input.trim();
    const files = [...uploadedFiles];
    setInput("");
    setUploadedFiles([]);
    setSlashMode(null);
    await sendPromptContent(content, files);
  }, [input, uploadedFiles, isStreaming, sessionId, sendPromptContent]);

  // Exec Steer / external inject → stream a user turn
  useEffect(() => {
    const onSend = (ev: Event) => {
      const detail = (ev as CustomEvent<SendPromptDetail>).detail;
      if (!detail?.content?.trim()) {
        throw new Error(
          `[ChatInput] ${SEND_PROMPT_EVENT} missing content (Fail Fast)`
        );
      }
      void sendPromptContent(detail.content);
    };
    window.addEventListener(SEND_PROMPT_EVENT, onSend);
    return () => window.removeEventListener(SEND_PROMPT_EVENT, onSend);
  }, [sendPromptContent]);

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
          let result: unknown;
          try {
            result = await response.json();
          } catch (e) {
            throw new Error(
              `[ChatInput] Upload response non-JSON (Fail Fast)\n` +
                `  file: ${uploadedFile.name}\n` +
                `  Error: ${e instanceof Error ? e.message : String(e)}`
            );
          }
          console.log(`Uploaded ${uploadedFile.name} to workspace/uploaded/`, result);
        }
      } catch (error) {
        console.error(`Error uploading ${uploadedFile.name}:`, error);
        window.alert(
          error instanceof Error
            ? error.message
            : `Upload failed: ${uploadedFile.name}`
        );
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
    setSlashArgs(parsed.args ?? "");
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

  const setSessionMode = useCallback(
    (mode: AgentMode) => {
      if (!sessionId) {
        throw new Error(
          `[ChatInput] Cannot set mode without session\n  mode: ${mode}`
        );
      }
      updateSessionSettings(sessionId, { mode });
      const chips = modeWriteChips(mode);
      applyObservabilityPack(chips.observability);
      clearSlashCommandFromInput();
      setSlashMode(null);
      showNotice(
        `Mode → ${mode} · create ${chips.create ? "✓" : "✗"} · update ${
          chips.update ? "✓" : "✗"
        } · delete ${chips.delete ? "✓" : "✗"}`
      );
    },
    [
      sessionId,
      updateSessionSettings,
      applyObservabilityPack,
      clearSlashCommandFromInput,
      showNotice,
    ]
  );

  const armLoop = useCallback(
    (intervalMs: number, prompt: string, doneCondition: string) => {
      const done = doneCondition.trim();
      if (!done) {
        throw new Error(
          `[ChatInput] Loop refused: empty done/stop condition (Fail Fast)\n` +
            `  Confirm a concrete completion criterion with the human before arming.`
        );
      }
      if (!sessionId || !currentModelId) {
        throw new Error(
          `[ChatInput] Cannot start loop without session/model\n` +
            `  sessionId: ${sessionId}\n  model: ${currentModelId}`
        );
      }
      stopLoop();
      loopDoneConditionRef.current = done;
      let tick = 0;
      const tickPrompt = () =>
        `${prompt}\n\n[LOOP] Done/stop when: ${done}\n` +
        `If the condition is met, reply with exactly: LOOP_DONE — <reason>`;

      showNotice(
        `Loop armed · every ${Math.round(intervalMs / 1000)}s · until: ${done.slice(0, 80)}`
      );
      setLoopConfirm(null);
      clearSlashCommandFromInput();
      setInput(tickPrompt());

      const kickSend = () => {
        tick += 1;
        setLoopStatus(
          `loop #${tick} · ${Math.round(intervalMs / 1000)}s · stop: ${done.slice(0, 40)}`
        );
        setTimeout(() => {
          document
            .querySelector<HTMLButtonElement>('[data-testid="chat-send-button"]')
            ?.click();
        }, 30);
      };
      setTimeout(kickSend, 40);
      loopTimerRef.current = setInterval(() => {
        setInput(tickPrompt());
        kickSend();
      }, intervalMs);
    },
    [
      sessionId,
      currentModelId,
      stopLoop,
      showNotice,
      clearSlashCommandFromInput,
    ]
  );

  const runLoop = useCallback(
    (args: string) => {
      if (args.trim().toLowerCase() === "stop") {
        stopLoop();
        clearSlashCommandFromInput();
        showNotice("Loop stopped");
        return;
      }
      const parsed = parseLoopArgs(args);
      if (!parsed) {
        showNotice("Usage: /loop [interval] <prompt> · then confirm done condition · /loop stop");
        clearSlashCommandFromInput();
        return;
      }
      // Fail Fast: never arm until human confirms explicit done/stop condition
      clearSlashCommandFromInput();
      setLoopConfirm({
        intervalMs: parsed.intervalMs,
        prompt: parsed.prompt,
        doneCondition: "",
      });
      showNotice("Confirm loop done/stop condition before arming");
    },
    [stopLoop, showNotice, clearSlashCommandFromInput]
  );

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

  const expandSlashToCommand = useCallback(
    (cmdName: string) => {
      const cursorPos = textareaRef.current?.selectionStart || input.length;
      const beforeCursor = input.slice(0, cursorPos);
      const lastSlashIndex = beforeCursor.lastIndexOf("/");
      if (lastSlashIndex === -1) return;
      const beforeSlash = input.slice(0, lastSlashIndex);
      const afterCursor = input.slice(cursorPos);
      const token = `/${cmdName} `;
      const newValue = `${beforeSlash}${token}${afterCursor}`;
      setInput(newValue);
      setSelectedIndex(0);
      setTimeout(() => {
        if (textareaRef.current) {
          const pos = lastSlashIndex + token.length;
          textareaRef.current.setSelectionRange(pos, pos);
          textareaRef.current.focus();
        }
      }, 0);
    },
    [input]
  );

  const handleModelSelect = useCallback(
    async (model: Model) => {
      if (sessionId) {
        updateSessionSettings(sessionId, { model: model.id });
      }
      await setGlobalModel(model.id);
      clearSlashCommandFromInput();
      showNotice(`Model → ${model.name}`);
    },
    [sessionId, updateSessionSettings, setGlobalModel, clearSlashCommandFromInput, showNotice]
  );

  const runClearChat = useCallback(() => {
    if (!sessionId) return;
    clearMessages(sessionId);
    void fetch(`/api/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: [] }),
    }).then(async (r) => {
      if (!r.ok) {
        throw new Error(
          `[ChatInput] /clear persist failed (Fail Fast)\n` +
            `  sessionId: ${sessionId}\n` +
            `  Status: ${r.status}`
        );
      }
      clearSlashCommandFromInput();
      showNotice("Chat cleared");
    }).catch((err) => {
      console.error(err);
      window.alert(err instanceof Error ? err.message : "Failed to clear chat");
    });
  }, [sessionId, clearMessages, clearSlashCommandFromInput, showNotice]);

  const runNewChat = useCallback(async () => {
    clearSlashCommandFromInput();
    if (!currentModelId) {
      throw new Error(
        "[ChatInput] /new refused: global model not loaded\n" +
          `  modelLoaded: ${modelLoaded}\n` +
          `  modelError: ${modelError}\n` +
          `  globalModelId: ${globalModelId}`
      );
    }
    await createSession(undefined, currentModelId);
    showNotice("New chat started");
  }, [
    createSession,
    currentModelId,
    clearSlashCommandFromInput,
    showNotice,
    modelLoaded,
    modelError,
    globalModelId,
  ]);

  const openMemoryPanel = useCallback(() => {
    if (!isPanelOpen("memory")) {
      railToggle("memory");
    }
  }, [isPanelOpen, railToggle]);

  const runRemember = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content) {
        expandSlashToCommand("remember");
        setSlashMode("command");
        setSlashFilter("remember");
        showNotice("Type text after /remember");
        return;
      }
      const res = await fetch("/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          importance: 0.9,
          keywords: content.split(/\s+/).slice(0, 6),
          metadata: { source: "slash_remember", session_id: sessionId },
        }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(
          `[ChatInput] /remember failed\n` +
            `  Status: ${res.status}\n` +
            `  Detail: ${detail}`
        );
      }
      clearSlashCommandFromInput();
      showNotice("Remembered");
      openMemoryPanel();
    },
    [
      sessionId,
      expandSlashToCommand,
      clearSlashCommandFromInput,
      showNotice,
      openMemoryPanel,
    ]
  );

  const runMemorySearch = useCallback(
    async (query: string) => {
      openMemoryPanel();
      const q = query.trim();
      if (!q) {
        clearSlashCommandFromInput();
        showNotice("Memory panel opened");
        return;
      }
      const res = await fetch(`/api/memory?search=${encodeURIComponent(q)}&limit=5`);
      if (!res.ok) {
        throw new Error(
          `[ChatInput] /memory search failed\n` +
            `  Status: ${res.status}`
        );
      }
      const data = await res.json();
      const total = data.total ?? (data.memories?.length ?? 0);
      clearSlashCommandFromInput();
      showNotice(`Memory: ${total} hit${total === 1 ? "" : "s"} for “${q}”`);
    },
    [openMemoryPanel, clearSlashCommandFromInput, showNotice]
  );

  const activateSlashCommand = useCallback(
    (cmd: SlashCommandDef, argsOverride?: string) => {
      const args = (argsOverride ?? slashArgs).trim();
      if (cmd.kind === "help") {
        expandSlashToCommand("help");
        setSlashMode("help");
        setSlashFilter("");
        setSelectedIndex(0);
        return;
      }
      if (cmd.kind === "picker") {
        expandSlashToCommand(cmd.name);
        setSlashMode(cmd.id as "model" | "skill");
        setSlashFilter("");
        setSelectedIndex(0);
        return;
      }
      // action
      if (cmd.id === "clear") {
        runClearChat();
        return;
      }
      if (cmd.id === "new") {
        void runNewChat().catch((err) => {
          console.error(err);
          window.alert(err instanceof Error ? err.message : "Failed to create session");
        });
        return;
      }
      if (cmd.id === "remember") {
        void runRemember(args).catch((err) => {
          console.error(err);
          window.alert(err instanceof Error ? err.message : "Failed to remember");
        });
        return;
      }
      if (cmd.id === "memory") {
        void runMemorySearch(args).catch((err) => {
          console.error(err);
          window.alert(err instanceof Error ? err.message : "Memory search failed");
        });
        return;
      }
      if ((MODE_SLASH_IDS as readonly string[]).includes(cmd.id) && isAgentMode(cmd.id)) {
        setSessionMode(cmd.id);
        return;
      }
      if (cmd.id === "loop") {
        runLoop(args);
        return;
      }
      throw new Error(
        `[ChatInput] Unknown slash action\n` +
          `  Command id: ${cmd.id}\n` +
          `  Expected: clear|new|remember|memory|ask|agent|plan|safe|debug|subagent|ppt|loop`
      );
    },
    [
      slashArgs,
      expandSlashToCommand,
      runClearChat,
      runNewChat,
      runRemember,
      runMemorySearch,
      setSessionMode,
      runLoop,
      showNotice,
    ]
  );

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
            void handleModelSelect(filteredModels[selectedIndex]).catch((err) => {
              console.error(err);
              window.alert(err instanceof Error ? err.message : "Failed to select model");
            });
          } else if (
            (slashMode === "command" || slashMode === "help") &&
            filteredCommands[selectedIndex]
          ) {
            activateSlashCommand(filteredCommands[selectedIndex]);
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
      filteredCommands,
      selectedIndex,
      handleModelSelect,
      activateSlashCommand,
      handleSkillSelect,
      handleSubmit,
    ]
  );

  useEffect(() => {
    return () => {
      if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
    };
  }, []);

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
      {loopConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/35 p-4"
          data-testid="loop-confirm-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="loop-confirm-title"
        >
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
            <h2 id="loop-confirm-title" className="text-sm font-semibold text-slate-900 mb-1">
              Confirm loop · done / stop condition
            </h2>
            <p className="text-xs text-slate-500 mb-3 leading-relaxed">
              Loop will not start until you state a clear completion criterion.
              Empty condition is rejected (Fail Fast).
            </p>
            <div className="text-[11px] text-slate-600 mb-2 space-y-1 rounded-lg bg-slate-50 border border-slate-100 p-2">
              <div>
                <span className="font-semibold">Interval:</span>{" "}
                {Math.round(loopConfirm.intervalMs / 1000)}s
              </div>
              <div>
                <span className="font-semibold">Prompt:</span> {loopConfirm.prompt}
              </div>
              <div>
                <span className="font-semibold">Mode:</span> {sessionMode}
              </div>
            </div>
            <label className="block text-xs font-medium text-slate-700 mb-1" htmlFor="loop-done-input">
              Done / stop when (required)
            </label>
            <textarea
              id="loop-done-input"
              data-testid="loop-done-condition"
              className="w-full min-h-[72px] text-sm border border-slate-200 rounded-lg p-2 mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              placeholder="e.g. CI green · file X exists · max 10 ticks · no change ×3"
              value={loopConfirm.doneCondition}
              onChange={(e) =>
                setLoopConfirm((prev) =>
                  prev ? { ...prev, doneCondition: e.target.value } : prev
                )
              }
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                data-testid="loop-confirm-cancel"
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                onClick={() => {
                  setLoopConfirm(null);
                  showNotice("Loop cancelled — not armed");
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                data-testid="loop-confirm-arm"
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-40"
                disabled={!loopConfirm.doneCondition.trim()}
                onClick={() => {
                  try {
                    armLoop(
                      loopConfirm.intervalMs,
                      loopConfirm.prompt,
                      loopConfirm.doneCondition
                    );
                  } catch (err) {
                    console.error(err);
                    window.alert(
                      err instanceof Error ? err.message : "Failed to arm loop"
                    );
                  }
                }}
              >
                Arm loop
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Session model + slash notice */}
      <div className="flex items-center gap-2 mb-2 min-h-[22px]">
        {modelError ? (
          <span data-testid="input-model-error" className="text-[11px] text-red-600 truncate max-w-[280px]" title={modelError}>
            Model error — check console
          </span>
        ) : !currentModel ? (
          <span className="text-[11px] text-slate-400">Loading model…</span>
        ) : (
          <button
            type="button"
            onClick={() => {
              if (disabled || isStreaming) return;
              setInput("/model ");
              setSlashMode("model");
              setSlashFilter("");
              setSelectedIndex(0);
              setTimeout(() => textareaRef.current?.focus(), 0);
            }}
            className={cn(
              "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px]",
              "bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
            )}
            data-testid="input-model-chip"
            title="Switch model (/model)"
          >
            <Cpu className="w-3 h-3 text-blue-500" />
            <span className="font-medium truncate max-w-[160px]">{currentModel.name}</span>
          </button>
        )}
        <span
          data-testid="mode-badge"
          className={cn(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold uppercase tracking-wide",
            "bg-blue-50 text-blue-700 border border-blue-100"
          )}
          title={`Session mode · create ${writeChips.create ? "on" : "off"} · update ${
            writeChips.update ? "on" : "off"
          }`}
        >
          {sessionMode}
        </span>
        <span
          data-testid="mode-policy-chips"
          className="text-[10px] text-slate-500"
        >
          c{writeChips.create ? "✓" : "✗"} u{writeChips.update ? "✓" : "✗"} d
          {writeChips.delete ? "✓" : "✗"}
        </span>
        {loopStatus && (
          <button
            type="button"
            data-testid="loop-status"
            onClick={() => {
              stopLoop();
              showNotice("Loop stopped");
            }}
            className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md"
            title="Click to stop loop"
          >
            {loopStatus}
          </button>
        )}
        {slashNotice && (
          <span
            data-testid="slash-notice"
            className="text-[11px] text-emerald-600 animate-in fade-in"
          >
            {slashNotice}
          </span>
        )}
      </div>

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
                : "Ask anything… type / for commands (/help, /model, /skill, /clear, /new)"
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

          {/* Slash: command palette / help */}
          {(slashMode === "command" || slashMode === "help") && filteredCommands.length > 0 && (
            <div
              ref={slashDropdownRef}
              data-testid="slash-command-dropdown"
              className="absolute bottom-full left-0 mb-2 w-80 max-h-64 overflow-y-auto bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50"
            >
              <div className="px-3 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                {slashMode === "help" ? "All Commands" : "Commands"}
              </div>
              {filteredCommands.map((cmd, index) => {
                const Icon = COMMAND_ICONS[cmd.id] ?? Command;
                return (
                  <button
                    key={cmd.id}
                    type="button"
                    data-testid={`slash-cmd-${cmd.id}`}
                    onClick={() => activateSlashCommand(cmd)}
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
                      <Icon
                        className={cn(
                          "w-3.5 h-3.5",
                          index === selectedIndex ? "text-blue-600" : "text-slate-500"
                        )}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">/{cmd.name}</div>
                      <div className="text-xs text-slate-500 truncate mt-0.5">
                        {cmd.description}
                      </div>
                    </div>
                  </button>
                );
              })}
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
                  type="button"
                  onClick={() => {
                    void handleModelSelect(model).catch((err) => {
                      console.error(err);
                      window.alert(err instanceof Error ? err.message : "Failed to select model");
                    });
                  }}
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
                  type="button"
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
            type="button"
            data-testid="chat-send-button"
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
