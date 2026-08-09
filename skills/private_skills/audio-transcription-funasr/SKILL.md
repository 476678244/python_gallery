---
name: audio-transcription-funasr
description: Transcribe audio and video files to text using Alibaba's FunASR model. Extract speech from MP4, MP3, WAV files and convert to text transcripts. Prefer over Whisper when HuggingFace model download fails (proxy/network).
category: text
tags:
  - transcription
  - audio
  - video
  - speech
  - voice
  - funasr
  - speech-to-text
  - subtitle
  - extract-text
aliases:
  - transcribe
  - extract-audio
  - speech-to-text
  - video-to-text
  - audio-transcription
  - transcribe-video
  - extract-speech
argument_hint: "[video_file_or_audio_file]"
user_invocable: true
auto_trigger: false
---

# Audio Transcription with FunASR

## Overview

Transcribe Chinese (and other) speech using **Alibaba FunASR** (`paraformer-zh` + VAD + punctuation).

**When to use this skill instead of Whisper/faster-whisper:**

| Issue with Whisper | FunASR advantage |
|--------------------|------------------|
| HuggingFace `large-v3` download fails (`ProxyError`, token refresh) | Models from **ModelScope**; works in typical CN network |
| 90+ min audio OOM or very slow single pass | Built-in **chunk pipeline** (5 min slices) |
| No punctuation in raw output | `ct-punc` restores Chinese punctuation |

Verified: **101 min** screen-recording live stream → **21 chunks** → **~10 min** transcribe on Apple Silicon CPU (`safe_claw` env).

## Requirements

- Python 3.8+ with `funasr` (**use conda env `safe_claw`** on this machine)
- FFmpeg + ffprobe (`brew install ffmpeg`)

### Preflight

```bash
conda run -n safe_claw python -c "from funasr import AutoModel; print('ok')"
ffmpeg -version | head -1
```

Install if missing:

```bash
conda activate safe_claw && pip install funasr
```

## Quick start (recommended)

One command — extract, auto-chunk if >30 min, write `.txt` + `.md`:

```bash
SKILL_PATH="/path/to/audio-transcription-funasr"
bash "$SKILL_PATH/scripts/run_pipeline.sh" \
  "/path/to/video.mp4" \
  "/path/to/output_dir" \
  "2026-06-28-live"
```

Outputs:

- `{output_dir}/2026-06-28-live-transcript.txt` — plain text, one paragraph per chunk
- `{output_dir}/2026-06-28-live-transcript.md` — YAML + `## [HH:MM:SS–HH:MM:SS]` sections
- `{output_dir}/_2026-06-28-live.wav` — extracted 16 kHz mono (reused if newer than source)
- `{output_dir}/_chunks-2026-06-28-live/` — temp chunks (safe to delete after success)
- `{output_dir}/_2026-06-28-live-transcribe.log` — full run log

Env overrides:

- `CONDA_ENV=safe_claw` — conda environment
- `CHUNK_THRESHOLD_SEC=1800` — auto-chunk above 30 min (default)
- `CHUNK_DURATION=300` — chunk size in seconds (default 5 min)

## Manual steps

### Step 1: Extract audio from video

Skip if a 16 kHz mono WAV already exists and is newer than the source file.

```bash
ffmpeg -y -i "$INPUT_FILE" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$TEMP_AUDIO_FILE"
```

Or use `scripts/extract_audio.sh`.

### Step 2: Split long audio (> ~30 min)

```bash
conda run -n safe_claw python "$SKILL_PATH/scripts/split_audio.py" \
  --input "$TEMP_AUDIO_FILE" \
  --output-dir "$CHUNK_DIR" \
  --chunk-duration 300
```

### Step 3: Transcribe

**Chunk mode** (long files):

```bash
conda run -n safe_claw python "$SKILL_PATH/scripts/transcribe.py" \
  --input-dir "$CHUNK_DIR" \
  --output "$OUTPUT.txt" \
  --markdown "$OUTPUT.md" \
  --chunk-duration 300 \
  --total-duration "$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_AUDIO_FILE")" \
  --source "$INPUT_FILE" \
  2>&1 | tee "$LOG_FILE"
```

**Single file** (short audio, < ~30 min):

```bash
conda run -n safe_claw python "$SKILL_PATH/scripts/transcribe.py" \
  --input "$TEMP_AUDIO_FILE" \
  --output "$OUTPUT.txt" \
  --markdown "$OUTPUT.md" \
  --source "$INPUT_FILE"
```

### Variable substitution

| Variable | Meaning |
|----------|---------|
| `$INPUT_FILE` | Source video/audio |
| `$TEMP_AUDIO_FILE` | Extracted WAV (e.g. `_basename.wav`) |
| `$CHUNK_DIR` | Chunk folder (e.g. `_chunks-basename/`) |
| `$OUTPUT.txt` / `$OUTPUT.md` | Transcript outputs |
| `$SKILL_PATH` | This skill directory |

## Troubleshooting

### 1. Whisper / faster-whisper fails on model download

```
ConnectionError: ProxyError ... huggingface.co ... faster-whisper-large-v3
```

→ **Use this FunASR skill.** Do not retry HF download unless proxy is fixed.

### 2. No stdout for 1–3 minutes after "Loading FunASR model"

Normal on **first run**: `paraformer-zh`, `fsmn-vad`, `ct-punc` download from ModelScope (~300 MB total). Use `tee` to a log file and run in background for long jobs.

### 3. Long video (> 1 hour) without chunking

Single-pass `model.generate()` on 100+ min WAV may OOM or hang. Always **split first** or use `run_pipeline.sh` (auto-chunks above 30 min).

### 4. Re-run without re-extracting audio

If `_audio-*.wav` exists and is newer than the MP4, `run_pipeline.sh` skips ffmpeg. Delete the WAV to force re-extract.

### 5. Offline / air-gapped

After models are cached once:

```bash
python transcribe.py ... --offline
```

Uses `disable_update=True`; fails if cache is empty.

### 6. Background job appears stuck

Check log file and output directory size. Chunk transcription prints `Transcribing chunk N/M` once model is loaded.

## Model information

See `references/models.md`.

## Supported formats

WAV, MP3, FLAC, OGG, M4A (via ffmpeg extract → 16 kHz mono WAV).

## Notes

- Quality depends on audio clarity; screen recordings with Zoom/chat noise are usually fine for Mandarin speech.
- Default stack: `paraformer-zh` + `fsmn-vad` + `ct-punc`.
- After success, delete `_chunks-*` and `_*.wav` to reclaim disk (~200–400 MB for 100 min sources).

## Downstream: 学校视频作业

需要**时间戳**（剪掉卡壳重录、把配图切换点对准讲词）时，用 `school-video-assignment`，
它的 `scripts/transcribe_timestamps.py` 保留句级与字级 timestamp。本 skill 产出的是通顺
正文，不带时间轴。

## Downstream: 南添直播校对与笔记

FunASR 产出的是 **ASR 原料**（含同音误识别）。写入 wiki 笔记前，必须经校对 skill：

```
raw/nantian_live_text/*-transcript.md
  → nantian-live-transcript-refactor（词表 + Agent 人工 pass）
  → assets/sources/weekly_live_notes/refactored_text_scripts/*-refactored.md
  → assets/sources/weekly_live_notes/*-live-notes.md
```

- 校对 skill：`<obsidian_wiki>/.cursor/skills/nantian-live-transcript-refactor/SKILL.md`
- 笔记 SOP：`assets/sources/weekly_live_notes/Agents.md`

**不要**跳过校对直接从 ASR 写重点笔记（101/贝森特/沃什/见好就收等会系统性出错）。

