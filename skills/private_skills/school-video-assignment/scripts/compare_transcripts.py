#!/usr/bin/env python3
"""Diff two ASR passes of the same take to separate real mispronunciations from ASR noise.

    python compare_transcripts.py asr_raw.json asr_denoised.json --media INPUT.mp4 --clips OUT_DIR

Same recording, two audio conditions:
  * the two passes DISAGREE  -> the audio was ambiguous, ASR guessed; usually not the kid's fault
  * the two passes AGREE on something wrong -> the kid probably really said it that way

It also doubles as the safety check for the noise gate: if the cleaned pass drops
syllables, similarity falls and the missing text shows up as a deletion.
"""

from __future__ import annotations

import argparse
import difflib
import json
import subprocess
from pathlib import Path


def load(path: Path) -> tuple[str, list[dict]]:
    item = json.loads(path.read_text(encoding="utf-8"))[0]
    sents = [
        {"start": s["start"] / 1000.0, "end": s["end"] / 1000.0, "text": s["text"]}
        for s in item.get("sentence_info", [])
    ]
    return item.get("text", ""), sents


def locate(sents: list[dict], text: str) -> float:
    """Rough source time for a snippet, by scanning concatenated sentence text."""
    pos = 0
    for s in sents:
        if text and text[0] in s["text"]:
            return s["start"]
        pos += len(s["text"])
    return sents[0]["start"] if sents else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_json", type=Path)
    ap.add_argument("clean_json", type=Path)
    ap.add_argument("--media", type=Path, help="source file, needed for --clips")
    ap.add_argument("--clips", type=Path, help="write listen-and-check clips here")
    ap.add_argument("--pad", type=float, default=1.5, help="seconds of context per clip")
    args = ap.parse_args()

    raw_text, raw_sents = load(args.raw_json)
    clean_text, clean_sents = load(args.clean_json)

    ratio = difflib.SequenceMatcher(None, raw_text, clean_text).ratio()
    print(f"原始 {len(raw_text)} 字 / 降噪后 {len(clean_text)} 字 / 相似度 {ratio:.3f}")
    if ratio >= 0.97:
        print("✅ 两遍基本一致 —— 降噪与噪声门没有吃掉字\n")
    else:
        print("⚠️  差异偏大，检查降噪是否过强（尤其 agate threshold）\n")

    sm = difflib.SequenceMatcher(None, raw_text, clean_text)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        a, b = raw_text[i1:i2], clean_text[j1:j2]
        if not (a.strip() or b.strip()):
            continue
        ctx = raw_text[max(0, i1 - 6): i2 + 6]
        t = locate(raw_sents, a or b)
        diffs.append({"t": t, "raw": a, "clean": b, "ctx": ctx})

    if diffs:
        print(f"两遍不一致的 {len(diffs)} 处（噪声敏感，念得清不清楚看这里）:")
        for d in diffs:
            print(f"  [{d['t']:7.2f}] 原始「{d['raw']}」 vs 降噪「{d['clean']}」   …{d['ctx']}…")
    else:
        print("两遍完全一致。")

    print(
        "\n注意：两遍一致 ≠ 念对了。专有名词（人名、型号、成语）即使两遍一致，"
        "也要照着讲稿核对一遍，ASR 会稳定地把同一个音识别成同一个错字。"
    )

    if args.clips and args.media:
        args.clips.mkdir(parents=True, exist_ok=True)
        for n, d in enumerate(diffs, 1):
            start = max(0.0, d["t"] - args.pad)
            label = (d["raw"] or d["clean"]).strip()[:10].replace("/", "_") or "diff"
            out = args.clips / f"{n:02d}_{label}.m4a"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}",
                 "-t", f"{args.pad * 2 + 2}", "-i", str(args.media), "-vn",
                 "-af", "loudnorm=I=-16:TP=-2:LRA=11", "-c:a", "aac", "-b:a", "128k", str(out)],
                check=True,
            )
        print(f"\n试听片段 -> {args.clips}")


if __name__ == "__main__":
    main()
