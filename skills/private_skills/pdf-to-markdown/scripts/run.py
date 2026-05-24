#!/usr/bin/env python3
"""
PDF -> Markdown via MinerU (direct backend call, no API server).

Usage:
    python run.py <input.pdf> <output_dir> [--lang ch|en] [--no-formula] [--no-table]

Requires conda env `safe_claw` with `mineru[all]` installed and pipeline models downloaded.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_pdf_to_markdown(
    pdf_path: str | Path,
    output_dir: str | Path,
    lang: str = "ch",
    formula_enable: bool = True,
    table_enable: bool = True,
) -> Path:
    from mineru.cli.common import do_parse

    pdf_path = Path(pdf_path).expanduser().resolve()
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()

    print(f"[mineru] input : {pdf_path}")
    print(f"[mineru] output: {output_path}")
    print(f"[mineru] lang  : {lang}  formula={formula_enable}  table={table_enable}")

    do_parse(
        output_dir=str(output_path),
        pdf_file_names=[pdf_path.name],
        pdf_bytes_list=[pdf_bytes],
        p_lang_list=[lang],
        backend="pipeline",
        parse_method="auto",
        formula_enable=formula_enable,
        table_enable=table_enable,
        f_dump_md=True,
        f_dump_middle_json=True,
        f_dump_model_output=True,
        f_dump_orig_pdf=True,
        f_dump_content_list=True,
    )

    md_file = output_path / pdf_path.name / "auto" / f"{pdf_path.name}.md"
    print(f"[mineru] done -> {md_file}")
    return md_file


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a PDF to Markdown using MinerU.")
    ap.add_argument("pdf", help="Input PDF path")
    ap.add_argument("output_dir", help="Output directory")
    ap.add_argument("--lang", default="ch", choices=["ch", "en"], help="OCR language hint")
    ap.add_argument("--no-formula", action="store_true", help="Disable formula parsing")
    ap.add_argument("--no-table", action="store_true", help="Disable table parsing")
    args = ap.parse_args()

    md = parse_pdf_to_markdown(
        pdf_path=args.pdf,
        output_dir=args.output_dir,
        lang=args.lang,
        formula_enable=not args.no_formula,
        table_enable=not args.no_table,
    )
    return 0 if md.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
