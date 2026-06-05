---
name: pdf-to-markdown
description: Use this skill when the user wants to convert a PDF (especially scanned, mixed-language, formula-heavy, or table-heavy documents) into Markdown using MinerU. Preserves headings, images, tables, and formulas. Best for Chinese/English documents where high-fidelity layout extraction matters. Trigger on requests like "convert PDF to md", "提取 PDF 内容", "解析 PDF 保留格式".
---

# PDF → Markdown via MinerU

## Overview

MinerU is a layout-aware PDF parser. Unlike `pdfplumber` or `pypdf` (which extract raw text), it uses ML models to detect headings, tables, formulas, and images, then emits structured Markdown with extracted asset files.

Use this skill instead of `pypdf`/`pdfplumber` whenever the user cares about **document structure**, **scanned PDFs**, **CJK content**, or **formulas/tables**.

## Prerequisites

- Python env with `mineru[all]` installed: `pip install mineru[all]`
- Models downloaded once: `mineru-models-download -s modelscope -m pipeline`
- Activate your env before running (e.g. conda, venv, etc.)

## Why direct Python API, not the `mineru` CLI

The `mineru` CLI auto-spawns a local `mineru-api` FastAPI server and polls health. On macOS this often **times out (503)** because model load > 300 s default. Calling `mineru.cli.common.do_parse` directly bypasses the API layer and works reliably.

> Avoid: `mineru -p <pdf> -o <out>` (flaky on cold start)
> Prefer: `python scripts/run.py <pdf> <out>` (this skill)

## Standard Operating Procedure

### Step 1 — Inspect the input

```bash
ls -la "<pdf_path>"
```

Confirm the filename (watch for special chars like `#`, `，`, spaces). Pass the **exact** name; do not rename.

### Step 2 — Pick the language hint

| Document content | `lang` |
|------------------|--------|
| 中文为主 | `"ch"` |
| English-only | `"en"` |
| Mixed CJK | `"ch"` (handles English fallback) |

### Step 3 — Run the conversion script

```bash
python scripts/run.py "<input.pdf>" "<output_dir>" --lang ch
```

First run will load models (~25 s); subsequent calls in same process are fast.

### Step 4 — Locate the output

```
<output_dir>/
└── <pdf_filename>/
    └── auto/
        ├── <pdf_filename>.md          ← main Markdown
        ├── images/                    ← extracted figures
        ├── <...>_content_list.json    ← structured blocks
        ├── <...>_middle.json          ← internal layout JSON
        ├── <...>_layout.pdf           ← debug: layout boxes
        └── <...>_origin.pdf           ← copy of input
```

The Markdown file references images via relative paths (`images/<hash>.jpg`), so move the whole `auto/` directory together.

## Code: minimal direct call

```python
from pathlib import Path
from mineru.cli.common import do_parse

def parse_pdf_to_markdown(pdf_path: str, output_dir: str, lang: str = "ch") -> Path:
    pdf_path = Path(pdf_path).expanduser().resolve()
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_bytes = pdf_path.read_bytes()

    do_parse(
        output_dir=str(output_path),
        pdf_file_names=[pdf_path.name],
        pdf_bytes_list=[pdf_bytes],
        p_lang_list=[lang],
        backend="pipeline",
        parse_method="auto",
        formula_enable=True,
        table_enable=True,
        f_dump_md=True,
        f_dump_middle_json=True,
        f_dump_model_output=True,
        f_dump_orig_pdf=True,
        f_dump_content_list=True,
    )
    return output_path / pdf_path.name / "auto" / f"{pdf_path.name}.md"
```

## Key Parameters

| Parameter | Default | When to change |
|-----------|---------|----------------|
| `backend` | `"pipeline"` | Use `"hybrid-auto-engine"` only if you have a VLM server; `pipeline` works on CPU/MPS |
| `parse_method` | `"auto"` | Force `"ocr"` if PDF is scanned and `auto` misclassifies it as text |
| `lang` | `"ch"` | `"en"` improves OCR speed/accuracy on pure English docs |
| `formula_enable` | `True` | Disable for plain prose to speed up ~30% |
| `table_enable` | `True` | Disable if no tables exist |

## Verified Examples

### Example 1 — English Patreon PDF (5 pages, mixed Chinese/English)
- Input: `Dot Plot__ Patreon.pdf` (4 MB)
- Output: 12.8 KB Markdown, 17 image assets
- Time: ~75 s (cold start incl. model load)

### Example 2 — Chinese macro report (38 pages, dense charts)
- Input: `第21周，#贝叶斯事件，摘要版.pdf` (18 MB)
- Output: 146 KB Markdown, ~30 images, structured headings preserved
- Time: ~95 s

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: mineru` | Wrong Python env | Activate the env where `mineru[all]` is installed |
| `Timed out waiting for local mineru-api` | CLI cold-start race | Skip CLI; use direct `do_parse` |
| Empty output dir | First run downloading models | Pre-run `mineru-models-download -s modelscope -m pipeline` |
| Garbled Chinese | Wrong `lang` hint | Set `lang="ch"` |
| Tables come out as text | `table_enable=False` or low-res scan | Ensure `table_enable=True`; for scans add `parse_method="ocr"` |
| Filename with special chars breaks shell | zsh interprets `#`, `，` | Quote the path: `"…"` |

## Related Files

- `scripts/run.py` — copy-pastable converter CLI
- MinerU upstream docs: https://github.com/opendatalab/MinerU/blob/master/docs/zh/usage/quick_usage.md
