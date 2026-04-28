#!/usr/bin/env python3
"""
Audio Splitting Script
Splits large audio files into smaller chunks for processing
"""

import argparse
import os
import subprocess
from pathlib import Path


def get_audio_duration(input_file):
    """Get audio duration in seconds using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return float(result.stdout.strip())
    return None


def split_audio(input_file, output_dir, chunk_duration=300, sample_rate=16000):
    """
    Split audio file into chunks
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory to save chunks
        chunk_duration: Duration of each chunk in seconds (default: 300 = 5 minutes)
        sample_rate: Sample rate for output (default: 16000)
    
    Returns:
        List of chunk file paths
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get total duration
    duration = get_audio_duration(input_file)
    if duration is None:
        raise ValueError(f"Could not get duration for {input_file}")
    
    print(f"Audio duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    
    # Calculate number of chunks
    num_chunks = int(duration / chunk_duration) + (1 if duration % chunk_duration > 0 else 0)
    print(f"Splitting into {num_chunks} chunks of {chunk_duration} seconds each")
    
    chunk_files = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = output_path / f"{input_path.stem}_chunk_{i+1:03d}.wav"
        
        cmd = [
            'ffmpeg',
            '-y',
            '-i', str(input_file),
            '-ss', str(start_time),
            '-t', str(chunk_duration),
            '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate),
            '-ac', '1',
            str(output_file)
        ]
        
        print(f"Creating chunk {i+1}/{num_chunks}: {output_file.name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            chunk_files.append(str(output_file))
            print(f"  ✓ Chunk created successfully")
        else:
            print(f"  ✗ Failed to create chunk: {result.stderr}")
    
    return chunk_files


def main():
    parser = argparse.ArgumentParser(
        description="Split audio files into chunks"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input audio file path"
    )
    parser.add_argument(
        "--output-dir", "-o",
        required=True,
        help="Output directory for chunks"
    )
    parser.add_argument(
        "--chunk-duration", "-d",
        type=int,
        default=300,
        help="Chunk duration in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--sample-rate", "-r",
        type=int,
        default=16000,
        help="Sample rate for output (default: 16000)"
    )
    
    args = parser.parse_args()
    
    try:
        chunks = split_audio(
            input_file=args.input,
            output_dir=args.output_dir,
            chunk_duration=args.chunk_duration,
            sample_rate=args.sample_rate
        )
        print(f"\n✓ Successfully created {len(chunks)} chunks")
        print(f"Chunk files:")
        for chunk in chunks:
            print(f"  - {chunk}")
    except Exception as e:
        print(f"Error during audio splitting: {e}")
        exit(1)


if __name__ == "__main__":
    main()
