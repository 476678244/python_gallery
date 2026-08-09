#!/usr/bin/env bash
# End-to-end: video/audio → extract → (optional split) → transcribe → txt + md
#
# Usage:
#   run_pipeline.sh <input_file> <output_dir> [basename]
#
# Example:
#   run_pipeline.sh ~/Downloads/live.mp4 ./raw/nantian_live_text 2026-06-28-live

set -euo pipefail

INPUT="${1:?Usage: run_pipeline.sh <input_file> <output_dir> [basename]}"
OUT_DIR="${2:?Usage: run_pipeline.sh <input_file> <output_dir> [basename]}"
BASENAME="${3:-$(basename "${INPUT%.*}")}"

SKILL_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CONDA_ENV="${CONDA_ENV:-safe_claw}"
CHUNK_THRESHOLD_SEC="${CHUNK_THRESHOLD_SEC:-1800}"   # 30 min → auto-chunk
CHUNK_DURATION="${CHUNK_DURATION:-300}"             # 5 min per chunk

AUDIO="${OUT_DIR}/_${BASENAME}.wav"
CHUNK_DIR="${OUT_DIR}/_chunks-${BASENAME}"
TXT_OUT="${OUT_DIR}/${BASENAME}-transcript.txt"
MD_OUT="${OUT_DIR}/${BASENAME}-transcript.md"
LOG="${OUT_DIR}/_${BASENAME}-transcribe.log"

mkdir -p "$OUT_DIR"

if ! command -v ffmpeg &>/dev/null || ! command -v ffprobe &>/dev/null; then
  echo "Error: ffmpeg/ffprobe not found. macOS: brew install ffmpeg"
  exit 1
fi

if ! conda run -n "$CONDA_ENV" python -c "from funasr import AutoModel" 2>/dev/null; then
  echo "Error: funasr not installed in conda env '$CONDA_ENV'."
  echo "  conda activate $CONDA_ENV && pip install funasr"
  exit 1
fi

# Step 1: extract audio (skip if wav already exists and is newer than source)
need_extract=1
if [[ -f "$AUDIO" ]]; then
  if [[ "$AUDIO" -nt "$INPUT" ]]; then
    echo "Reusing existing audio: $AUDIO"
    need_extract=0
  fi
fi

if [[ "$need_extract" -eq 1 ]]; then
  echo "Extracting audio → $AUDIO"
  ffmpeg -y -i "$INPUT" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$AUDIO"
fi

DURATION="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")"
echo "Audio duration: ${DURATION}s ($(python3 -c "print(round(float('${DURATION}')/60, 1))") min)"

# Step 2: chunk if long
USE_CHUNKS=0
if python3 -c "import sys; sys.exit(0 if float('${DURATION}') > ${CHUNK_THRESHOLD_SEC} else 1)"; then
  USE_CHUNKS=1
  echo "Long audio (>${CHUNK_THRESHOLD_SEC}s): splitting into ${CHUNK_DURATION}s chunks"
  conda run -n "$CONDA_ENV" python "$SKILL_PATH/scripts/split_audio.py" \
    --input "$AUDIO" \
    --output-dir "$CHUNK_DIR" \
    --chunk-duration "$CHUNK_DURATION"
fi

# Step 3: transcribe (log to file; model download may be silent for minutes)
echo "Transcribing → $TXT_OUT (+ $MD_OUT)"
echo "Log: $LOG"

if [[ "$USE_CHUNKS" -eq 1 ]]; then
  conda run -n "$CONDA_ENV" python "$SKILL_PATH/scripts/transcribe.py" \
    --input-dir "$CHUNK_DIR" \
    --output "$TXT_OUT" \
    --markdown "$MD_OUT" \
    --chunk-duration "$CHUNK_DURATION" \
    --total-duration "$DURATION" \
    --source "$INPUT" \
    2>&1 | tee "$LOG"
else
  conda run -n "$CONDA_ENV" python "$SKILL_PATH/scripts/transcribe.py" \
    --input "$AUDIO" \
    --output "$TXT_OUT" \
    --markdown "$MD_OUT" \
    --source "$INPUT" \
    2>&1 | tee "$LOG"
fi

echo ""
echo "Done."
echo "  txt: $TXT_OUT"
echo "  md:  $MD_OUT"
echo "  Optional cleanup: rm -rf '$CHUNK_DIR' '$AUDIO'  (saves ~200MB+ for long files)"
