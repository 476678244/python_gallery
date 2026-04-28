---
name: audio-transcription-funasr
description: Transcribe audio and video files to text using Alibaba's FunASR model. Extract speech from MP4, MP3, WAV files and convert to text transcripts.
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
This skill provides audio transcription capabilities using Alibaba's FunASR (Fundamental Automatic Speech Recognition) model.

## Features
- Extract audio from video files
- Transcribe audio to text using FunASR
- Support for multiple audio formats
- High accuracy speech recognition

## Requirements
- Python 3.8+
- FunASR library
- FFmpeg (for audio extraction)

## Installation
```bash
pip install funasr
```

Install FFmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`

## Usage

### Execution Steps

To transcribe a video file, execute the following commands:

**Step 1: Extract audio from video**
```bash:execute
ffmpeg -y -i $INPUT_FILE -vn -acodec pcm_s16le -ar 16000 -ac 1 $TEMP_AUDIO_FILE
```

**Step 2: Split audio into chunks (for large files)**
```bash:execute
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python $SKILL_PATH/scripts/split_audio.py --input $TEMP_AUDIO_FILE --output-dir $CHUNK_DIR --chunk-duration 300
```

**Step 3: Transcribe audio chunks and merge results**
```bash:execute
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python $SKILL_PATH/scripts/transcribe.py --input-dir $CHUNK_DIR --output $OUTPUT_FILE
```

### Variable Substitution

- `$INPUT_FILE` - Path to the input video/audio file (provided as argument)
- `$TEMP_AUDIO_FILE` - Temporary path for extracted audio (derived from `$INPUT_FILE` with `.wav` extension, e.g., `${INPUT_FILE%.*}.wav` or `${INPUT_FILE}_temp.wav`)
- `$CHUNK_DIR` - Directory for audio chunks (derived from `$INPUT_FILE` with `_chunks` suffix, e.g., `${INPUT_FILE%.*}_chunks`)
- `$OUTPUT_FILE` - Path for the output transcription file (default: $INPUT_FILE_transcription.txt)
- `$SKILL_PATH` - Path to the skill directory

### Chunking Configuration

The audio splitting uses the following parameters:
- **Chunk duration**: 300 seconds (5 minutes) by default
- **Sample rate**: 16000 Hz (optimized for FunASR)
- **Channels**: 1 (mono)

You can adjust the chunk duration in Step 2 by changing `--chunk-duration` (in seconds). Smaller chunks reduce memory usage but increase processing time.

### Examples

**Basic usage (small files, no chunking):**
```bash
# For video file (tested with MP4)
ffmpeg -y -i "$INPUT_FILE" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$TEMP_AUDIO_FILE"
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/transcribe.py" --input "$TEMP_AUDIO_FILE" --output "$OUTPUT_FILE"

# For audio file (skip extraction)
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/transcribe.py" --input "$INPUT_FILE" --output "$OUTPUT_FILE"
```

**Advanced usage (large files with chunking):**
```bash
# Extract audio
ffmpeg -y -i "$INPUT_FILE" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$TEMP_AUDIO_FILE"

# Split into 5-minute chunks
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/split_audio.py" --input "$TEMP_AUDIO_FILE" --output-dir "$CHUNK_DIR" --chunk-duration 300

# Transcribe all chunks and merge
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/transcribe.py" --input-dir "$CHUNK_DIR" --output "$OUTPUT_FILE"
```

## Model Information
See `references/models.md` for detailed information about available FunASR models.

## Supported Audio Formats
- WAV
- MP3
- FLAC
- OGG
- M4A

## Notes
- The transcription quality depends on the audio quality and language
- FunASR supports multiple languages including Chinese and English
- For best results, use WAV format with 16kHz sample rate
