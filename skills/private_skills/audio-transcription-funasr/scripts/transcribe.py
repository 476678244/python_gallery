#!/usr/bin/env python3
"""
Audio Transcription Script using FunASR
Transcribes audio files to text using Alibaba's FunASR model
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from funasr import AutoModel
except ImportError:
    print("Error: FunASR is not installed.")
    print("Install it using: pip install funasr")
    sys.exit(1)


def transcribe_audio(input_file, output_file=None, model_name="paraformer-zh", language="zh"):
    """
    Transcribe audio file to text using FunASR
    
    Args:
        input_file: Path to input audio file
        output_file: Path to output text file (optional)
        model_name: FunASR model name (default: paraformer-zh)
        language: Language code (default: zh for Chinese)
    
    Returns:
        Transcribed text
    """
    # Check if input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    print(f"Loading FunASR model: {model_name}")
    model = AutoModel(
        model=model_name,
        vad_model="fsmn-vad",
        punc_model="ct-punc",
        # disable_update=True  # Uncomment to use cached models
    )
    
    print(f"Transcribing audio file: {input_file}")
    res = model.generate(input=input_file)
    
    if res and len(res) > 0:
        text = res[0].get("text", "")
        print(f"Transcription completed.")
        print(f"Text: {text}")
        
        # Save to file if output path is provided
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Transcription saved to: {output_file}")
        
        return text
    else:
        print("Warning: No transcription result returned")
        return ""


def transcribe_chunks(input_dir, output_file, model_name="paraformer-zh", language="zh"):
    """
    Transcribe multiple audio chunks in a directory and merge results
    
    Args:
        input_dir: Directory containing audio chunk files
        output_file: Path to output merged text file
        model_name: FunASR model name (default: paraformer-zh)
        language: Language code (default: zh for Chinese)
    
    Returns:
        Merged transcribed text
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Find all chunk files (sorted by name)
    chunk_files = sorted(input_path.glob("*.wav"))
    if not chunk_files:
        raise FileNotFoundError(f"No WAV files found in {input_dir}")
    
    print(f"Found {len(chunk_files)} audio chunks")
    
    # Load model once
    print(f"Loading FunASR model: {model_name}")
    model = AutoModel(
        model=model_name,
        vad_model="fsmn-vad",
        punc_model="ct-punc",
        # disable_update=True  # Uncomment to use cached models
    )
    
    # Transcribe each chunk
    all_texts = []
    for i, chunk_file in enumerate(chunk_files, 1):
        print(f"Transcribing chunk {i}/{len(chunk_files)}: {chunk_file.name}")
        res = model.generate(input=str(chunk_file))
        
        if res and len(res) > 0:
            text = res[0].get("text", "")
            all_texts.append(text)
            print(f"  ✓ Chunk {i} transcribed: {len(text)} characters")
        else:
            print(f"  ✗ Chunk {i} failed to transcribe")
            all_texts.append("")  # Keep order even if failed
    
    # Merge all texts
    merged_text = "\n".join(all_texts)
    print(f"\nTranscription completed. Total characters: {len(merged_text)}")
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(merged_text)
    print(f"Merged transcription saved to: {output_file}")
    
    return merged_text


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using FunASR"
    )
    parser.add_argument(
        "--input", "-i",
        help="Input audio file path (for single file mode)"
    )
    parser.add_argument(
        "--input-dir", "-d",
        help="Input directory containing audio chunks (for chunk mode)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output text file path"
    )
    parser.add_argument(
        "--model", "-m",
        default="paraformer-zh",
        help="FunASR model name (default: paraformer-zh)"
    )
    parser.add_argument(
        "--language", "-l",
        default="zh",
        help="Language code (default: zh for Chinese)"
    )
    
    args = parser.parse_args()
    
    try:
        # Determine mode: single file or chunks
        if args.input_dir:
            # Chunk mode
            transcribe_chunks(
                input_dir=args.input_dir,
                output_file=args.output,
                model_name=args.model,
                language=args.language
            )
        elif args.input:
            # Single file mode
            transcribe_audio(
                input_file=args.input,
                output_file=args.output,
                model_name=args.model,
                language=args.language
            )
        else:
            parser.error("Either --input or --input-dir must be specified")
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
