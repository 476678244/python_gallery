#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import argparse
from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        sys.exit(1)
    return text

def clean_text(text):
    """Clean and format the extracted text."""
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Clean up spaces around Chinese characters
    text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
    # Add space after periods that don't have one
    text = re.sub(r'\.([^ \n])', r'. \1', text)
    return text.strip()

def convert_pdf_to_markdown(pdf_path, output_path=None):
    """Convert PDF file to Markdown format."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False

    # Set default output path if not provided
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '.md'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    print(f"Converting {pdf_path} to Markdown...")
    
    # Extract and clean text
    text = extract_text_from_pdf(pdf_path)
    text = clean_text(text)
    
    # Write to markdown file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(pdf_path)}\n\n")
            f.write(text)
        print(f"Successfully converted to: {output_path}")
        return True
    except Exception as e:
        print(f"Error writing to output file: {e}")
        return False

# Default paths
DEFAULT_PDF_PATH = "/Users/nicole/workspace/github/a476678244/learn_skills_everyday/bayes/每周贝叶斯事件/2025/第52周，#贝叶斯事件，完整版.pdf"
DEFAULT_MD_PATH = "/Users/nicole/workspace/github/a476678244/learn_skills_everyday/bayes/每周贝叶斯事件/every_week_bayes_events.md"

def main():
    parser = argparse.ArgumentParser(description='Convert PDF files to Markdown format')
    parser.add_argument('pdf_path', 
                       nargs='?',
                       default=DEFAULT_PDF_PATH,
                       help=f'Path to the input PDF file (default: {DEFAULT_PDF_PATH})')
    parser.add_argument('-o', '--output', 
                       default=DEFAULT_MD_PATH,
                       help=f'Path to the output Markdown file (default: {DEFAULT_MD_PATH})')
    
    args = parser.parse_args()
    
    # Handle file paths with spaces
    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path) and pdf_path.startswith('"') and pdf_path.endswith('"'):
        pdf_path = pdf_path[1:-1]
    
    convert_pdf_to_markdown(pdf_path, args.output)

if __name__ == "__main__":
    main()
