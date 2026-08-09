"use client";

import type { DeckArtifact } from "@/features/chat/lib/parse-deck-artifact";
import { dispatchSendPrompt } from "@/features/chat/lib/send-prompt-event";

interface DeckArtifactCardProps {
  deck: DeckArtifact;
}

/**
 * PPT outline bone: confirm → generate via tools; revise outline via short prompt.
 * Does not switch mode (already /ppt).
 */
export function DeckArtifactCard({ deck }: DeckArtifactCardProps) {
  const onConfirm = () => {
    dispatchSendPrompt(
      [
        "确认出稿。",
        "请按当前 Deck Outline / Slide Storyboard 调用 safe_claw_ppt_*：",
        "deck_init → slide_upsert（每页）→ save_version → preview。",
        "不要只口头承诺；必须落盘 _v1.pptx 并刷新 Deck Preview。",
      ].join("\n")
    );
  };

  const onRevise = () => {
    dispatchSendPrompt("调整大纲：");
  };

  return (
    <div
      data-testid="deck-artifact"
      className="mt-2 rounded-[10px] border border-sky-200 bg-sky-50/80 overflow-hidden"
    >
      <div className="px-2.5 py-2 bg-sky-50 border-b border-sky-200">
        <p className="text-[11px] font-bold uppercase tracking-wide text-sky-800">
          Deck outline · /ppt
        </p>
      </div>

      {deck.intro ? (
        <p className="px-2.5 pt-2 text-[12px] text-slate-600 leading-snug">
          {deck.intro}
        </p>
      ) : null}

      {deck.outline.length > 0 ? (
        <div className="px-2.5 py-2" data-testid="deck-outline">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
            Outline
          </p>
          <ol className="m-0 pl-5 list-decimal text-[12.5px] leading-relaxed text-slate-800 space-y-1">
            {deck.outline.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ol>
        </div>
      ) : null}

      {deck.storyboard.length > 0 ? (
        <div
          className="border-t border-sky-200 px-2.5 py-2 bg-white/60"
          data-testid="deck-storyboard"
        >
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
            Slide storyboard
          </p>
          <ol className="m-0 pl-5 list-decimal text-[12.5px] leading-relaxed text-slate-800 space-y-1">
            {deck.storyboard.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ol>
        </div>
      ) : null}

      {deck.pending.length > 0 ? (
        <div
          className="border-t border-sky-200 px-2.5 py-2 text-[11.5px] text-slate-700"
          data-testid="deck-pending"
        >
          <p className="font-semibold text-[10px] uppercase tracking-wide text-slate-500 mb-1">
            Pending confirmation
          </p>
          <ul className="list-disc pl-4 space-y-0.5">
            {deck.pending.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="border-t border-sky-200 px-2.5 py-2 flex flex-wrap gap-2 bg-sky-50/50">
        <button
          type="button"
          data-testid="deck-confirm-generate"
          onClick={onConfirm}
          className="h-6 px-2.5 rounded-md text-[11px] font-medium bg-sky-700 text-white hover:brightness-105"
        >
          确认出稿
        </button>
        <button
          type="button"
          data-testid="deck-revise-outline"
          onClick={onRevise}
          className="h-6 px-2.5 rounded-md text-[11px] font-medium border border-sky-300 bg-white text-sky-900 hover:bg-sky-50"
        >
          改大纲
        </button>
        <span className="text-[10px] text-slate-400 self-center">
          出稿走 safe_claw_ppt_* · 不改 mode
        </span>
      </div>
    </div>
  );
}
