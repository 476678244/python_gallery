"use client";

import type { PlanArtifact } from "@/features/chat/lib/parse-plan-artifact";
import { useSessionStore } from "@/stores/session-store";
import { useUIStore } from "@/stores/ui-store";
import { modeWriteChips } from "@/entities/agent-mode";

interface PlanArtifactCardProps {
  plan: PlanArtifact;
  sessionId: string | null | undefined;
}

/**
 * Dedicated Plan-mode structure bone (steps / risks / pending).
 * CTAs switch session mode only — never auto-execute (methodology).
 */
export function PlanArtifactCard({ plan, sessionId }: PlanArtifactCardProps) {
  const updateSessionSettings = useSessionStore((s) => s.updateSessionSettings);
  const applyObservabilityPack = useUIStore((s) => s.applyObservabilityPack);

  const switchMode = (mode: "agent" | "safe") => {
    if (!sessionId) {
      throw new Error(
        `[PlanArtifactCard] Cannot switch mode without session\n  mode: ${mode}`
      );
    }
    updateSessionSettings(sessionId, { mode });
    applyObservabilityPack(modeWriteChips(mode).observability);
  };

  return (
    <div
      data-testid="plan-artifact"
      className="mt-2 rounded-[10px] border border-violet-200 bg-violet-50/80 overflow-hidden"
    >
      <div className="px-2.5 py-2 bg-violet-50 border-b border-violet-200">
        <p className="text-[11px] font-bold uppercase tracking-wide text-violet-700">
          Plan artifact · readonly
        </p>
      </div>

      {plan.intro ? (
        <p className="px-2.5 pt-2 text-[12px] text-slate-600 leading-snug">
          {plan.intro}
        </p>
      ) : null}

      <ol className="m-0 py-2.5 pl-7 pr-2.5 list-decimal text-[12.5px] leading-relaxed text-slate-800 space-y-1">
        {plan.steps.map((step, i) => (
          <li key={i} data-testid="plan-step">
            {step}
          </li>
        ))}
      </ol>

      {plan.risks.length > 0 && (
        <div
          data-testid="plan-risks"
          className="border-t border-violet-200 px-2.5 py-2 text-[11.5px] text-amber-900 bg-amber-50"
        >
          <p className="font-semibold text-[10px] uppercase tracking-wide text-amber-800 mb-1">
            Risks
          </p>
          <ul className="list-disc pl-4 space-y-0.5">
            {plan.risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {plan.pending.length > 0 && (
        <div
          data-testid="plan-pending"
          className="border-t border-violet-200 px-2.5 py-2 text-[11.5px] text-slate-700 bg-white/70"
        >
          <p className="font-semibold text-[10px] uppercase tracking-wide text-slate-500 mb-1">
            Pending confirmation
          </p>
          <ul className="list-disc pl-4 space-y-0.5">
            {plan.pending.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="border-t border-violet-200 px-2.5 py-2 flex flex-wrap gap-2 bg-violet-50/50">
        <button
          type="button"
          data-testid="plan-switch-agent"
          onClick={() => switchMode("agent")}
          className="h-6 px-2.5 rounded-md text-[11px] font-medium bg-blue-600 text-white hover:brightness-105"
        >
          切换到 Agent 执行
        </button>
        <button
          type="button"
          data-testid="plan-switch-safe"
          onClick={() => switchMode("safe")}
          className="h-6 px-2.5 rounded-md text-[11px] font-medium border border-emerald-300 bg-white text-emerald-800 hover:bg-emerald-50"
        >
          切换到 Safe 新建
        </button>
        <span className="text-[10px] text-slate-400 self-center">
          不自动开写 · 须显式切换
        </span>
      </div>
    </div>
  );
}
