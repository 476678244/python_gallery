#!/usr/bin/env python3
"""Ingest Obsidian investment jargon wiki notes into SafeClaw Memory.

See: docs/features/memory-system/scripts.md
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import httpx

DEFAULT_JARGON = Path(
    "/Users/nicole/workspace/github/a476678244/obsidian_wiki_investment/wiki/jargon"
)
API = os.environ.get("API", "http://localhost:8000")
JARGON = Path(os.environ.get("JARGON_DIR", DEFAULT_JARGON))


def extract_title(text: str, stem: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    m = re.search(r"title:\s*[\"']?([^\"'\n]+)", text, re.I)
    if m:
        return m.group(1).strip()
    return stem


def main() -> int:
    files = sorted(JARGON.glob("*.md"))
    if not files:
        print(f"[ingest] No markdown under {JARGON}", file=sys.stderr)
        return 1

    created = []
    errors = []

    with httpx.Client(timeout=30.0, trust_env=False) as client:
        health = client.get(f"{API}/health")
        if health.status_code != 200:
            print(f"[ingest] API health failed: {health.status_code}", file=sys.stderr)
            return 1

        for path in files:
            raw = path.read_text(encoding="utf-8")
            title = extract_title(raw, path.stem)
            content = (
                f"[Investment Jargon Wiki] {title}\n"
                f"source: wiki/jargon/{path.name}\n\n"
                f"{raw.strip()}"
            )
            if len(content) > 6000:
                content = content[:5997] + "..."

            keywords = list(
                {
                    "jargon",
                    "investment",
                    "wiki",
                    "黑话",
                    path.stem,
                    title,
                    *[w for w in re.split(r"[\s/_\-（）()]+", title) if len(w) >= 2][:8],
                }
            )

            res = client.post(
                f"{API}/memory",
                json={
                    "content": content,
                    "importance": 0.92,
                    "keywords": keywords[:16],
                    "metadata": {
                        "source": "obsidian_wiki_investment",
                        "path": str(path),
                        "slug": path.stem,
                        "collection": "jargon",
                    },
                },
            )
            if res.status_code != 200:
                errors.append({"file": path.name, "status": res.status_code, "body": res.text[:200]})
                continue
            body = res.json()
            created.append({"file": path.name, "title": title, "id": body.get("id")})

        stats = client.get(f"{API}/memory", params={"layer": "active", "limit": 1}).json().get(
            "stats", {}
        )

    # Optional: rebuild local vector index when caller enables it in-process
    rebuild_note = None
    if os.environ.get("MEMORY_REBUILD_VECTORS") == "1":
        try:
            from safe_claw.core.memory.manager import MemoryManager
            from safe_claw.models.config import MemoryConfig

            workspace = Path.home() / "Downloads" / "safe_claw_worksapce" / "workspace"
            mm = MemoryManager(
                config=MemoryConfig(enable_vector_search=True),
                workspace_path=str(workspace),
            )
            rebuild_note = {"indexed": mm.rebuild_vector_index()}
        except Exception as e:
            rebuild_note = {"error": str(e)}

    print(
        json.dumps(
            {
                "ingested": len(created),
                "errors": errors,
                "stats": stats,
                "jargon_dir": str(JARGON),
                "vector_rebuild": rebuild_note,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
