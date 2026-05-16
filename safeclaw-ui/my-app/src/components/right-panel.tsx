"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  TrendingUp,
  Wrench,
  Coins,
  ClipboardList,
  Terminal,
  FileText,
  Brain,
  ChevronDown,
  Globe,
  BarChart3,
  Zap,
  Bot,
} from "lucide-react";
import { useUIStore, type RightPanelKey } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

// ── Rail definition ─────────────────────────────────────────────
const RAIL_ITEMS: {
  key: RightPanelKey;
  icon: React.ElementType;
  label: string;
  badge?: string;
  badgeVariant?: "green" | "amber" | "blue";
}[] = [
  { key: "exec",    icon: TrendingUp,   label: "Exec",    badge: "✓",     badgeVariant: "green" },
  { key: "skills",  icon: Wrench,       label: "Skills",  badge: "2",     badgeVariant: "blue" },
  { key: "budget",  icon: Coins,        label: "Budget" },
  { key: "log",     icon: ClipboardList,label: "Log",     badge: "live",  badgeVariant: "amber" },
  { key: "shell",   icon: Terminal,     label: "Shell" },
  { key: "context", icon: FileText,     label: "Context" },
  { key: "memory",  icon: Brain,        label: "Memory",  badge: "3" },
];

const RAIL_DIVIDER_AFTER: RightPanelKey[] = ["budget", "shell"];

const PANEL_TITLES: Record<RightPanelKey, string> = {
  exec:    "Execution Path",
  skills:  "Skills Path",
  budget:  "Prompt Budget",
  log:     "Backend Log",
  shell:   "Shell",
  context: "Context Files",
  memory:  "Memory",
};

// ── Execution Path ───────────────────────────────────────────────
const EXEC_STEPS = [
  { id: "parse",    name: "Understanding request", sub: "Parsed intent & entities", status: "done", chips: ["✓ done", "0.31s"] },
  { id: "router",   name: "Skill router",          sub: "Selected: Research, Analyze", status: "done", chips: ["✓ done", "Research", "Analyze", "0.12s"] },
  { id: "memory",   name: "Memory retrieval",      sub: "3 relevant memories loaded", status: "done", chips: ["✓ done", "0.08s", "3 memories"] },
  { id: "llm",      name: "LLM call",              sub: "qwen3.5 · stream · 512 max tokens", status: "done", chips: ["✓ done", "1.79s", "231 in", "331 out"] },
];

function ExecChip({ text }: { text: string }) {
  const isGreen  = text.startsWith("✓");
  const isBlue   = ["Research","Analyze"].includes(text);
  const isAmber  = text.includes("in");
  return (
    <span className={cn(
      "inline-block px-1.5 py-0.5 rounded text-[10px] font-medium",
      isGreen ? "bg-green-100 text-green-700" :
      isBlue  ? "bg-blue-50  text-blue-700" :
      isAmber ? "bg-amber-100 text-amber-800" :
                "bg-slate-100 text-slate-500"
    )}>{text}</span>
  );
}

function ExecutionPathPanel() {
  return (
    <div className="p-3 space-y-0">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-3">
        Current run · msg-1747120230
      </p>
      {EXEC_STEPS.map((step, i) => (
        <div key={step.id} className="flex gap-2">
          <div className="flex flex-col items-center w-5 flex-shrink-0">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 border-2 border-green-100 mt-0.5 flex-shrink-0" />
            {i < EXEC_STEPS.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1" />}
          </div>
          <div className="flex-1 pb-3 min-w-0">
            <p className="text-xs font-semibold text-slate-800">{step.name}</p>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">{step.sub}</p>
            <div className="flex flex-wrap gap-1 mt-1.5">
              {step.chips.map((c) => <ExecChip key={c} text={c} />)}
            </div>
          </div>
        </div>
      ))}
      <div className="flex gap-2">
        <div className="w-5 flex-shrink-0 flex justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 border-2 border-green-100 mt-0.5" />
        </div>
        <p className="text-xs font-semibold text-green-600 mt-0.5">✓ Complete · 2.30s · 562 tokens</p>
      </div>
    </div>
  );
}

// ── Skills Path ─────────────────────────────────────────────────
const SKILLS_DATA = [
  { icon: Globe,    name: "Research",         status: "invoked", time: "0.45s" },
  { icon: BarChart3,name: "Analyze",          status: "invoked", time: "0.31s" },
  { icon: Zap,      name: "Code",             status: "skipped", time: "—" },
  { icon: Bot,      name: "cue-regeneration", status: "skipped", time: "—" },
];

function SkillsPathPanel() {
  return (
    <div className="p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
        Per-message skill invocation
      </p>
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">💬 msg-1</span>
          <span className="text-[11px] text-slate-400 flex-1 truncate">Analyze Macan tire market</span>
          <span className="text-[10px] text-green-600 font-semibold">2 invoked</span>
        </div>
        {SKILLS_DATA.map((s, i) => (
          <div key={s.name} className={cn(
            "flex items-center gap-2 px-3 py-2 text-xs",
            i < SKILLS_DATA.length - 1 && "border-b border-slate-100"
          )}>
            <s.icon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            <span className="flex-1 font-medium text-slate-700 truncate">{s.name}</span>
            <span className={cn(
              "text-[10px] font-semibold px-1.5 py-0.5 rounded",
              s.status === "invoked" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-400"
            )}>{s.status}</span>
            <span className="text-[10px] text-slate-400 w-8 text-right">{s.time}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-slate-400 mt-3">5 skills registered · 2 active this session</p>
    </div>
  );
}

// ── Prompt Budget ───────────────────────────────────────────────
function BudgetPanel() {
  const cards = [
    { label: "Session Total", value: "562",   sub: "tokens used" },
    { label: "Budget Left",   value: "7,438", sub: "of 8,000 limit", green: true },
    { label: "Prompt In",     value: "231",   sub: "tokens" },
    { label: "Completion",    value: "331",   sub: "tokens" },
  ];
  const bars = [
    { label: "System prompt",    pct: 15.6, tokens: 88,  cls: "bg-purple-400" },
    { label: "User message",     pct: 9.8,  tokens: 55,  cls: "bg-blue-500" },
    { label: "Memory injection", pct: 15.6, tokens: 88,  cls: "bg-amber-400" },
    { label: "Completion",       pct: 58.9, tokens: 331, cls: "bg-green-500" },
  ];
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
      <div className="space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Token breakdown</p>
        {bars.map((b) => (
          <div key={b.label}>
            <div className="flex justify-between text-[11px] text-slate-500 mb-1">
              <span>{b.label}</span>
              <span className="font-medium text-slate-700 tabular-nums">{b.tokens}</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden">
              <div className={cn("h-full rounded-full", b.cls)} style={{ width: `${b.pct}%` }} />
            </div>
          </div>
        ))}
      </div>
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
              <td className="py-1">msg-1</td>
              <td className="tabular-nums">231</td>
              <td className="tabular-nums">331</td>
              <td className="tabular-nums font-semibold text-slate-800">562</td>
              <td className="tabular-nums">2.30s</td>
            </tr>
          </tbody>
        </table>
      </div>
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

// ── Context / Memory ────────────────────────────────────────────
function ContextPanel() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2 text-slate-400 text-xs text-center p-4">
      <FileText className="w-8 h-8 text-slate-300" />
      No context files attached.
      <span className="text-slate-300">Drop files or use 📎 in the input bar.</span>
    </div>
  );
}

function MemoryPanel() {
  const items = [
    { icon: "🔍", title: "User prefers Michelin tires",       sub: "Mentioned in 2 previous sessions" },
    { icon: "🚗", title: "Vehicle: Porsche Macan 2022",       sub: "Stored 3 days ago" },
    { icon: "💰", title: "Budget preference: mid-range",      sub: "Inferred from conversation history" },
  ];
  return (
    <div className="p-3 space-y-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Active memories · this session</p>
      {items.map((m) => (
        <div key={m.title} className="border border-slate-200 rounded-lg p-2.5 text-xs">
          <p className="font-semibold text-slate-800 mb-0.5">{m.icon} {m.title}</p>
          <p className="text-slate-400">{m.sub}</p>
        </div>
      ))}
    </div>
  );
}

// ── Panel body renderer ─────────────────────────────────────────
function PanelBody({ panelKey }: { panelKey: RightPanelKey }) {
  switch (panelKey) {
    case "exec":    return <ExecutionPathPanel />;
    case "skills":  return <SkillsPathPanel />;
    case "budget":  return <BudgetPanel />;
    case "log":     return <BackendLogPanel />;
    case "shell":   return <ShellPanel />;
    case "context": return <ContextPanel />;
    case "memory":  return <MemoryPanel />;
  }
}

// ── Accordion card ──────────────────────────────────────────────
function PanelCard({ panelKey }: { panelKey: RightPanelKey }) {
  const collapseToggle = useUIStore((s) => s.collapseToggle);
  const expanded = useUIStore((s) => s.isPanelExpanded(panelKey));
  const def = RAIL_ITEMS.find((r) => r.key === panelKey)!;
  const Icon = def.icon;

  return (
    <div
      className={cn(
        "flex flex-col border-b border-slate-200 flex-shrink-0 overflow-hidden transition-all duration-250",
        expanded
          ? "min-h-[calc(100vh/3)] max-h-[calc(100vh/3)]"
          : "min-h-0 max-h-[37px]"
      )}
    >
      {/* Header */}
      <button
        onClick={() => collapseToggle(panelKey)}
        className={cn(
          "flex items-center gap-2 px-3 py-2 flex-shrink-0 w-full text-left transition-colors",
          expanded ? "bg-slate-50 border-b border-slate-200 hover:bg-slate-100" : "hover:bg-slate-50"
        )}
      >
        <Icon className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        <span className="flex-1 text-[11px] font-bold uppercase tracking-[0.5px] text-slate-500">
          {PANEL_TITLES[panelKey]}
        </span>
        {def.badge && (
          <span className={cn(
            "text-[9.5px] font-bold px-1.5 py-px rounded-full text-white flex-shrink-0",
            def.badgeVariant === "green" ? "bg-green-500" :
            def.badgeVariant === "amber" ? "bg-amber-400 !text-amber-900" :
            def.badgeVariant === "blue"  ? "bg-blue-500" : "bg-slate-400"
          )}>{def.badge}</span>
        )}
        <ChevronDown className={cn(
          "w-3 h-3 text-slate-400 flex-shrink-0 transition-transform duration-200",
          !expanded && "-rotate-90"
        )} />
      </button>
      {/* Body */}
      {expanded && (
        <div className="flex-1 overflow-y-auto min-h-0">
          <PanelBody panelKey={panelKey} />
        </div>
      )}
    </div>
  );
}

// ── Rail button ─────────────────────────────────────────────────
function RailBtn({ item }: { item: (typeof RAIL_ITEMS)[number] }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const railToggle = useUIStore((s) => s.railToggle);
  const isOpen     = useUIStore((s) => s.isPanelOpen(item.key));
  const isExpanded = useUIStore((s) => s.isPanelExpanded(item.key));
  const Icon = item.icon;

  // Before mount, render neutral state to match SSR output
  const activeExpanded = mounted && isExpanded;
  const activeOpen     = mounted && isOpen;

  return (
    <button
      title={PANEL_TITLES[item.key]}
      onClick={() => railToggle(item.key)}
      className={cn(
        "relative w-9 h-9 rounded flex flex-col items-center justify-center gap-0.5 transition-all duration-120 flex-shrink-0",
        activeExpanded
          ? "bg-blue-50 text-blue-600"
          : activeOpen
          ? "text-slate-500 hover:bg-slate-200"
          : "text-slate-400 hover:bg-slate-200 hover:text-slate-700"
      )}
    >
      {activeExpanded && (
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
  useEffect(() => { setMounted(true); }, []);

  const openPanelKeys = useUIStore((s) => s.openPanelKeys);

  const expandedKeys = openPanelKeys
    .filter((k) => !k.startsWith("!"))
    .map((k) => k as RightPanelKey);

  const anyExpanded = expandedKeys.length > 0;
  const allKeys = openPanelKeys.map((k) =>
    k.startsWith("!") ? (k.slice(1) as RightPanelKey) : (k as RightPanelKey)
  );

  return (
    <div className="flex flex-row h-screen flex-shrink-0">
      {/* Accordion stack — hidden on SSR to avoid hydration mismatch */}
      <div
        className={cn(
          "flex flex-col border-l border-slate-200 bg-white overflow-x-hidden overflow-y-auto transition-all duration-220",
          mounted && anyExpanded ? "w-80" : "w-0"
        )}
      >
        {mounted && allKeys.map((key) => (
          <PanelCard key={key} panelKey={key} />
        ))}
      </div>

      {/* Icon rail */}
      <nav className="w-11 min-w-[44px] border-l border-slate-200 bg-slate-50 flex flex-col items-center py-2 gap-0.5 overflow-y-auto h-full">
        {RAIL_ITEMS.map((item) => (
          <div key={item.key} className="flex flex-col items-center gap-0.5 w-full px-1">
            <RailBtn item={item} />
            {RAIL_DIVIDER_AFTER.includes(item.key) && (
              <div className="w-6 h-px bg-slate-200 my-1" />
            )}
          </div>
        ))}
      </nav>
    </div>
  );
}
