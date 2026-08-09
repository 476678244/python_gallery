#!/usr/bin/env python3
"""Turn an ASR result into a draft edit plan: which pauses to squeeze, which NG takes to drop.

    python find_edit_points.py asr_raw.json INPUT.mp4 -o edit_plan.json

Kids re-record a sentence mid-take and nobody trims it, so the giveaways are:
  * a long silent gap *inside* one sentence  -> stumble, the retry follows
  * two neighbouring sentences with the same text -> one is a leftover take
  * a sentence starting with a doubled character ("今今天") -> false start

Auto-generated cuts are a starting point. Read them, keep the deliberate pauses,
then hand-write the `anchors` list before running build_timeline.py.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PUNCT = "，。？！、；：""''…—《》 "

# Legitimate reduplication, not a false start.
REDUP_OK = {
    "谢谢", "看看", "想想", "说说", "试试", "常常", "刚刚", "渐渐", "偏偏", "仅仅",
    "天天", "每每", "年年", "处处", "件件", "个个", "多多", "深深", "远远", "牢牢",
    "妈妈", "爸爸", "爷爷", "奶奶", "哥哥", "姐姐", "弟弟", "妹妹", "叔叔", "阿阿",
    "星星", "宝宝", "娃娃", "圈圈", "轻轻", "慢慢", "悄悄", "偷偷", "统统", "白白",
}


def probe(path: Path) -> tuple[float, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate,nb_frames",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    num, den = out[0].split("/")
    return float(num) / float(den), int(out[1])


def norm(text: str) -> str:
    return "".join(c for c in text if c not in PUNCT)


def sentences(asr_path: Path) -> list[dict]:
    item = json.loads(asr_path.read_text(encoding="utf-8"))[0]
    out = []
    for s in item.get("sentence_info", []):
        out.append(
            {
                "start": s["start"] / 1000.0,
                "end": s["end"] / 1000.0,
                "text": s["text"],
                "norm": norm(s["text"]),
                "chars": [(a / 1000.0, b / 1000.0) for a, b in (s.get("timestamp") or [])],
            }
        )
    return out


def internal_stumble(sent: dict, min_gap: float) -> tuple[float, float] | None:
    """Largest silent gap between two characters of one sentence."""
    best = None
    for (_, prev_end), (next_start, _) in zip(sent["chars"], sent["chars"][1:]):
        gap = next_start - prev_end
        if gap >= min_gap and (best is None or gap > best[1] - best[0]):
            best = (prev_end, next_start)
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("asr_json", type=Path)
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("edit_plan.json"))
    ap.add_argument("--pause-max", type=float, default=1.3, help="squeeze gaps longer than this")
    ap.add_argument("--pause-target", type=float, default=0.6, help="what to squeeze them down to")
    ap.add_argument("--para-pause", type=float, default=1.2, help="pause kept at paragraph breaks")
    ap.add_argument("--stumble-gap", type=float, default=1.5, help="in-sentence silence = stumble")
    args = ap.parse_args()

    fps, n_frames = probe(args.video)
    duration = n_frames / fps
    sents = sentences(args.asr_json)

    cuts: list[list] = []
    review: list[dict] = []

    if sents and sents[0]["start"] > 0.5:
        cuts.append([0.0, round(sents[0]["start"] - 0.4, 2), "开场静音"])

    for i, s in enumerate(sents):
        # false start: 今今天 / 我我们
        m = re.match(r"^(.)\1", s["norm"])
        if m and s["chars"] and s["norm"][:2] not in REDUP_OK:
            review.append(
                {"time": round(s["start"], 2), "kind": "重复首字",
                 "text": s["text"], "hint": f"删掉第一个「{m.group(1)}」"}
            )

        # stumble inside one sentence: squeeze it, but say so loudly, because if the
        # words after the gap are a retry the cut needs widening to swallow the retry
        gap = internal_stumble(s, args.stumble_gap)
        if gap:
            slack = (gap[1] - gap[0] - args.pause_target) / 2
            cuts.append([round(gap[0] + slack, 2), round(gap[1] - slack, 2),
                         f"句内静默 {gap[1]-gap[0]:.1f}s → {args.pause_target:.1f}s（若后半是重录请改成整段删除）"])
            review.append(
                {"time": round(gap[0], 2), "kind": "句内卡壳",
                 "text": s["text"],
                 "hint": f"{gap[0]:.2f}-{gap[1]:.2f} 静默 {gap[1]-gap[0]:.1f}s，"
                         f"已按压缩处理；若后面是重录，请把这条 cut 扩成整段删除"}
            )

        # leftover take: same words again within the next two sentences
        for j in range(i + 1, min(i + 3, len(sents))):
            a, b = s["norm"], sents[j]["norm"]
            if len(a) >= 3 and (a == b or a in b or b in a):
                review.append(
                    {"time": round(s["start"], 2), "kind": "疑似重复句",
                     "text": f"{s['text']}  ⟷  {sents[j]['text']}",
                     "hint": "确认是排比强调还是没剪掉的重录"}
                )
                break

        # inter-sentence pause
        if i + 1 < len(sents):
            gap_a, gap_b = s["end"], sents[i + 1]["start"]
            if gap_b - gap_a > args.pause_max:
                # a sentence-final 。！？ reads as a paragraph break, leave more air
                keep = args.para_pause if s["text"][-1:] in "。！？" else args.pause_target
                slack = (gap_b - gap_a - keep) / 2
                cuts.append([round(gap_a + slack, 2), round(gap_b - slack, 2),
                             f"停顿 {gap_b-gap_a:.1f}s → {keep:.1f}s"])

    if sents and duration - sents[-1]["end"] > 0.8:
        cuts.append([round(sents[-1]["end"] + 0.5, 2), round(duration, 2), "结尾静音"])

    saved = sum(b - a for a, b, _ in cuts)
    plan = {
        "_note": "时间为源视频秒数。cuts 已自动生成，请逐条复核；anchors 需按讲词内容手写。",
        "source": str(args.video),
        "fps": fps,
        "frames": n_frames,
        "cuts": cuts,
        "anchors": [[round(s["start"], 2), "ready/REPLACE.jpg", s["text"][:28]]
                    for s in sents if s["text"][-1:] in "。！？"][:24],
        "review": review,
    }
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"源 {duration:.1f}s / {len(sents)} 句")
    print(f"自动剪辑 {len(cuts)} 处，共 {saved:.1f}s → 预计成片 {duration - saved:.1f}s\n")
    if review:
        print("需要人工判断的地方:")
        for r in review:
            print(f"  [{r['time']:7.2f}] {r['kind']}: {r['text']}")
            print(f"            → {r['hint']}")
    print(f"\n-> {args.output}（anchors 里的 REPLACE.jpg 要换成真实配图）")


if __name__ == "__main__":
    main()
