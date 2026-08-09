#!/usr/bin/env python3
"""Expand edit_plan.json into everything the compositor needs.

    python build_timeline.py edit_plan.json --work work --backgrounds backgrounds

Writes:
    work/keep_frames.json        frame runs that survive the cuts
    work/audio_select.txt        matching ffmpeg aselect expression
    backgrounds/storyboard_aligned.json   background switches on the *trimmed* timeline

The anchors in edit_plan.json are written against the original recording, because that
is what the transcript timestamps refer to. Cuts shift everything left, so anchor times
have to be re-mapped or the pictures drift away from the words.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def keep_frames(cuts: list[tuple[float, float]], n: int, fps: float) -> list[int]:
    return [i for i in range(n) if not any(a <= i / fps < b for a, b in cuts)]


def to_runs(frames: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start = prev = frames[0]
    for f in frames[1:]:
        if f == prev + 1:
            prev = f
            continue
        runs.append((start, prev))
        start = prev = f
    runs.append((start, prev))
    return runs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--backgrounds", type=Path, default=Path("backgrounds"))
    ap.add_argument("--min-segment", type=float, default=1.5,
                    help="drop background segments shorter than this")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    fps = float(plan["fps"])
    n_frames = int(plan["frames"])
    cuts = sorted((float(c[0]), float(c[1])) for c in plan["cuts"])
    anchors = [(float(a[0]), a[1], a[2]) for a in plan["anchors"]]

    frames = keep_frames(cuts, n_frames, fps)
    if not frames:
        raise SystemExit("cuts removed every frame")
    runs = to_runs(frames)

    kept_before = [0] * (n_frames + 1)
    seen = set(frames)
    running = 0
    for i in range(n_frames + 1):
        kept_before[i] = running
        if i in seen:
            running += 1

    def src_to_out(t: float) -> float:
        return kept_before[min(int(round(t * fps)), n_frames)] / fps

    src_dur, out_dur = n_frames / fps, len(frames) / fps
    print(f"源 {src_dur:.2f}s ({n_frames} 帧) → 成片 {out_dur:.2f}s ({len(frames)} 帧)，"
          f"剪掉 {src_dur - out_dur:.2f}s")
    print(f"保留片段 {len(runs)} 段 = {len(runs) - 1} 个剪切点\n")

    segments = []
    for i, (t_src, image, cue) in enumerate(anchors):
        start = src_to_out(t_src)
        end = src_to_out(anchors[i + 1][0]) if i + 1 < len(anchors) else out_dur
        if end - start < args.min_segment:
            print(f"  跳过过短分镜 [{start:.2f}-{end:.2f}] {cue}")
            continue
        img = image if "/" in image else f"ready/{image}"
        segments.append({"start": round(start, 2), "end": round(end, 2),
                         "image": img, "cue": cue})

    print("分镜（成片时间轴）:")
    for s in segments:
        print(f"  [{s['start']:6.2f} - {s['end']:6.2f}]  {Path(s['image']).name:34s} {s['cue']}")

    args.work.mkdir(parents=True, exist_ok=True)
    args.backgrounds.mkdir(parents=True, exist_ok=True)
    (args.work / "keep_frames.json").write_text(
        json.dumps({"fps": fps, "runs": runs}, indent=2), encoding="utf-8")
    (args.work / "audio_select.txt").write_text(
        "+".join(f"between(t,{a / fps:.5f},{(b + 1) / fps:.5f})" for a, b in runs),
        encoding="utf-8")
    (args.backgrounds / "storyboard_aligned.json").write_text(
        json.dumps({"segments": segments}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {args.work}/keep_frames.json, {args.work}/audio_select.txt, "
          f"{args.backgrounds}/storyboard_aligned.json")


if __name__ == "__main__":
    main()
