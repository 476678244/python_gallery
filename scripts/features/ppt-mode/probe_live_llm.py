#!/usr/bin/env python3
"""Live LLM probe: /ppt 直接出稿 → ppt_preview → PPT_STEER → _v2.

Writes evidence JSON under WORKSPACE ppt/_evidence_* (not source tree tmp).
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000"
WORKSPACE = Path.home() / "Downloads" / "safe_claw_worksapce" / "workspace"
EVIDENCE_DIR = WORKSPACE / "ppt" / "_evidence_2026-08-05"
DECK_HINT = f"liveprobe{int(time.time()) % 100000}"


def _sse_events(resp: httpx.Response):
    buf = ""
    for chunk in resp.iter_text():
        buf += chunk
        while "\n\n" in buf:
            block, buf = buf.split("\n\n", 1)
            data_lines = []
            for line in block.splitlines():
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
            if not data_lines:
                continue
            raw = "\n".join(data_lines).strip()
            if not raw or raw == "[DONE]":
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def stream_turn(session_id: str, messages: list[dict], mode: str = "ppt") -> dict:
    out = {
        "ppt_preview": [],
        "tools": [],
        "execution_steps": [],
        "errors": [],
        "content": "",
        "done": None,
    }
    with httpx.Client(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
        with client.stream(
            "POST",
            f"{API}/chat/stream",
            json={
                "session_id": session_id,
                "mode": mode,
                "messages": messages,
                "stream": True,
            },
        ) as resp:
            if resp.status_code != 200:
                body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"[ppt-probe] /chat/stream HTTP {resp.status_code}\n  Body: {body[:800]}"
                )
            for ev in _sse_events(resp):
                t = ev.get("type")
                if t == "ppt_preview":
                    out["ppt_preview"].append(ev)
                elif t == "tool":
                    out["tools"].append(ev)
                elif t == "execution_step":
                    out["execution_steps"].append(ev)
                elif t == "error":
                    out["errors"].append(ev)
                elif t == "content":
                    out["content"] = ev.get("content") or out["content"]
                elif t == "done":
                    out["done"] = ev
    return out


def list_deck_artifacts(prefix: str) -> dict:
    ppt_root = WORKSPACE / "ppt"
    pptx = sorted(ppt_root.glob(f"{prefix}*_v*.pptx")) + sorted(
        ppt_root.glob(f"*live*_v*.pptx")
    )
    # Also any new pptx from last few minutes
    recent = []
    now = time.time()
    for p in ppt_root.glob("*_v*.pptx"):
        if now - p.stat().st_mtime < 900:
            recent.append(p)
    previews = []
    for d in (ppt_root / "previews").glob("*") if (ppt_root / "previews").exists() else []:
        if d.is_dir() and now - d.stat().st_mtime < 900:
            pngs = sorted(d.glob("slide_*.png"))
            previews.append({"dir": str(d), "png_count": len(pngs), "pngs": [str(x) for x in pngs]})
    return {
        "pptx_matching_hint": [str(p) for p in pptx],
        "pptx_recent": [str(p) for p in sorted(recent, key=lambda x: x.stat().st_mtime)],
        "previews_recent": previews,
    }


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    session_id = f"ppt-live-{uuid.uuid4().hex[:8]}"

    # Create session sticky mode=ppt
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{API}/sessions",
            json={"title": f"PPT live {DECK_HINT}", "model": None},
        )
        if r.status_code >= 400:
            print(f"[warn] session create {r.status_code}: {r.text[:200]}")
        else:
            data = r.json()
            session_id = data.get("id") or data.get("session_id") or session_id
            client.patch(
                f"{API}/sessions/{session_id}",
                json={"settings": {"mode": "ppt"}},
            )

    print(f"session={session_id} deck_hint={DECK_HINT}")

    msg1 = (
        f"直接出稿。请用 safe_claw_ppt_* 工具完成，不要空谈。\n"
        f"deck_id 必须用：{DECK_HINT}\n"
        f"两页：\n"
        f"1) 标题「Live Probe」要点：真实 LLM / 预览刷新\n"
        f"2) 标题「Next」要点：_v2 迭代\n"
        f"主题 default。完成后必须 save_version 再 preview。"
    )
    print("--- turn1: 直接出稿 ---")
    t0 = time.time()
    turn1 = stream_turn(
        session_id,
        [{"role": "user", "content": msg1}],
    )
    print(f"turn1 done in {time.time() - t0:.1f}s previews={len(turn1['ppt_preview'])} errors={len(turn1['errors'])}")
    if turn1["errors"]:
        print("turn1 errors:", json.dumps(turn1["errors"], ensure_ascii=False)[:500])

    arts1 = list_deck_artifacts(DECK_HINT)
    (EVIDENCE_DIR / "turn1.json").write_text(
        json.dumps({"turn": turn1, "artifacts": arts1}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Resolve deck_id/version from preview event or filesystem
    deck_id = DECK_HINT
    version = 1
    if turn1["ppt_preview"]:
        deck_id = turn1["ppt_preview"][-1].get("deck_id") or deck_id
        version = turn1["ppt_preview"][-1].get("version") or version
    elif arts1["pptx_recent"]:
        # parse name
        name = Path(arts1["pptx_recent"][-1]).stem  # foo_v1
        if "_v" in name:
            deck_id, _, ver = name.rpartition("_v")
            try:
                version = int(ver)
            except ValueError:
                pass

    v1_ok = any(f"_v1.pptx" in p or f"_v{version}.pptx" in p for p in arts1["pptx_recent"])
    png_ok = any(p.get("png_count", 0) >= 1 for p in arts1["previews_recent"])
    preview_evt_ok = len(turn1["ppt_preview"]) >= 1

    print(f"v1_files={v1_ok} pngs={png_ok} sse_preview={preview_evt_ok}")
    print("recent pptx:", arts1["pptx_recent"][-5:])
    print("content tail:", (turn1["content"] or "")[-400:])

    if not (v1_ok or preview_evt_ok):
        print("FAIL: no v1 pptx / ppt_preview — abort before steer")
        return 1

    msg2 = (
        f"[PPT_STEER] slide=1\n"
        f"deck_id: {deck_id}\n"
        f"version: {version}\n"
        f"需求：把第 1 页标题改成「Live Probe v2」，并 save_version + preview 新版本。"
    )
    print("--- turn2: PPT_STEER → v2 ---")
    t1 = time.time()
    history = [
        {"role": "user", "content": msg1},
        {"role": "assistant", "content": turn1["content"] or "(ok)"},
        {"role": "user", "content": msg2},
    ]
    turn2 = stream_turn(session_id, history)
    print(f"turn2 done in {time.time() - t1:.1f}s previews={len(turn2['ppt_preview'])} errors={len(turn2['errors'])}")
    arts2 = list_deck_artifacts(deck_id)
    (EVIDENCE_DIR / "turn2.json").write_text(
        json.dumps({"turn": turn2, "artifacts": arts2}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    has_v2 = any("_v2.pptx" in p for p in arts2["pptx_recent"])
    preview2 = len(turn2["ppt_preview"]) >= 1 or any(
        "v2" in (p.get("dir") or "") and p.get("png_count", 0) >= 1
        for p in arts2["previews_recent"]
    )

    summary = {
        "session_id": session_id,
        "deck_id": deck_id,
        "turn1_preview_events": len(turn1["ppt_preview"]),
        "turn2_preview_events": len(turn2["ppt_preview"]),
        "v1_ok": bool(v1_ok or preview_evt_ok),
        "v2_ok": bool(has_v2),
        "preview_refresh_ok": bool(preview_evt_ok or png_ok),
        "preview2_ok": bool(preview2),
        "pptx_recent": arts2["pptx_recent"],
        "previews_recent": arts2["previews_recent"],
        "turn1_errors": turn1["errors"],
        "turn2_errors": turn2["errors"],
    }
    (EVIDENCE_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if summary["v1_ok"] and summary["v2_ok"] and (summary["preview_refresh_ok"] or summary["preview2_ok"]):
        print("PASS: live LLM ppt v1→v2 + preview")
        return 0
    print("FAIL: incomplete live path")
    return 1


if __name__ == "__main__":
    sys.exit(main())
