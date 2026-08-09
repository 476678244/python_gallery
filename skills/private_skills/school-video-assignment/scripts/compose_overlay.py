#!/usr/bin/env python3
"""Matte the speaker out of a home recording and stand them in front of location stills.

    python compose_overlay.py --person speaker.mp4 \
        --storyboard backgrounds/storyboard_aligned.json \
        --keep-frames work/keep_frames.json \
        --output out/final.mp4

Needs RobustVideoMatting: clone the repo and drop the checkpoints next to it, then point
--rvm-repo / --rvm-ckpt at them (or set RVM_REPO / RVM_CKPT_DIR).

    git clone https://github.com/PeterL1n/RobustVideoMatting
    curl -LO https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth

Mattes are cached per (variant, downsample) so the slow part runs once and you can
iterate on framing, storyboard and cuts for free.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent

# Source SNR in a living room is often only ~15 dB, and matching a -16 LUFS target
# means ~20 dB of gain, so clean up before the make-up gain rather than after.
CLEANUP = (
    "highpass=f=90,"
    "afftdn=nr=12:nf=-45:tn=1,"
    "agate=threshold=0.010:ratio=3:attack=15:release=350:makeup=1,"
    "equalizer=f=3000:t=q:w=1.2:g=3,"
)


def pick_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def ffmpeg_raw_writer(path: Path, w: int, h: int, fps: float, pix_fmt: str = "bgr24"):
    return subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", pix_fmt, "-s", f"{w}x{h}", "-r", f"{fps:.4f}", "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18", str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def load_plate(path: Path, size: tuple[int, int]) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


class Storyboard:
    def __init__(self, path: Path, size: tuple[int, int], fade: float = 0.6):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.fade = fade
        self.segments = []
        for seg in data["segments"]:
            img = Path(seg["image"])
            if not img.is_absolute():
                img = path.parent / seg["image"]
            self.segments.append({"start": float(seg["start"]), "end": float(seg["end"]),
                                  "frame": load_plate(img, size)})
        if not self.segments:
            raise RuntimeError("empty storyboard")

    def frame_at(self, t: float) -> np.ndarray:
        segs = self.segments
        cur = 0
        for i, s in enumerate(segs):
            if t >= s["start"]:
                cur = i
        if cur + 1 < len(segs):
            boundary = segs[cur + 1]["start"]
            if boundary - self.fade <= t < boundary + self.fade:
                w = float(np.clip((t - boundary + self.fade) / (2 * self.fade), 0, 1))
                return np.clip(segs[cur]["frame"] * (1 - w) + segs[cur + 1]["frame"] * w,
                               0, 255).astype(np.uint8)
        return segs[cur]["frame"]


def soft_shadow(h, w, cx, cy, rx, ry, strength) -> np.ndarray:
    y, x = np.ogrid[:h, :w]
    m = ((x - cx) / max(rx, 1)) ** 2 + ((y - cy) / max(ry, 1)) ** 2
    a = np.clip(1.0 - m, 0, 1).astype(np.float32)
    return cv2.GaussianBlur(a, (0, 0), sigmaX=max(rx, ry) * 0.15) * strength


def largest_component_bbox(pha: np.ndarray, thresh: int = 40):
    mask = (pha > thresh).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return None
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh, _ = stats[idx]
    return int(x), int(y), int(x + bw - 1), int(y + bh - 1)


def estimate_stable_crop(pha_path: Path, stride: int = 2, pad: int = 80):
    """One crop box for the whole take, covering every gesture.

    Per-frame boxes make the speaker jitter and swim around the corner, so take the
    union over the clip and keep it fixed. The largest connected component avoids
    stray alpha speckles blowing the box out to the full frame.
    """
    cap = cv2.VideoCapture(str(pha_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {pha_path}")
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
    x0, y0, x1, y1 = w, h, 0, 0
    found = False
    i = 0
    while True:
        ok, pha = cap.read()
        if not ok:
            break
        if i % stride == 0:
            if pha.ndim == 3:
                pha = cv2.cvtColor(pha, cv2.COLOR_BGR2GRAY)
            box = largest_component_bbox(pha)
            if box:
                found = True
                x0, y0 = min(x0, box[0]), min(y0, box[1])
                x1, y1 = max(x1, box[2]), max(y1, box[3])
        i += 1
    cap.release()
    if not found:
        return 0, 0, w - 1, h - 1
    return max(0, x0 - pad), max(0, y0 - pad), min(w - 1, x1 + pad), min(h - 1, y1 + pad)


def refine_alpha(alpha: np.ndarray) -> np.ndarray:
    """Solidify motion-blurred limbs, then leave a ~1px feather.

    A waving arm comes back at alpha 0.3-0.6 and reads as see-through, which is the
    single most obvious tell that the background was replaced.
    """
    u8 = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    u8 = cv2.morphologyEx(u8, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
    a = np.clip((u8.astype(np.float32) / 255.0 - 0.06) / 0.54, 0, 1)
    u8 = cv2.dilate((a * 255).astype(np.uint8),
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    u8 = cv2.GaussianBlur(u8, (0, 0), sigmaX=0.9)
    return np.clip(u8.astype(np.float32) / 255.0, 0, 1)


def composite_frame(fgr, pha, bg, crop_box, height_frac, max_width_frac, side="left"):
    H, W = bg.shape[:2]
    if pha.ndim == 3:
        pha = pha[:, :, 0]
    alpha = refine_alpha(pha.astype(np.float32) / 255.0)

    x0, y0, x1, y1 = crop_box
    crop_bgr, crop_a = fgr[y0:y1 + 1, x0:x1 + 1], alpha[y0:y1 + 1, x0:x1 + 1]
    if crop_bgr.size == 0:
        return bg.copy()

    ch, cw = crop_bgr.shape[:2]
    max_w = max(1, int(round(W * max_width_frac)))
    scale = int(round(H * height_frac)) / max(ch, 1)
    if cw * scale > max_w:
        scale = max_w / max(cw, 1)
    rw, rh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))

    person = cv2.resize(crop_bgr, (rw, rh), interpolation=cv2.INTER_LINEAR)
    person_a = cv2.resize(crop_a, (rw, rh), interpolation=cv2.INTER_LINEAR)

    margin_x = max(8, int(round(W * 0.02)))
    ox = margin_x if side == "left" else max(0, W - margin_x - rw)
    # Flush to the bottom edge. The silhouette is already cut off by the source frame,
    # so any gap underneath turns that flat edge into a visible floating rectangle.
    oy = max(0, H - rh)
    rw = min(rw, W - ox)
    person, person_a = person[:, :rw], person_a[:, :rw]

    out = bg.astype(np.float32)
    sh = soft_shadow(H, W, ox + rw // 2, oy + int(rh * 0.75),
                     int(rw * 0.50), int(rh * 0.38), 0.22)
    for c in range(3):
        out[:, :, c] = out[:, :, c] * (1 - sh) + 20.0 * sh

    roi = out[oy:oy + rh, ox:ox + rw]
    p = person.astype(np.float32)
    # light wrap: bleed plate colour into the outer edge so the cutout stops looking pasted
    edge = np.clip(cv2.GaussianBlur(person_a, (0, 0), 4.0) - person_a, 0, 1)[..., None]
    p = p * (1 - edge * 0.55) + roi * (edge * 0.55)
    a = person_a[..., None]
    roi[:] = p * a + roi * (1 - a)
    return np.clip(out, 0, 255).astype(np.uint8)


def ensure_matting(person: Path, work: Path, device, downsample: float, variant: str,
                   repo: Path, ckpt_dir: Path):
    tag = f"{variant}_ds{downsample}"
    fgr_path, pha_path = work / f"fgr_{tag}.mp4", work / f"pha_{tag}.mp4"
    meta = work / f"meta_{tag}.txt"
    if fgr_path.exists() and pha_path.exists() and meta.exists():
        fps, w, h = meta.read_text().split()
        print(f"复用已缓存的抠像: {fgr_path.name}")
        return fgr_path, pha_path, float(fps), int(w), int(h)

    sys.path.insert(0, str(repo))
    from model import MattingNetwork  # noqa: E402

    work.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(person))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {person}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    ckpt = ckpt_dir / f"rvm_{variant}.pth"
    if not ckpt.exists():
        raise FileNotFoundError(ckpt)
    net = MattingNetwork(variant).eval().to(device)
    net.load_state_dict(torch.load(ckpt, map_location=device, weights_only=True))
    print(f"抠像中 variant={variant} downsample={downsample} frames={n}")

    fgr_ff = ffmpeg_raw_writer(fgr_path, w, h, fps, "bgr24")
    pha_ff = ffmpeg_raw_writer(pha_path, w, h, fps, "gray")
    rec = [None] * 4
    done = 0
    try:
        with torch.no_grad():
            while True:
                ok, bgr = cap.read()
                if not ok:
                    break
                src = (torch.from_numpy(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                       .float().div_(255.0).permute(2, 0, 1).unsqueeze(0).to(device))
                fgr, pha, *rec = net(src, *rec, downsample)
                fgr_np = fgr[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy()
                pha_np = pha[0, 0].clamp(0, 1).cpu().numpy()
                if fgr_np.shape[:2] != (h, w):
                    fgr_np = cv2.resize(fgr_np, (w, h), interpolation=cv2.INTER_LINEAR)
                    pha_np = cv2.resize(pha_np, (w, h), interpolation=cv2.INTER_LINEAR)
                fgr_ff.stdin.write(cv2.cvtColor((fgr_np * 255).astype(np.uint8),
                                                cv2.COLOR_RGB2BGR).tobytes())
                pha_ff.stdin.write((pha_np * 255).astype(np.uint8).tobytes())
                done += 1
                if done % 500 == 0:
                    print(f"  {done}/{n}")
    finally:
        cap.release()
        for ff in (fgr_ff, pha_ff):
            if ff.stdin and not ff.stdin.closed:
                ff.stdin.close()
            ff.wait()
    meta.write_text(f"{fps} {w} {h}\n")
    return fgr_path, pha_path, fps, w, h


def measure_loudness(src: Path, chain: str) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src), "-af",
         f"{chain}loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True)
    tail = proc.stderr[proc.stderr.rindex("{"):]
    return json.loads(tail[: tail.index("}") + 1])


def mux_audio(video: Path, person: Path, output: Path, audio_select: str | None) -> None:
    """Trim, clean, then two-pass loudnorm with a limiter.

    Single-pass loudnorm on a very quiet source overshoots and clips (peaks above
    0 dBFS); the measured second pass plus alimiter keeps true peak at -1.5 dB.
    """
    trim = f"aselect='{audio_select}',asetpts=N/SR/TB," if audio_select else ""
    chain = trim + CLEANUP
    m = measure_loudness(person, chain)
    print(f"响度第一遍: I={m['input_i']} TP={m['input_tp']} LRA={m['input_lra']}")
    second = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:"
              f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
              f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(person),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-af", f"{chain}{second},alimiter=limit=0.891:level=disabled,aresample=48000",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(output)],
        check=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--person", required=True, type=Path)
    p.add_argument("--storyboard", type=Path)
    p.add_argument("--background", type=Path, help="single still, instead of a storyboard")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--work", type=Path, default=Path("work"))
    p.add_argument("--keep-frames", type=Path)
    p.add_argument("--height-frac", type=float, default=0.6667)
    p.add_argument("--max-width-frac", type=float, default=0.42)
    p.add_argument("--side", choices=["left", "right"], default="left")
    p.add_argument("--downsample-ratio", type=float, default=0.4,
                   help="aim for width*ratio ~ 512, which is what RVM was trained on")
    p.add_argument("--variant", choices=["mobilenetv3", "resnet50"], default="resnet50")
    p.add_argument("--fade", type=float, default=0.6)
    p.add_argument("--rvm-repo", type=Path,
                   default=Path(os.environ.get("RVM_REPO", ROOT.parent / "RobustVideoMatting")))
    p.add_argument("--rvm-ckpt", type=Path,
                   default=Path(os.environ.get("RVM_CKPT_DIR", ROOT.parent / "models")))
    args = p.parse_args()

    if not args.storyboard and not args.background:
        raise SystemExit("need --storyboard or --background")

    device = pick_device()
    print(f"device={device}")
    fgr_path, pha_path, fps, W, H = ensure_matting(
        args.person, args.work, device, args.downsample_ratio, args.variant,
        args.rvm_repo, args.rvm_ckpt)

    crop_box = estimate_stable_crop(pha_path)
    print(f"固定裁切框 {crop_box}")

    story = Storyboard(args.storyboard, (W, H), args.fade) if args.storyboard else None
    plate = load_plate(args.background, (W, H)) if args.background else None

    keep, junctions, audio_select = None, set(), None
    if args.keep_frames:
        kf = json.loads(args.keep_frames.read_text())
        runs = [(int(a), int(b)) for a, b in kf["runs"]]
        keep = {i for a, b in runs for i in range(a, b + 1)}
        junctions = {a for a, _ in runs[1:]}
        sel = args.keep_frames.parent / "audio_select.txt"
        audio_select = sel.read_text().strip() if sel.exists() else None
        print(f"剪辑：保留 {len(keep)} 帧，{len(runs) - 1} 个剪切点")

    fgr_cap, pha_cap = cv2.VideoCapture(str(fgr_path)), cv2.VideoCapture(str(pha_path))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(".novoice.mp4")
    ff = ffmpeg_raw_writer(tmp, W, H, fps)

    DISSOLVE = [0.70, 0.45, 0.22]
    written, src_i, prev, left = 0, -1, None, 0
    try:
        while True:
            ok1, fgr = fgr_cap.read()
            ok2, pha = pha_cap.read()
            if not ok1 or not ok2:
                break
            src_i += 1
            if keep is not None and src_i not in keep:
                continue
            if src_i in junctions:
                left = len(DISSOLVE)
            if pha.ndim == 3:
                pha = cv2.cvtColor(pha, cv2.COLOR_BGR2GRAY)
            bg = story.frame_at(written / fps) if story else plate
            out = composite_frame(fgr, pha, bg, crop_box,
                                  args.height_frac, args.max_width_frac, args.side)
            # bleed the outgoing frame through for a few frames so cuts do not pop
            if left and prev is not None:
                w = DISSOLVE[len(DISSOLVE) - left]
                out = cv2.addWeighted(prev, w, out, 1 - w, 0)
                left -= 1
            prev = out
            ff.stdin.write(out.tobytes())
            written += 1
            if written % 500 == 0:
                print(f"  合成 {written}")
    finally:
        fgr_cap.release()
        pha_cap.release()
        if ff.stdin and not ff.stdin.closed:
            ff.stdin.close()
        ff.wait()

    print(f"合成 {written} 帧，混音中…")
    mux_audio(tmp, args.person, args.output, audio_select)
    tmp.unlink(missing_ok=True)
    print(f"done -> {args.output}")


if __name__ == "__main__":
    main()
