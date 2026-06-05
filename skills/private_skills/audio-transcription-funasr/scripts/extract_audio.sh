#!/bin/bash

# Audio Extraction Script
# Extracts audio from video/audio files using FFmpeg

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: FFmpeg is not installed."
    echo "Install it using:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
    exit 1
fi

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_file> <output_file> [optional_ffmpeg_args]"
    echo "Example: $0 input_video.mp4 output_audio.wav"
    echo "Example: $0 input_video.mp4 output_audio.mp3 -b:a 192k"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"
shift 2
FFMPEG_ARGS="$@"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    exit 1
fi

# Extract audio
echo "Extracting audio from '$INPUT_FILE' to '$OUTPUT_FILE'..."

if [ -z "$FFMPEG_ARGS" ]; then
    ffmpeg -i "$INPUT_FILE" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$OUTPUT_FILE" -y
else
    ffmpeg -i "$INPUT_FILE" -vn $FFMPEG_ARGS "$OUTPUT_FILE" -y
fi

# Check if extraction was successful
if [ $? -eq 0 ]; then
    echo "Audio extraction completed successfully."
    echo "Output file: $OUTPUT_FILE"
else
    echo "Error: Audio extraction failed."
    exit 1
fi
