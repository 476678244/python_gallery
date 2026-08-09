#!/usr/bin/env python3
"""Transcribe a recording with FunASR, keeping sentence- and character-level timestamps.

The sibling skill `audio-transcription-funasr` produces readable prose; this one keeps
the timing data that the edit planner needs.

    python transcribe_timestamps.py INPUT.mp4 OUT_DIR [--tag raw|denoised]

Writes OUT_DIR/asr_{tag}.json and OUT_DIR/asr_{tag}.txt
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MODELSCOPE_CACHE", os.path.expanduser("~/.cache/modelscope"))
for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"):
    os.environ.pop(var, None)

# A local file named inspect.py / typing.py etc. next to this script will shadow the
# stdlib and break funasr's import walk. Keep the script directory off sys.path.
sys.path[:] = [p for p in sys.path if Path(p).resolve() != Path(__file__).resolve().parent]

DENOISE = (
    "highpass=f=90,"
    "afftdn=nr=12:nf=-45:tn=1,"
    "agate=threshold=0.010:ratio=3:attack=15:release=350:makeup=1,"
    "equalizer=f=3000:t=q:w=1.2:g=3"
)


def extract_wav(src: Path, dst: Path, denoise: bool) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000"]
    if denoise:
        cmd += ["-af", DENOISE]
    cmd += ["-c:a", "pcm_s16le", str(dst)]
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--tag", default="raw", help="raw | denoised")
    ap.add_argument("--denoise", action="store_true", help="apply the cleanup chain before ASR")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    wav = args.out_dir / f"_speech16k_{args.tag}.wav"
    extract_wav(args.input, wav, args.denoise)

    from funasr import AutoModel  # imported late so ffmpeg errors surface first

    model = AutoModel(
        model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        punc_model="iic/punc_ct-transformer_cn-en-common-vocab471067-large",
        device="cpu",
        disable_update=True,
    )
    res = model.generate(input=str(wav), batch_size_s=300, sentence_timestamp=True)

    json_path = args.out_dir / f"asr_{args.tag}.json"
    json_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    item = res[0]
    lines = [item.get("text", ""), "", "=== SENTENCES ==="]
    for s in item.get("sentence_info", []):
        lines.append(f"[{s['start']/1000:7.2f} - {s['end']/1000:7.2f}] {s['text']}")
    txt = "\n".join(lines)
    (args.out_dir / f"asr_{args.tag}.txt").write_text(txt, encoding="utf-8")
    print(txt)
    print(f"\n-> {json_path}")


if __name__ == "__main__":
    main()
