#!/usr/bin/env python3
"""Check a finished assignment against the submission spec and for common defects.

    python verify_output.py out/final.mp4 --max-minutes 5 --max-mb 200 --contact-sheet /tmp/grid.jpg

Catches the things that are invisible until someone else plays the file: clipped audio,
a hissy noise floor, a video that is one second over the limit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def audio_stat(path: Path, pattern: str, extra: list[str] | None = None) -> list[str]:
    cmd = ["ffmpeg", "-hide_banner"]
    cmd += extra or []
    cmd += ["-i", str(path), "-af", "volumedetect" if pattern != "peak" else "astats=metadata=1",
            "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    return err.splitlines()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--max-minutes", type=float, default=5.0)
    ap.add_argument("--max-mb", type=float, default=200.0)
    ap.add_argument("--contact-sheet", type=Path)
    args = ap.parse_args()

    info = ffprobe(args.video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / 1e6

    problems: list[str] = []
    print(f"文件      {args.video.name}")
    print(f"容器      {info['format']['format_name']}  /  {v['codec_name']}"
          + (f" + {a['codec_name']}" if a else "  ⚠️ 无音轨"))
    print(f"分辨率    {v['width']}x{v['height']}  {eval(v['r_frame_rate']):.0f}fps")
    print(f"时长      {dur:.1f}s ({int(dur // 60)}:{int(dur % 60):02d})"
          f"   上限 {args.max_minutes:.0f}:00")
    print(f"体积      {size_mb:.1f} MB   上限 {args.max_mb:.0f} MB")

    if dur > args.max_minutes * 60:
        problems.append(f"超时长 {dur - args.max_minutes * 60:.1f}s")
    if size_mb > args.max_mb:
        problems.append(f"超体积 {size_mb - args.max_mb:.1f} MB")
    if a is None:
        problems.append("没有音轨")
    if "mp4" not in info["format"]["format_name"]:
        problems.append("不是 MP4 容器")

    if a:
        vol = "\n".join(audio_stat(args.video, "vol"))
        mean = re.search(r"mean_volume: ([-\d.]+) dB", vol)
        peak = re.search(r"max_volume: ([-\d.]+) dB", vol)
        print(f"\n平均音量  {mean.group(1) if mean else '?'} dB   （宜在 -20 ~ -14）")
        print(f"峰值      {peak.group(1) if peak else '?'} dB   （必须 < 0，否则爆音）")
        if peak and float(peak.group(1)) >= -0.1:
            problems.append(f"音频削波，峰值 {peak.group(1)} dB —— 用两遍 loudnorm + alimiter 重做")
        if mean and float(mean.group(1)) < -24:
            problems.append(f"整体偏轻 {mean.group(1)} dB，评委可能听不清")

        sil = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(args.video), "-af",
             "silencedetect=noise=-35dB:d=0.8", "-f", "null", "-"],
            capture_output=True, text=True).stderr
        gaps = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", sil)]
        if gaps:
            print(f"停顿      {len(gaps)} 段 > 0.8s，共 {sum(gaps):.1f}s "
                  f"（占 {sum(gaps)/dur:.0%}），最长 {max(gaps):.1f}s")
            if sum(gaps) / dur > 0.2:
                problems.append(f"空白占了 {sum(gaps)/dur:.0%}，节奏拖沓，考虑压缩停顿")
        else:
            print("停顿      无 > 0.8s 的静音段")

    if args.contact_sheet:
        times = [dur * f for f in (0.05, 0.25, 0.45, 0.65, 0.85, 0.97)]
        tiles = []
        for i, t in enumerate(times):
            tile = Path(f"/tmp/_vq_{i}.jpg")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t}",
                            "-i", str(args.video), "-frames:v", "1", str(tile)], check=True)
            tiles.append(tile)
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for t in tiles:
            cmd += ["-i", str(t)]
        cmd += ["-filter_complex",
                "[0][1][2]hstack=3[a];[3][4][5]hstack=3[b];[a][b]vstack,scale=1440:-2",
                str(args.contact_sheet)]
        subprocess.run(cmd, check=True)
        print(f"\n抽帧图    {args.contact_sheet}（务必看一眼：抠像边缘、人物位置、配图是否对得上讲词）")

    print()
    if problems:
        print("需要处理:")
        for p in problems:
            print(f"  ✗ {p}")
        raise SystemExit(1)
    print("✅ 规格与音频检查通过")


if __name__ == "__main__":
    main()
