#!/usr/bin/env python3
"""
Audio Transcription Script using FunASR
Transcribes audio files to text using Alibaba's FunASR model
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

try:
    from funasr import AutoModel
except ImportError:
    print("Error: FunASR is not installed.", flush=True)
    print("Install: conda activate safe_claw && pip install funasr", flush=True)
    sys.exit(1)


def fmt_clock(total_seconds: float) -> str:
    total = max(0, int(total_seconds))
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def fmt_range(start_sec: float, end_sec: float) -> str:
    return f"{fmt_clock(start_sec)}–{fmt_clock(end_sec)}"


def load_model(model_name: str, offline: bool = False) -> AutoModel:
    print(f"Loading FunASR model: {model_name}", flush=True)
    if offline:
        print("  (offline mode: disable_update=True, using cached models only)", flush=True)
    print(
        "  First run may download models from ModelScope (~300MB); "
        "stdout can be silent for 1–3 minutes.",
        flush=True,
    )
    return AutoModel(
        model=model_name,
        vad_model="fsmn-vad",
        punc_model="ct-punc",
        disable_update=offline,
    )


def write_plain_output(path: Path, texts: list[str]) -> None:
    path.write_text("\n".join(texts), encoding="utf-8")
    print(f"Plain text saved to: {path}", flush=True)


def write_markdown_output(
    path: Path,
    texts: list[str],
    *,
    source: str | None,
    chunk_duration: int,
    total_duration_sec: float | None,
    model_name: str,
) -> None:
    char_count = sum(len(t) for t in texts)
    lines = [
        "---",
        f"date: {date.today().isoformat()}",
        f"model: funasr {model_name} + fsmn-vad + ct-punc",
        f"chunks: {len(texts)}",
        f"chunk_duration_sec: {chunk_duration}",
        f"characters: {char_count}",
    ]
    if source:
        lines.append(f"source: {source}")
    if total_duration_sec is not None:
        lines.append(f"duration_min: {round(total_duration_sec / 60)}")
    lines.extend(["---", "", "# 语音转写文字稿", ""])
    if source:
        lines.append(f"> 源文件：`{source}`")
    lines.append("")

    single_section = len(texts) == 1 and chunk_duration <= 0
    for i, text in enumerate(texts):
        if not single_section:
            start = i * chunk_duration
            end = (
                min((i + 1) * chunk_duration, total_duration_sec)
                if total_duration_sec is not None
                else (i + 1) * chunk_duration
            )
            lines.append(f"## [{fmt_range(start, end)}]")
            lines.append("")
        lines.append(text.strip())
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown saved to: {path}", flush=True)


def transcribe_audio(
    input_file: str,
    output_file: str | None = None,
    model_name: str = "paraformer-zh",
    offline: bool = False,
    markdown_file: str | None = None,
    source: str | None = None,
) -> str:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    model = load_model(model_name, offline=offline)

    print(f"Transcribing audio file: {input_file}", flush=True)
    res = model.generate(input=input_file)

    if res and len(res) > 0:
        text = res[0].get("text", "")
        print(f"Transcription completed ({len(text)} characters).", flush=True)

        if output_file:
            write_plain_output(Path(output_file), [text])
        if markdown_file:
            write_markdown_output(
                Path(markdown_file),
                [text],
                source=source or input_file,
                chunk_duration=0,
                total_duration_sec=None,
                model_name=model_name,
            )
        return text

    print("Warning: No transcription result returned", flush=True)
    return ""


def transcribe_chunks(
    input_dir: str,
    output_file: str,
    model_name: str = "paraformer-zh",
    offline: bool = False,
    chunk_duration: int = 300,
    total_duration_sec: float | None = None,
    markdown_file: str | None = None,
    source: str | None = None,
) -> str:
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    chunk_files = sorted(input_path.glob("*.wav"))
    if not chunk_files:
        raise FileNotFoundError(f"No WAV files found in {input_dir}")

    print(f"Found {len(chunk_files)} audio chunks", flush=True)

    model = load_model(model_name, offline=offline)

    all_texts: list[str] = []
    for i, chunk_file in enumerate(chunk_files, 1):
        print(f"Transcribing chunk {i}/{len(chunk_files)}: {chunk_file.name}", flush=True)
        res = model.generate(input=str(chunk_file))

        if res and len(res) > 0:
            text = res[0].get("text", "")
            all_texts.append(text)
            print(f"  ✓ Chunk {i} transcribed: {len(text)} characters", flush=True)
        else:
            print(f"  ✗ Chunk {i} failed to transcribe", flush=True)
            all_texts.append("")

    char_count = sum(len(t) for t in all_texts)
    print(f"\nTranscription completed. Total characters: {char_count}", flush=True)

    write_plain_output(Path(output_file), all_texts)
    if markdown_file:
        write_markdown_output(
            Path(markdown_file),
            all_texts,
            source=source,
            chunk_duration=chunk_duration,
            total_duration_sec=total_duration_sec,
            model_name=model_name,
        )

    return "\n".join(all_texts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio files using FunASR")
    parser.add_argument("--input", "-i", help="Input audio file path (single-file mode)")
    parser.add_argument(
        "--input-dir", "-d", help="Directory of audio chunks (chunk mode)"
    )
    parser.add_argument("--output", "-o", required=True, help="Output .txt path")
    parser.add_argument(
        "--markdown",
        help="Optional output .md path with YAML front matter and time sections",
    )
    parser.add_argument(
        "--model", "-m", default="paraformer-zh", help="FunASR model (default: paraformer-zh)"
    )
    parser.add_argument(
        "--chunk-duration",
        type=int,
        default=300,
        help="Chunk length in seconds for markdown timestamps (default: 300)",
    )
    parser.add_argument(
        "--total-duration",
        type=float,
        default=None,
        help="Total audio duration in seconds (for last chunk timestamp label)",
    )
    parser.add_argument(
        "--source",
        help="Original video/audio path for metadata (defaults to --input)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cached models only (disable_update=True); fails if models missing",
    )

    args = parser.parse_args()

    try:
        if args.input_dir:
            transcribe_chunks(
                input_dir=args.input_dir,
                output_file=args.output,
                model_name=args.model,
                offline=args.offline,
                chunk_duration=args.chunk_duration,
                total_duration_sec=args.total_duration,
                markdown_file=args.markdown,
                source=args.source,
            )
        elif args.input:
            transcribe_audio(
                input_file=args.input,
                output_file=args.output,
                model_name=args.model,
                offline=args.offline,
                markdown_file=args.markdown,
                source=args.source or args.input,
            )
        else:
            parser.error("Either --input or --input-dir must be specified")
    except Exception as e:
        print(f"Error during transcription: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
