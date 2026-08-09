"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  TrendingUp,
  Wrench,
  Coins,
  ClipboardList,
  Terminal,
  Eye,
  Brain,
  Presentation,
  ChevronDown,
  GripHorizontal,
  GripVertical,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useUIStore, type RightPanelKey } from "@/stores/ui-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useSkillStore } from "@/stores/skill-store";
import { useMessageStore } from "@/stores/message-store";
import { useDeckPreviewStore } from "@/stores/deck-preview-store";
import { MemoryPanel } from "@/features/memory/components/memory-panel";
import { abortChat } from "@/features/chat/services/chat-api";
import { dispatchSendPrompt } from "@/features/chat/lib/send-prompt-event";
import { cn } from "@/lib/utils";
import type { ExecutionStep } from "@/entities/execution";

// ── Rail definition ─────────────────────────────────────────────
const RAIL_ITEMS: {
  key: RightPanelKey;
  icon: React.ElementType;
  label: string;
  badge?: string;
  badgeVariant?: "green" | "amber" | "blue";
}[] = [
  { key: "exec",    icon: TrendingUp,   label: "Exec",    badge: "✓",     badgeVariant: "green" },
  { key: "deck",    icon: Presentation, label: "Deck",    badge: "ppt",   badgeVariant: "blue" },
  { key: "skills",  icon: Wrench,       label: "Skills",  badge: "2",     badgeVariant: "blue" },
  { key: "budget",  icon: Coins,        label: "Budget" },
  { key: "log",     icon: ClipboardList,label: "Log",     badge: "live",  badgeVariant: "amber" },
  { key: "shell",   icon: Terminal,     label: "Shell" },
  { key: "prompts", icon: Eye,          label: "Prompts", badge: "1",     badgeVariant: "blue" },
  { key: "memory",  icon: Brain,        label: "Memory" },
];

const RAIL_DIVIDER_AFTER: RightPanelKey[] = ["budget", "shell"];

const PANEL_TITLES: Record<RightPanelKey, string> = {
  exec:    "Execution Path",
  deck:    "Deck Preview",
  skills:  "Skills Path",
  budget:  "Prompt Budget",
  log:     "Backend Log",
  shell:   "Shell",
  prompts: "Prompt Inspect",
  memory:  "Memory",
};

// ── Execution Path ───────────────────────────────────────────────
function ExecChip({ text }: { text: string }) {
  const isGreen  = text.startsWith("✓");
  const isAmber  = /\d+ in$/.test(text);
  const isDur    = /^\d+\.\d+s$/.test(text);
  return (
    <span className={cn(
      "inline-block px-1.5 py-0.5 rounded text-[10px] font-medium",
      isGreen ? "bg-green-100 text-green-700" :
      isAmber ? "bg-amber-100 text-amber-800" :
      isDur   ? "bg-slate-100 text-slate-500" :
                "bg-blue-50  text-blue-700"
    )}>{text}</span>
  );
}

function stepDotColor(step: ExecutionStep) {
  if (step.status === "completed") return "bg-green-500 border-green-100";
  if (step.status === "running")   return "bg-blue-500 border-blue-100 animate-pulse";
  if (step.status === "error" || step.status === "failed") return "bg-red-500 border-red-100";
  if (step.status === "cancelled" || step.status === "redirected") return "bg-amber-500 border-amber-100";
  return "bg-slate-300 border-slate-100";
}

const DEFAULT_STEER =
  "换个方向：只查本地配置里的 enabled_skills，不要再做开放网页检索。";

function DeckPreviewPanel() {
  const deckId = useDeckPreviewStore((s) => s.deckId);
  const version = useDeckPreviewStore((s) => s.version);
  const previewUrls = useDeckPreviewStore((s) => s.previewUrls);
  const selectedSlide = useDeckPreviewStore((s) => s.selectedSlide);
  const error = useDeckPreviewStore((s) => s.error);
  const versions = useDeckPreviewStore((s) => s.versions);
  const selectSlide = useDeckPreviewStore((s) => s.selectSlide);
  const selectVersion = useDeckPreviewStore((s) => s.selectVersion);
  const [steerOpen, setSteerOpen] = useState(false);
  const [steerText, setSteerText] = useState("");
  const [steerScope, setSteerScope] = useState<"slide" | "deck">("slide");

  const currentUrl = previewUrls[selectedSlide - 1];

  const submitSteer = () => {
    const need = steerText.trim();
    if (!need) {
      throw new Error(
        "[DeckPreview] PPT_STEER requires non-empty 需求\n  Actual: empty"
      );
    }
    const header =
      steerScope === "deck"
        ? `[PPT_STEER] scope=deck`
        : `[PPT_STEER] slide=${selectedSlide}`;
    const lines = [
      header,
      deckId ? `deck_id: ${deckId}` : null,
      version != null ? `version: ${version}` : null,
      `需求：${need}`,
    ].filter(Boolean);
    dispatchSendPrompt(lines.join("\n"));
    setSteerOpen(false);
    setSteerText("");
  };

  return (
    <div className="p-2 space-y-2" data-testid="deck-preview-panel">
      <div className="flex items-center justify-between gap-2">
        <div className="text-[11px] text-slate-600 truncate">
          {deckId ? (
            <>
              <span className="font-semibold text-slate-800">{deckId}</span>
              {version != null ? ` · v${version}` : ""}
              {previewUrls.length ? ` · ${previewUrls.length} slides` : ""}
            </>
          ) : (
            <span className="text-slate-400">No deck yet — save + preview in /ppt</span>
          )}
        </div>
        <div className="flex gap-1 shrink-0">
          <button
            type="button"
            data-testid="ppt-steer-slide"
            className="text-[10px] px-1.5 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-50"
            onClick={() => {
              setSteerScope("slide");
              setSteerOpen(true);
            }}
          >
            提需求·页
          </button>
          <button
            type="button"
            data-testid="ppt-steer-deck"
            className="text-[10px] px-1.5 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-50"
            onClick={() => {
              setSteerScope("deck");
              setSteerOpen(true);
            }}
          >
            提需求·全局
          </button>
        </div>
      </div>

      {error ? (
        <div className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded p-2">
          {error}
        </div>
      ) : null}

      {versions.length > 1 ? (
        <div className="flex flex-wrap gap-1" data-testid="deck-version-list">
          {versions.map((v) => (
            <button
              key={v.version}
              type="button"
              className={cn(
                "text-[10px] px-1.5 py-0.5 rounded border",
                v.version === version
                  ? "border-blue-400 bg-blue-50 text-blue-800"
                  : "border-slate-200 text-slate-500"
              )}
              onClick={() => selectVersion(v.version)}
            >
              v{v.version}
            </button>
          ))}
        </div>
      ) : null}

      {currentUrl ? (
        <div className="rounded border border-slate-200 bg-slate-50 overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={currentUrl}
            alt={`Slide ${selectedSlide}`}
            className="w-full h-auto max-h-56 object-contain bg-white"
            data-testid="deck-preview-main"
          />
        </div>
      ) : (
        <div
          className="h-28 rounded border border-dashed border-slate-200 flex items-center justify-center text-[11px] text-slate-400"
          data-testid="deck-preview-empty"
        >
          Waiting for safe_claw_ppt_preview…
        </div>
      )}

      {previewUrls.length > 0 ? (
        <div className="flex gap-1 overflow-x-auto pb-1" data-testid="deck-thumb-strip">
          {previewUrls.map((url, i) => {
            const n = i + 1;
            return (
              <button
                key={url}
                type="button"
                onClick={() => selectSlide(n)}
                className={cn(
                  "shrink-0 w-14 h-10 rounded border overflow-hidden",
                  n === selectedSlide ? "border-blue-500 ring-1 ring-blue-300" : "border-slate-200"
                )}
                data-testid={`deck-thumb-${n}`}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={url} alt={`thumb ${n}`} className="w-full h-full object-cover" />
              </button>
            );
          })}
        </div>
      ) : null}

      {steerOpen ? (
        <div
          className="rounded border border-amber-200 bg-amber-50 p-2 space-y-1.5"
          data-testid="ppt-steer-modal"
        >
          <p className="text-[10px] font-semibold text-amber-900 uppercase tracking-wide">
            {steerScope === "deck" ? "全局提需求" : `第 ${selectedSlide} 页提需求`}
          </p>
          <textarea
            data-testid="ppt-steer-input"
            className="w-full text-[12px] rounded border border-amber-200 p-1.5 min-h-[56px]"
            value={steerText}
            onChange={(e) => setSteerText(e.target.value)}
            placeholder="例如：标题改短、留白加大…"
          />
          <div className="flex gap-1 justify-end">
            <button
              type="button"
              className="text-[10px] px-2 py-1 rounded border border-slate-200 bg-white"
              onClick={() => setSteerOpen(false)}
            >
              取消
            </button>
            <button
              type="button"
              data-testid="ppt-steer-send"
              className="text-[10px] px-2 py-1 rounded bg-amber-600 text-white"
              onClick={submitSteer}
            >
              发送 PPT_STEER
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ExecPanelHeadControls() {
  const [steerOpen, setSteerOpen] = useState(false);
  const [steerHint, setSteerHint] = useState(DEFAULT_STEER);
  const haltActiveSteps = useExecutionStore((s) => s.haltActiveSteps);
  const redirectActiveSteps = useExecutionStore((s) => s.redirectActiveSteps);
  const worldStopped = useExecutionStore((s) => s.worldStopped);
  const cancelStreaming = useMessageStore((s) => s.cancelStreaming);
  const isStreaming = useMessageStore((s) => s.isStreaming);

  const onHalt = useCallback(() => {
    abortChat();
    cancelStreaming();
    haltActiveSteps();
  }, [cancelStreaming, haltActiveSteps]);

  const onSteerConfirm = useCallback(() => {
    const hint = steerHint.trim() || DEFAULT_STEER;
    abortChat();
    cancelStreaming();
    redirectActiveSteps();
    // Inject short control signal and stream a new main turn (not store-only)
    dispatchSendPrompt(
      `[USER_STEER] 要换个方向。\n新方向：${hint}\n要求：取消当前 subagent；重新看三步后 spawn；勿合并旧子轨迹。`
    );
    setSteerOpen(false);
  }, [steerHint, cancelStreaming, redirectActiveSteps]);

  // Keyboard: Esc = Halt, R = open Steer (when Exec pack open; skip if typing in inputs)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      const tag = t?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || t?.isContentEditable) return;
      if (e.key === "Escape") {
        e.preventDefault();
        onHalt();
        return;
      }
      if ((e.key === "r" || e.key === "R") && !e.metaKey && !e.ctrlKey && !e.altKey) {
        if (worldStopped || isStreaming) return;
        e.preventDefault();
        setSteerOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onHalt, worldStopped, isStreaming]);

  return (
    <>
      <div className="flex items-center gap-1 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          data-testid="exec-btn-steer"
          title="纠正方向 (R)"
          disabled={worldStopped}
          onClick={() => setSteerOpen(true)}
          className={cn(
            "h-6 px-2 rounded-md text-[11px] font-medium border",
            "bg-white text-amber-800 border-amber-300 hover:bg-amber-50",
            "disabled:opacity-40 disabled:cursor-not-allowed"
          )}
        >
          纠正方向
        </button>
        <button
          type="button"
          data-testid="exec-btn-halt"
          title="STOP THE WORLD (Esc)"
          onClick={onHalt}
          className="h-6 px-2 rounded-md text-[11px] font-medium bg-red-600 text-white hover:brightness-105"
        >
          Halt
        </button>
      </div>
      {steerOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
          data-testid="steer-modal"
          onClick={() => setSteerOpen(false)}
        >
          <div
            className="bg-white rounded-lg shadow-lg w-[420px] max-w-[90vw] p-4 space-y-3"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-sm font-semibold text-slate-800">纠正方向</p>
            <p className="text-[11px] text-slate-500">
              取消当前 subagent，并向 main 注入短控制信号（不回灌旧子轨迹）。
            </p>
            <textarea
              className="w-full h-24 text-xs border border-slate-200 rounded-md p-2"
              value={steerHint}
              onChange={(e) => setSteerHint(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="h-7 px-3 text-[11px] border border-slate-200 rounded-md"
                onClick={() => setSteerOpen(false)}
              >
                取消
              </button>
              <button
                type="button"
                data-testid="steer-confirm"
                className="h-7 px-3 text-[11px] rounded-md bg-amber-500 text-white font-medium"
                onClick={onSteerConfirm}
              >
                确认纠正并提示 Main
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function ExecStepNode({
  step,
  stepsById,
  isLast,
  nested,
}: {
  step: ExecutionStep;
  stepsById: Map<string, ExecutionStep>;
  isLast: boolean;
  nested: boolean;
}) {
  const children = (step.childrenIds || [])
    .map((id) => stepsById.get(id))
    .filter((s): s is ExecutionStep => Boolean(s));
  const isSubagent = step.type === "subagent";
  const isNestedTool = nested && step.type === "tool_call";

  return (
    <div>
      <div
        className={cn("flex gap-2", nested && "ml-3 pl-2 border-l border-slate-200")}
        data-testid={
          isSubagent ? "exec-step-subagent" : isNestedTool ? "exec-step-nested-tool" : undefined
        }
      >
        <div className="flex flex-col items-center w-5 flex-shrink-0">
          <div className={cn("w-2.5 h-2.5 rounded-full border-2 mt-0.5 flex-shrink-0", stepDotColor(step))} />
          {(!isLast || children.length > 0) && <div className="w-px flex-1 bg-slate-200 my-1" />}
        </div>
        <div className="flex-1 pb-3 min-w-0">
          <p className="text-xs font-semibold text-slate-800">{step.name}</p>
          {step.sub && (
            <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">{step.sub}</p>
          )}
          {step.chips && step.chips.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {step.chips.map((c, ci) => <ExecChip key={ci} text={c} />)}
            </div>
          )}
          {isSubagent && (
            <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-2 space-y-1.5" data-testid="subagent-block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Subagent · 默认展开
              </p>
              {step.agentName && (
                <p className="text-[11px] text-slate-600">
                  <span className="text-slate-400">agent </span>{step.agentName}
                </p>
              )}
              {step.stepNow && (
                <p className="text-[11px] text-slate-600">
                  <span className="text-slate-400">step_now </span>{step.stepNow}
                </p>
              )}
              {step.expectedOutput && (
                <p className="text-[11px] text-slate-600">
                  <span className="text-slate-400">expected </span>{step.expectedOutput}
                </p>
              )}
              {step.lookAhead && step.lookAhead.length > 0 && (
                <ol className="list-decimal list-inside space-y-0.5 mt-1">
                  {step.lookAhead.map((item, i) => (
                    <li
                      key={i}
                      data-testid="look-ahead-item"
                      className="text-[11px] text-slate-700"
                    >
                      {item}
                    </li>
                  ))}
                </ol>
              )}
              {step.error && (
                <pre className="text-[10px] text-red-700 bg-red-50 border border-red-100 rounded p-1.5 whitespace-pre-wrap">
                  {step.error}
                </pre>
              )}
            </div>
          )}
          {!isSubagent && step.error && (
            <pre className="mt-1 text-[10px] text-red-700 bg-red-50 border border-red-100 rounded p-1.5 whitespace-pre-wrap">
              {step.error}
            </pre>
          )}
        </div>
      </div>
      {children.map((child, i) => (
        <ExecStepNode
          key={child.id}
          step={child}
          stepsById={stepsById}
          isLast={i === children.length - 1}
          nested
        />
      ))}
    </div>
  );
}

function ExecutionPathPanel() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const uiStore = useUIStore();
  const currentCallIndex = mounted ? uiStore.currentCallIndex : 0;
  const totalCalls = mounted ? uiStore.totalCalls : 0;
  const nextCall = uiStore.nextCall;
  const prevCall = uiStore.prevCall;

  const execStore = useExecutionStore();
  const execution = mounted ? execStore.getLatestExecution() : undefined;
  const worldStopped = mounted ? execStore.worldStopped : false;

  const currentLLMCall = execution?.llmCalls?.[currentCallIndex];
  const steps = currentLLMCall
    ? currentLLMCall.steps.filter((s) => s.name !== "Start")
    : execution?.steps?.filter((s) => s.name !== "Start") ?? [];

  const isActive = currentLLMCall?.status === "running" || execution?.status === "running";
  const hasNext = currentCallIndex < totalCalls - 1;
  const hasPrev = currentCallIndex > 0;
  const showNav = totalCalls > 1;

  const stepsById = new Map(steps.map((s) => [s.id, s]));
  const roots = steps.filter((s) => !s.parentId || !stepsById.has(s.parentId));

  const worldBanner = worldStopped ? (
    <div
      data-testid="world-stopped-banner"
      className="mb-3 rounded-md border border-red-200 bg-red-50 px-2 py-1.5 text-[11px] font-medium text-red-700"
    >
      STOP THE WORLD · 现场冻结 · Steer 已禁用 · Esc 可再次 Halt
    </div>
  ) : null;

  if (steps.length === 0) {
    return (
      <div className="p-3 text-xs text-slate-400">
        {worldBanner}
        {showNav && (
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <button
              onClick={prevCall}
              disabled={!hasPrev}
              className={cn(
                "p-1 rounded text-[10px]",
                hasPrev ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
              )}
            >
              ← Prev
            </button>
            <span className="text-[10px] font-medium text-slate-500">
              Call {currentCallIndex + 1}/{totalCalls}
            </span>
            <button
              onClick={nextCall}
              disabled={!hasNext}
              className={cn(
                "p-1 rounded text-[10px]",
                hasNext ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
              )}
            >
              Next →
            </button>
          </div>
        )}
        {isActive ? "Execution starting..." : "Send a message to see execution plan."}
      </div>
    );
  }

  const totalDur = steps.reduce((s, st) => s + (st.duration || 0), 0);
  const callTokens = currentLLMCall?.promptTokens && currentLLMCall?.completionTokens
    ? currentLLMCall.promptTokens + currentLLMCall.completionTokens
    : undefined;

  return (
    <div className="p-3 space-y-0" data-testid="execution-path-panel">
      {worldBanner}
      {showNav && (
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
          <button
            onClick={prevCall}
            disabled={!hasPrev}
            className={cn(
              "p-1 rounded text-[10px] transition-colors",
              hasPrev ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
            )}
          >
            ← Prev
          </button>
          <span className="text-[10px] font-semibold text-red-600">
            Call {currentCallIndex + 1} of {totalCalls}
          </span>
          <button
            onClick={nextCall}
            disabled={!hasNext}
            className={cn(
              "p-1 rounded text-[10px] transition-colors",
              hasNext ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
            )}
          >
            Next →
          </button>
        </div>
      )}

      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-3">
        {currentLLMCall ? `Call #${currentLLMCall.callNumber} execution` : "Current run"}
      </p>
      {roots.map((step, i) => (
        <ExecStepNode
          key={step.id}
          step={step}
          stepsById={stepsById}
          isLast={i === roots.length - 1}
          nested={false}
        />
      ))}
      {(currentLLMCall?.status === "completed" || (!currentLLMCall && execution?.status === "completed")) && (
        <div className="flex gap-2">
          <div className="w-5 flex-shrink-0 flex justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 border-2 border-green-100 mt-0.5" />
          </div>
          <p className="text-xs font-semibold text-green-600 mt-0.5">
            ✓ Complete · {totalDur.toFixed(2)}s{callTokens ? ` · ${callTokens} tokens` : ""}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Skills Path ─────────────────────────────────────────────────
function SkillsPathPanel() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const uiStore = useUIStore();
  const currentCallIndex = mounted ? uiStore.currentCallIndex : 0;
  const totalCalls = mounted ? uiStore.totalCalls : 0;
  const nextCall = uiStore.nextCall;
  const prevCall = uiStore.prevCall;

  const execStore = useExecutionStore();
  const skillStore = useSkillStore();
  const execution = mounted ? execStore.getLatestExecution() : undefined;
  const flatSkills = mounted ? skillStore.flatSkills : [];
  const totalSkills = mounted ? skillStore.totalSkills : 0;

  // Get current LLM call
  const currentLLMCall = execution?.llmCalls?.[currentCallIndex];

  // loaded = create_deep_agent SoT; router = BM25 hints (skills_invoked)
  const loadedSet = new Set<string>();
  const routerSet = new Set<string>();
  const readySet = new Set<string>();

  if (currentLLMCall) {
    currentLLMCall.skillsLoaded?.forEach((s) => loadedSet.add(s));
    currentLLMCall.activeSkills?.forEach((s) => readySet.add(s));
    currentLLMCall.skillsInvoked?.forEach((s) => routerSet.add(s));
  } else if (execution) {
    for (const step of execution.steps) {
      step.skillsLoaded?.forEach((s) => loadedSet.add(s));
      step.activeSkills?.forEach((s) => readySet.add(s));
      step.skillsInvoked?.forEach((s) => routerSet.add(s));
    }
  }

  // Prefer actual loaded list; else enabled/ready; else store slice
  const displayNames =
    loadedSet.size > 0
      ? Array.from(loadedSet)
      : readySet.size > 0
        ? Array.from(readySet)
        : flatSkills.filter((s) => !s.isFolder).slice(0, 8).map((s) => s.name);

  const loadedCount = loadedSet.size;
  const invokedCount = routerSet.size;
  const showNav = totalCalls > 1;
  const hasNext = currentCallIndex < totalCalls - 1;
  const hasPrev = currentCallIndex > 0;

  return (
    <div className="p-3">
      {/* Navigation for LLM Calls */}
      {showNav && (
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
          <button
            onClick={prevCall}
            disabled={!hasPrev}
            className={cn(
              "p-1 rounded text-[10px] transition-colors",
              hasPrev ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
            )}
          >
            ← Prev
          </button>
          <span className="text-[10px] font-semibold text-red-600">
            Call {currentCallIndex + 1} of {totalCalls}
          </span>
          <button
            onClick={nextCall}
            disabled={!hasNext}
            className={cn(
              "p-1 rounded text-[10px] transition-colors",
              hasNext ? "hover:bg-slate-200 text-slate-600" : "text-slate-300 cursor-not-allowed"
            )}
          >
            Next →
          </button>
        </div>
      )}

      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
        {currentLLMCall ? `Call #${currentLLMCall.callNumber} skills` : "Per-message skill invocation"}
      </p>
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">
            🔧 Skills
          </span>
          <span className="text-[10px] text-slate-400 flex-1 truncate">
            {currentLLMCall ? `Call ${currentLLMCall.callNumber}` : (execution?.messageId?.slice(0, 20) || "—")}
          </span>
          <span className="text-[10px] text-green-600 font-semibold">
            {loadedCount > 0 ? `${loadedCount} loaded` : `${invokedCount} router`}
          </span>
        </div>
        {displayNames.length > 0 ? (
          displayNames.map((name, i) => {
            const loaded = loadedSet.has(name) || (loadedSet.size === 0 && readySet.has(name));
            const routed = routerSet.has(name);
            return (
              <div key={name} className={cn(
                "flex items-center gap-2 px-3 py-2 text-xs",
                i < displayNames.length - 1 && "border-b border-slate-100"
              )}>
                <Wrench className={cn(
                  "w-3.5 h-3.5 flex-shrink-0",
                  loaded ? "text-green-500" : "text-slate-300"
                )} />
                <span className={cn(
                  "flex-1 font-medium truncate",
                  loaded ? "text-slate-800" : "text-slate-400"
                )}>{name}</span>
                {loaded && (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-green-100 text-green-700">
                    loaded
                  </span>
                )}
                {routed && (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    router
                  </span>
                )}
              </div>
            );
          })
        ) : (
          <div className="px-3 py-4 text-xs text-slate-400 text-center">
            No skills activated for this call
          </div>
        )}
      </div>
      <p className="text-[10px] text-slate-400 mt-3">
        {totalSkills} skills registered · {invokedCount} active
      </p>
    </div>
  );
}

// ── Prompt Budget ───────────────────────────────────────────────
function BudgetPanel() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const execStore = useExecutionStore();
  const execution = mounted ? execStore.getLatestExecution() : undefined;
  const BUDGET_LIMIT = 8000;

  const totalTokens = execution?.metadata?.totalTokens ?? 0;
  // Try to extract prompt/completion from the done event stored in graph metadata
  // For now estimate from steps
  const llmStep = execution?.steps.find((s) => s.name === "LLM call" && s.chips);
  let promptIn = 0;
  let completionOut = 0;
  if (llmStep?.chips) {
    for (const c of llmStep.chips) {
      const inMatch = c.match(/(\d+) in$/);
      const outMatch = c.match(/(\d+) out$/);
      if (inMatch) promptIn = parseInt(inMatch[1]);
      if (outMatch) completionOut = parseInt(outMatch[1]);
    }
  }
  const total = totalTokens || (promptIn + completionOut);
  const budgetLeft = Math.max(0, BUDGET_LIMIT - total);
  const totalDur = execution?.totalDuration ?? 0;

  const cards = [
    { label: "Session Total", value: total.toLocaleString(),     sub: "tokens used",            green: false },
    { label: "Budget Left",   value: budgetLeft.toLocaleString(), sub: `of ${BUDGET_LIMIT.toLocaleString()} limit`, green: true },
    { label: "Prompt In",     value: promptIn.toLocaleString(),  sub: "tokens",                green: false },
    { label: "Completion",    value: completionOut.toLocaleString(), sub: "tokens",             green: false },
  ];

  const bars = total > 0 ? [
    { label: "Prompt In",  tokens: promptIn,      pct: (promptIn / total) * 100,      cls: "bg-blue-500" },
    { label: "Completion", tokens: completionOut,  pct: (completionOut / total) * 100, cls: "bg-green-500" },
  ] : [];

  return (
    <div className="p-3 space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {cards.map((c) => (
          <div key={c.label} className="border border-slate-200 rounded-lg p-2.5 bg-slate-50">
            <p className="text-[10px] text-slate-400">{c.label}</p>
            <p className={cn("text-lg font-bold", c.green ? "text-green-600" : "text-slate-800")}>{c.value}</p>
            <p className="text-[10px] text-slate-400">{c.sub}</p>
          </div>
        ))}
      </div>
      {bars.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Token breakdown</p>
          {bars.map((b) => (
            <div key={b.label}>
              <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                <span>{b.label}</span>
                <span className="font-medium text-slate-700 tabular-nums">{b.tokens}</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden">
                <div className={cn("h-full rounded-full", b.cls)} style={{ width: `${Math.min(b.pct, 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
      {execution && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Turn history</p>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-[10px] text-slate-400 border-b border-slate-200">
                {["Turn","In","Out","Total","Time"].map((h) => (
                  <th key={h} className="pb-1 text-left font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="text-slate-600">
                <td className="py-1">{execution.messageId?.slice(0, 8)}</td>
                <td className="tabular-nums">{promptIn}</td>
                <td className="tabular-nums">{completionOut}</td>
                <td className="tabular-nums font-semibold text-slate-800">{total}</td>
                <td className="tabular-nums">{totalDur.toFixed(2)}s</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Backend Log ─────────────────────────────────────────────────
const FAKE_LOGS = [
  { level: "INFO",  msg: "SafeClaw API started on :8000" },
  { level: "INFO",  msg: "LM Studio connected · qwen3.5-9b-vlm" },
  { level: "INFO",  msg: "Session 870c8829 loaded · 0 messages" },
  { level: "DEBUG", msg: "chat/stream POST received" },
  { level: "INFO",  msg: "Skill router: Research ✓  Analyze ✓" },
  { level: "DEBUG", msg: "Memory retrieval: 3 items injected" },
  { level: "INFO",  msg: "LLM stream started · max_tokens=512" },
  { level: "DEBUG", msg: 'SSE chunk #1 · delta="Hi"' },
  { level: "DEBUG", msg: 'SSE chunk #2 · delta=" there"' },
  { level: "INFO",  msg: "LLM stream done · 331 tokens · 1.79s" },
  { level: "INFO",  msg: "Response saved to session" },
];

function levelColor(l: string) {
  return { INFO: "#79c0ff", DEBUG: "#8b949e", WARN: "#e3b341", ERROR: "#ff7b72" }[l] ?? "#c9d1d9";
}

function ts() {
  return new Date().toTimeString().slice(0, 8);
}

function BackendLogPanel() {
  const [lines, setLines] = useState<{ time: string; level: string; msg: string }[]>([]);
  const indexRef = useRef(0);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tick = setInterval(() => {
      if (indexRef.current < FAKE_LOGS.length) {
        const entry = FAKE_LOGS[indexRef.current++];
        setLines((prev) => [...prev.slice(-120), { time: ts(), ...entry }]);
      } else {
        setLines((prev) => [
          ...prev.slice(-120),
          { time: ts(), level: "DEBUG", msg: `heartbeat · ${Math.random().toFixed(3)}s latency` },
        ]);
      }
    }, 700);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight;
  }, [lines]);

  return (
    <div className="flex flex-col h-full gap-2 p-2">
      <div className="flex items-center gap-2 px-1">
        <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" />
        <span className="text-[11px] text-slate-500">Live · uvicorn · :8000</span>
        <button
          onClick={() => setLines([])}
          className="ml-auto text-[10.5px] text-blue-500 hover:underline"
        >
          Clear
        </button>
      </div>
      <div
        ref={boxRef}
        className="flex-1 overflow-y-auto rounded-lg p-2.5 min-h-0"
        style={{ background: "#0d1117", fontFamily: "'SF Mono', Menlo, monospace", fontSize: 10.5 }}
      >
        {lines.map((l, i) => (
          <div key={i} style={{ lineHeight: 1.7, color: "#c9d1d9" }}>
            <span style={{ color: "#8b949e" }}>{l.time}</span>{" "}
            <span style={{ color: levelColor(l.level), fontWeight: 600 }}>{l.level.padEnd(5)}</span>{" "}
            {l.msg}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Shell ───────────────────────────────────────────────────────
const SHELL_PRELOAD = [
  { prompt: true,  text: "uvicorn streamlit_ui.api.main:app --port 8000" },
  { prompt: false, text: "INFO:     Started server process [8421]" },
  { prompt: false, text: "INFO:     Waiting for application startup." },
  { prompt: false, text: "INFO:     Application startup complete." },
  { prompt: false, text: "INFO:     Uvicorn running on http://0.0.0.0:8000" },
];

const FAKE_CMD_OUTPUT: Record<string, string> = {
  ls:   "safeclaw-ui/  streamlit_ui/  workspace/  start_safeclaw.sh",
  pwd:  "/Users/nicole/workspace/github/a476678244/python_gallery",
  "ps aux | grep uvicorn": "nicole  8421  uvicorn streamlit_ui.api.main:app --port 8000",
};

function ShellPanel() {
  const [history, setHistory] = useState(SHELL_PRELOAD);
  const [input, setInput] = useState("");
  const outRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (outRef.current) outRef.current.scrollTop = outRef.current.scrollHeight;
  }, [history]);

  const handleKey = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    const cmd = input.trim();
    setInput("");
    if (!cmd) return;
    setHistory((prev) => [
      ...prev,
      { prompt: true, text: cmd },
      { prompt: false, text: FAKE_CMD_OUTPUT[cmd] ?? `zsh: command not found: ${cmd.split(" ")[0]}` },
    ]);
  }, [input]);

  return (
    <div
      className="flex flex-col h-full rounded-lg overflow-hidden"
      style={{ background: "#0d1117", fontFamily: "'SF Mono', Menlo, monospace", fontSize: 11 }}
    >
      {/* title bar */}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b" style={{ borderColor: "#30363d" }}>
        {["#ff5f56","#ffbd2e","#27c93f"].map((c) => (
          <span key={c} className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: c }} />
        ))}
        <span className="ml-2 text-[10px]" style={{ color: "#8b949e" }}>zsh · python_gallery</span>
      </div>
      {/* output */}
      <div ref={outRef} className="flex-1 overflow-y-auto p-2.5 min-h-0" style={{ color: "#c9d1d9", lineHeight: 1.7 }}>
        {history.map((l, i) => (
          <div key={i}>
            {l.prompt ? (
              <>
                <span style={{ color: "#79c0ff" }}>~/python_gallery</span>{" "}
                <span style={{ color: "#8b949e" }}>$</span>{" "}
                {l.text}
              </>
            ) : (
              <span style={{ color: "#8b949e" }}>{l.text}</span>
            )}
          </div>
        ))}
      </div>
      {/* input */}
      <div className="flex items-center px-2.5 py-1.5 border-t" style={{ borderColor: "#30363d" }}>
        <span style={{ color: "#79c0ff", marginRight: 6 }}>❯</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Enter command…"
          className="flex-1 bg-transparent outline-none text-[11px]"
          style={{ color: "#c9d1d9", fontFamily: "inherit" }}
        />
      </div>
    </div>
  );
}

// ── Prompt Inspect ─────────────────────────────────────────────
interface Message {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string; // for tool calls
}

interface LLMCall {
  call_id: string;
  call_number: number;
  timestamp: string;
  messages: Message[];
  formatted_prompt: string;
  token_estimate: number;
  response?: string;
  response_timestamp?: string;
  response_tokens?: number;
  duration_ms?: number;
  model?: string;
}

// Role badge component
function RoleBadge({ role, toolName }: { role: Message["role"]; toolName?: string }) {
  const roleConfig = {
    system: { icon: "🔧", label: "SYSTEM", color: "text-violet-600", bg: "bg-violet-50", border: "border-violet-200" },
    user: { icon: "👤", label: "USER", color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" },
    assistant: { icon: "🤖", label: "ASSISTANT", color: "text-green-600", bg: "bg-green-50", border: "border-green-200" },
    tool: { icon: "🔧", label: toolName ? `TOOL: ${toolName}` : "TOOL", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" },
  };

  const config = roleConfig[role];

  return (
    <div className={cn("flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider", config.color)}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </div>
  );
}

// Message content component
function MessageContent({ content, role }: { content: string; role: Message["role"] }) {
  const borderColor = {
    system: "border-l-violet-300",
    user: "border-l-blue-300",
    assistant: "border-l-green-300",
    tool: "border-l-orange-300",
  }[role];

  return (
    <div className={cn("pl-3 border-l-2 text-[11px] text-slate-600 leading-relaxed", borderColor)}>
      {content}
    </div>
  );
}

// Prompt message component
function PromptMessage({ message, isLast }: { message: Message; isLast: boolean }) {
  return (
    <div className={cn("pb-3", !isLast && "border-b border-slate-100 mb-3")}>
      <RoleBadge role={message.role} toolName={message.name} />
      <div className="mt-1">
        <MessageContent content={message.content} role={message.role} />
      </div>
    </div>
  );
}

function PromptInspectPanel() {
  const [mounted, setMounted] = useState(false);
  const [calls, setCalls] = useState<LLMCall[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  // Use global UI store for call navigation (synced across panels)
  const uiStore = useUIStore();
  const currentCallIndex = mounted ? uiStore.currentCallIndex : 0;
  const totalCalls = mounted ? uiStore.totalCalls : 0;
  const setTotalCalls = uiStore.setTotalCalls;
  const nextCall = uiStore.nextCall;
  const prevCall = uiStore.prevCall;

  const execStore = useExecutionStore();
  const execution = mounted ? execStore.getLatestExecution() : undefined;
  const messageId = execution?.messageId;

  // Fetch LLM calls when messageId changes
  useEffect(() => {
    if (!messageId) {
      setCalls([]);
      setTotalCalls(0);
      return;
    }

    const fetchCalls = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/llm-calls/${messageId}`);
        const data = await response.json();
        const fetchedCalls = data.calls || [];
        setCalls(fetchedCalls);
        setTotalCalls(fetchedCalls.length);
      } catch (e) {
        console.error("Failed to fetch LLM calls:", e);
        setCalls([]);
        setTotalCalls(0);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCalls();

    // Poll for updates every 2 seconds while execution is running
    const interval = setInterval(() => {
      if (execution?.status === "running") {
        fetchCalls();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [messageId, execution?.status, setTotalCalls]);

  const currentCall = calls[currentCallIndex];
  const hasNext = currentCallIndex < calls.length - 1;
  const hasPrev = currentCallIndex > 0;

  // Calculate total tokens for current call
  const totalTokens = (currentCall?.token_estimate || 0) + (currentCall?.response_tokens || 0);

  if (isLoading && calls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-slate-400 text-xs p-4">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        Loading LLM calls...
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-400 text-xs text-center p-4">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <Eye className="w-7 h-7 text-slate-300" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-500 mb-1">No LLM calls recorded yet</p>
          <p className="text-slate-400">Send a message to see prompt logs</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Navigation Header - "LLM Calls N of M" */}
      <div className="flex items-center justify-between px-3 py-2.5 bg-white border-b border-slate-200">
        <button
          onClick={prevCall}
          disabled={!hasPrev}
          className={cn(
            "w-8 h-8 flex items-center justify-center rounded-lg transition-all",
            hasPrev
              ? "hover:bg-slate-100 text-slate-600 bg-slate-50"
              : "text-slate-300 cursor-not-allowed bg-transparent"
          )}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <div className="text-center">
          <p className="text-[12px] font-bold text-red-600 tracking-wide">
            LLM Calls {currentCallIndex + 1} of {totalCalls || calls.length}
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {currentCall?.duration_ms
              ? `${currentCall.duration_ms.toFixed(0)}ms • ${totalTokens.toLocaleString()} tokens`
              : "pending..."}
          </p>
        </div>
        <button
          onClick={nextCall}
          disabled={!hasNext}
          className={cn(
            "w-8 h-8 flex items-center justify-center rounded-lg transition-all",
            hasNext
              ? "hover:bg-slate-100 text-slate-600 bg-slate-50"
              : "text-slate-300 cursor-not-allowed bg-transparent"
          )}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Call Details */}
      {currentCall && (
        <div className="flex-1 overflow-y-auto bg-slate-50/50">
          {/* Prompt Section */}
          <div className="p-3">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              {/* Section Header */}
              <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border-b border-slate-200">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600">
                  Prompt Input
                </span>
                <span className="text-[9px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                  ~{currentCall.token_estimate?.toLocaleString() || "0"} tokens
                </span>
              </div>
              {/* Messages */}
              <div className="p-3 space-y-3" style={{ maxHeight: "200px", overflowY: "auto" }}>
                {currentCall.messages && currentCall.messages.length > 0 ? (
                  currentCall.messages.map((msg, i) => (
                    <PromptMessage
                      key={i}
                      message={msg}
                      isLast={i === currentCall.messages.length - 1}
                    />
                  ))
                ) : currentCall.formatted_prompt ? (
                  <div className="text-[11px] text-slate-600 whitespace-pre-wrap font-mono leading-relaxed">
                    {currentCall.formatted_prompt}
                  </div>
                ) : (
                  <div className="text-[11px] text-slate-400 italic">No prompt data available</div>
                )}
              </div>
            </div>
          </div>

          {/* Response Section */}
          <div className="px-3 pb-3">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              {/* Section Header */}
              <div className="flex items-center justify-between px-3 py-2 bg-green-50/50 border-b border-slate-200">
                <span className="text-[10px] font-bold uppercase tracking-wider text-green-600">
                  Response
                </span>
                <span className="text-[9px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {currentCall.response_tokens
                    ? `${currentCall.response_tokens.toLocaleString()} tokens`
                    : "waiting..."}
                </span>
              </div>
              {/* Response Content */}
              <div className="bg-green-50/20">
                {currentCall.response ? (
                  <div
                    className="p-3 text-[11px] text-slate-700 whitespace-pre-wrap leading-relaxed border-l-3 border-green-400"
                    style={{ maxHeight: "200px", overflowY: "auto" }}
                  >
                    {currentCall.response}
                  </div>
                ) : (
                  <div className="p-6 flex flex-col items-center justify-center gap-2 text-slate-400">
                    <span className="text-[11px]">Waiting for response...</span>
                    {execution?.status === "running" && (
                      <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Metadata Footer */}
          <div className="px-3 pb-3">
            <div className="flex items-center gap-4 px-3 py-2.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-slate-400">Call ID:</span>
                <span className="text-[10px] font-mono font-semibold text-slate-700">
                  {currentCall.call_id?.slice(-8) || "—"}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-slate-400">Time:</span>
                <span className="text-[10px] font-semibold text-slate-700">
                  {currentCall.timestamp
                    ? new Date(currentCall.timestamp).toLocaleTimeString("en-US", {
                        hour12: false,
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })
                    : "—"}
                </span>
              </div>
              {currentCall.model && (
                <div className="flex items-center gap-1.5 ml-auto">
                  <span className="text-[10px] text-slate-400">Model:</span>
                  <span className="text-[10px] font-semibold text-slate-700">
                    {currentCall.model}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Panel body renderer ─────────────────────────────────────────
function PanelBody({ panelKey }: { panelKey: RightPanelKey }) {
  switch (panelKey) {
    case "exec":    return <ExecutionPathPanel />;
    case "deck":    return <DeckPreviewPanel />;
    case "skills":  return <SkillsPathPanel />;
    case "budget":  return <BudgetPanel />;
    case "log":     return <BackendLogPanel />;
    case "shell":   return <ShellPanel />;
    case "prompts": return <PromptInspectPanel />;
    case "memory":  return <MemoryPanel />;
  }
}

// ── Vertical resize handle between panels ───────────────────────
function VerticalResizeHandle({
  onResize,
  onResizeEnd,
}: {
  onResize: (delta: number) => void;
  onResizeEnd?: () => void;
}) {
  const [isDragging, setIsDragging] = useState(false);

  // Attach listeners synchronously in mousedown — useEffect-after-state loses early moves
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
      let lastY = e.clientY;
      const handleMouseMove = (ev: MouseEvent) => {
        onResize(ev.clientY - lastY);
        lastY = ev.clientY;
      };
      const handleMouseUp = () => {
        setIsDragging(false);
        onResizeEnd?.();
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [onResize, onResizeEnd]
  );

  return (
    <div
      onMouseDown={handleMouseDown}
      className={cn(
        "h-2 flex-shrink-0 cursor-ns-resize flex items-center justify-center transition-colors",
        "hover:bg-blue-100 active:bg-blue-200",
        isDragging ? "bg-blue-100" : "bg-slate-100"
      )}
    >
      <GripHorizontal className="w-3 h-3 text-slate-400" />
    </div>
  );
}

// ── Horizontal resize handle for right panel width ──────────────
function HorizontalResizeHandle({
  onResize,
}: {
  onResize: (delta: number) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);

  // Attach listeners synchronously in mousedown — useEffect-after-state loses early moves
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
      let lastX = e.clientX;
      const handleMouseMove = (ev: MouseEvent) => {
        // Dragging left (decreasing x) should increase width
        onResize(lastX - ev.clientX);
        lastX = ev.clientX;
      };
      const handleMouseUp = () => {
        setIsDragging(false);
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [onResize]
  );

  return (
    <div
      onMouseDown={handleMouseDown}
      className={cn(
        "w-3 flex-shrink-0 cursor-ew-resize flex items-center justify-center transition-colors",
        "hover:bg-blue-100 active:bg-blue-200 border-l border-r border-slate-200",
        isDragging ? "bg-blue-100" : "bg-slate-50"
      )}
    >
      <GripVertical className="w-3 h-3 text-slate-400" />
    </div>
  );
}

// ── Accordion card ──────────────────────────────────────────────
function PanelCard({
  panelKey,
  height,
  onResize,
  memoryBadge,
}: {
  panelKey: RightPanelKey;
  height: number;
  onResize: (delta: number) => void;
  memoryBadge?: string;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const store = useUIStore();
  const def = RAIL_ITEMS.find((r) => r.key === panelKey);
  // Safety check: if panelKey is not in RAIL_ITEMS, don't render
  if (!def) {
    return null;
  }
  const Icon = def.icon;
  const expanded = mounted ? store.isPanelExpanded(panelKey) : false;
  const collapseToggle = store.collapseToggle;
  const badge = panelKey === "memory" ? memoryBadge : def.badge;

  return (
    <div
      className="flex flex-col border-b border-slate-200 flex-shrink-0 overflow-hidden"
      style={expanded ? { height } : { height: 37 }}
    >
      {/* Header — Exec keeps Halt/Steer on the product panel head */}
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2 flex-shrink-0 w-full h-[37px]",
          expanded ? "bg-slate-50 border-b border-slate-200" : ""
        )}
      >
        <button
          type="button"
          onClick={() => collapseToggle(panelKey)}
          className={cn(
            "flex items-center gap-2 flex-1 min-w-0 text-left transition-colors rounded",
            "hover:bg-slate-100/80"
          )}
        >
          <Icon className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
          <span className="flex-1 text-[11px] font-bold uppercase tracking-[0.5px] text-slate-500 truncate">
            {PANEL_TITLES[panelKey]}
          </span>
        </button>
        {panelKey === "exec" && expanded && <ExecPanelHeadControls />}
        {badge && (
          <span
            data-testid={panelKey === "memory" ? "memory-badge" : undefined}
            className={cn(
            "text-[9.5px] font-bold px-1.5 py-px rounded-full text-white flex-shrink-0",
            def.badgeVariant === "green" ? "bg-green-500" :
            def.badgeVariant === "amber" ? "bg-amber-400 !text-amber-900" :
            def.badgeVariant === "blue"  ? "bg-blue-500" : "bg-slate-400"
          )}>{badge}</span>
        )}
        <button
          type="button"
          onClick={() => collapseToggle(panelKey)}
          className="p-0.5 rounded hover:bg-slate-100"
          aria-label={expanded ? "Collapse panel" : "Expand panel"}
        >
          <ChevronDown className={cn(
            "w-3 h-3 text-slate-400 flex-shrink-0 transition-transform duration-200",
            !expanded && "-rotate-90"
          )} />
        </button>
      </div>
      {/* Body */}
      {expanded && (
        <>
          <div className="flex-1 overflow-y-auto min-h-0">
            <PanelBody panelKey={panelKey} />
          </div>
          {/* Bottom resize handle for adjusting this panel's height */}
          <VerticalResizeHandle onResize={onResize} />
        </>
      )}
    </div>
  );
}

// ── Rail button ─────────────────────────────────────────────────
function RailBtn({ item }: { item: (typeof RAIL_ITEMS)[number] }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  // Only access store after mount to ensure it's initialized
  const store = useUIStore();
  const Icon = item.icon;

  if (!mounted) {
    // Render neutral state during SSR/hydration
    return (
      <button
        title={PANEL_TITLES[item.key]}
        className="relative w-9 h-9 rounded flex flex-col items-center justify-center gap-0.5 transition-all duration-120 flex-shrink-0 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
      >
        <Icon className="w-4 h-4" />
        <span className="text-[8px] font-bold uppercase tracking-wide leading-none">{item.label}</span>
      </button>
    );
  }

  const isOpen = store.isPanelOpen(item.key);
  const isExpanded = store.isPanelExpanded(item.key);

  return (
    <button
      title={PANEL_TITLES[item.key]}
      onClick={() => store.railToggle(item.key)}
      className={cn(
        "relative w-9 h-9 rounded flex flex-col items-center justify-center gap-0.5 transition-all duration-120 flex-shrink-0",
        isExpanded
          ? "bg-blue-50 text-blue-600"
          : isOpen
          ? "text-slate-500 hover:bg-slate-200"
          : "text-slate-400 hover:bg-slate-200 hover:text-slate-700"
      )}
    >
      {isExpanded && (
        <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r bg-blue-500" />
      )}
      <Icon className="w-4 h-4" />
      <span className="text-[8px] font-bold uppercase tracking-wide leading-none">{item.label}</span>
    </button>
  );
}

// ── Root export ─────────────────────────────────────────────────
export function RightPanel() {
  const [mounted, setMounted] = useState(false);
  const [memoryCount, setMemoryCount] = useState<number | null>(null);
  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    let cancelled = false;
    const loadStats = async () => {
      try {
        const res = await fetch("/api/memory?layer=active&limit=1");
        if (!res.ok) {
          throw new Error(`Memory stats failed: ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) {
          setMemoryCount(typeof data?.stats?.total_count === "number"
            ? data.stats.total_count
            : (data?.stats?.active_count ?? 0));
        }
      } catch {
        if (!cancelled) setMemoryCount(null);
      }
    };
    loadStats();
    const id = setInterval(loadStats, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  // Access entire store - use defaults during SSR/hydration
  const store = useUIStore();
  const openPanelKeys = mounted ? store.openPanelKeys : [];
  const rightPanelWidth = mounted ? store.rightPanelWidth : 320;
  const setRightPanelWidth = store.setRightPanelWidth;
  const getPanelHeight = store.getPanelHeight;
  const setPanelHeight = store.setPanelHeight;
  const panelHeights = mounted ? store.panelHeights : {};
  const memoryBadge = memoryCount !== null ? String(memoryCount) : undefined;

  // Valid panel keys that exist in RAIL_ITEMS
  const validPanelKeys = new Set(RAIL_ITEMS.map((r) => r.key));

  const expandedKeys = openPanelKeys
    .filter((k) => !k.startsWith("!"))
    .map((k) => k as RightPanelKey)
    .filter((k) => validPanelKeys.has(k));

  const allKeys = openPanelKeys
    .map((k) => (k.startsWith("!") ? k.slice(1) : k) as RightPanelKey)
    .filter((k) => validPanelKeys.has(k));

  const anyOpen = allKeys.length > 0;
  const anyExpanded = expandedKeys.length > 0;

  // Auto-distribute heights whenever expanded panel count changes (1-3 panels).
  // Must re-run on 1→2→3 so newly opened panels share space evenly.
  useEffect(() => {
    if (expandedKeys.length === 0 || expandedKeys.length > 3) {
      return;
    }

    const RESIZE_HANDLE_HEIGHT = 8;
    const HEADER_HEIGHT = 37;
    const TOTAL_RESERVE = expandedKeys.length * (HEADER_HEIGHT + RESIZE_HANDLE_HEIGHT);
    const availableHeight = window.innerHeight - TOTAL_RESERVE;
    const autoHeight = Math.floor(availableHeight / expandedKeys.length);
    expandedKeys.forEach((key) => {
      setPanelHeight(key, autoHeight);
    });
  }, [expandedKeys.length, setPanelHeight]);

  // Resize handlers
  const handlePanelResize = useCallback((key: RightPanelKey, delta: number) => {
    const current = getPanelHeight(key);
    setPanelHeight(key, current + delta);
  }, [getPanelHeight, setPanelHeight]);

  const handleWidthResize = useCallback((delta: number) => {
    setRightPanelWidth(rightPanelWidth + delta);
  }, [rightPanelWidth, setRightPanelWidth]);

  return (
    <div className="flex flex-row h-screen flex-shrink-0">
      {/* Horizontal resize handle - on the LEFT side of the panel (next to chat) */}
      {mounted && anyOpen && (
        <HorizontalResizeHandle onResize={handleWidthResize} />
      )}

      {/* Accordion stack — shown whenever at least one panel is open; hidden on SSR to avoid hydration mismatch */}
      <div
        className={cn(
          "flex flex-col border-l border-slate-200 bg-white overflow-x-hidden transition-all duration-220",
          mounted && anyOpen ? "opacity-100" : "w-0 opacity-0",
          // Allow scrolling when >3 panels, otherwise fit to viewport
          expandedKeys.length > 3 ? "overflow-y-auto" : "overflow-y-hidden"
        )}
        style={mounted && anyOpen ? { width: rightPanelWidth } : undefined}
      >
        {mounted && allKeys.map((key) => (
          <PanelCard
            key={key}
            panelKey={key}
            height={getPanelHeight(key)}
            onResize={(delta) => handlePanelResize(key, delta)}
            memoryBadge={memoryBadge}
          />
        ))}
      </div>

      {/* Icon rail */}
      <nav className="w-11 min-w-[44px] border-l border-slate-200 bg-slate-50 flex flex-col items-center py-2 gap-0.5 overflow-y-auto h-full">
        {RAIL_ITEMS.map((item) => (
          <div key={item.key} className="flex flex-col items-center gap-0.5 w-full px-1">
            <RailBtn
              item={
                item.key === "memory" && memoryBadge
                  ? { ...item, badge: memoryBadge }
                  : item
              }
            />
            {RAIL_DIVIDER_AFTER.includes(item.key) && (
              <div className="w-6 h-px bg-slate-200 my-1" />
            )}
          </div>
        ))}
      </nav>
    </div>
  );
}
