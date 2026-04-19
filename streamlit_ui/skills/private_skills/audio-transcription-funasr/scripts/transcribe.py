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


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using FunASR"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input audio file path"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output text file path (optional)"
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
        transcribe_audio(
            input_file=args.input,
            output_file=args.output,
            model_name=args.model,
            language=args.language
        )
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
