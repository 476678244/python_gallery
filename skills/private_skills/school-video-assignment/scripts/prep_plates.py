#!/usr/bin/env python3
"""Normalise background stills into 1280x720 plates and start an attribution file.

    python prep_plates.py backgrounds/sources backgrounds/ready --sources-md backgrounds/SOURCES.md

Phone screenshots and web images arrive at every aspect ratio; anything not exactly
16:9 is centre-cropped after scaling to cover, so no letterbox bars reach the composite.
White page margins around screenshots are trimmed first.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".JPG", ".JPEG", ".PNG"}


def trim_flat_border(img: np.ndarray, tol: int = 6) -> np.ndarray:
    """Drop uniform (usually white) margins left by screenshots."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    row_var = gray.reshape(h, -1).std(axis=1)
    col_var = gray.reshape(h, w).std(axis=0)
    rows = np.where(row_var > tol)[0]
    cols = np.where(col_var > tol)[0]
    if rows.size < 10 or cols.size < 10:
        return img
    return img[rows.min(): rows.max() + 1, cols.min(): cols.max() + 1]


def cover_crop(img: np.ndarray, w: int, h: int) -> np.ndarray:
    ih, iw = img.shape[:2]
    scale = max(w / iw, h / ih)
    resized = cv2.resize(img, (int(round(iw * scale)), int(round(ih * scale))),
                         interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    rh, rw = resized.shape[:2]
    # bias the crop upward: interiors and buildings have their subject above centre
    y0 = max(0, int((rh - h) * 0.4))
    x0 = max(0, (rw - w) // 2)
    return resized[y0: y0 + h, x0: x0 + w]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--no-trim", action="store_true")
    ap.add_argument("--sources-md", type=Path, help="write an attribution scaffold")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in args.src_dir.iterdir() if p.suffix in EXTS)
    if not files:
        raise SystemExit(f"no images in {args.src_dir}")

    rows = []
    for i, src in enumerate(files, 1):
        img = cv2.imread(str(src), cv2.IMREAD_COLOR)
        if img is None:
            print(f"  skip (unreadable) {src.name}")
            continue
        before = img.shape[:2]
        if not args.no_trim:
            img = trim_flat_border(img)
        plate = cover_crop(img, args.width, args.height)
        name = f"{i:02d}_{src.stem[:40].replace(' ', '_')}.jpg"
        cv2.imwrite(str(args.out_dir / name), plate, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"  {src.name}  {before[1]}x{before[0]} -> {name}")
        rows.append((name, src.name))

    if args.sources_md:
        lines = [
            "# 配图来源",
            "",
            "学校作业要能说明素材出处。请把每张图的来源补完整；自己拍的写「本人拍摄」。",
            "",
            "| 成片用图 | 原始文件 | 来源 / 链接 | 许可 |",
            "|---|---|---|---|",
        ]
        lines += [f"| `{a}` | `{b}` |  |  |" for a, b in rows]
        args.sources_md.parent.mkdir(parents=True, exist_ok=True)
        args.sources_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n-> {args.sources_md}")

    print(f"\n{len(rows)} 张底板 -> {args.out_dir}")


if __name__ == "__main__":
    main()
