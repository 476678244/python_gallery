# Acceptance Report — PPT Mode · 2026-08-05

## Verdict

**Phase A–D + E2E S0/S0b/S2/S3/S4 PASS + 真 LLM live probe PASS.**  
SoT: [methodology.md](./methodology.md) · [acceptance.md](./acceptance.md).

## Evidence

| Gate | Result | Notes |
|------|--------|-------|
| pytest `test/tools/test_ppt_tools.py` + `test_mode_policy.py` | **PASS** | tools happy path, save no-overwrite, preview, ToolManager gate, ppt policy |
| Playwright `ppt-mode.spec.ts` | **PASS (5)** | S0 badge/chips · S0b Deck pack · S2 outline+确认出稿 · S3 thumbs/v1–v2 · S4 sticky reload |
| Deck Outline card | **landed** | `DeckArtifactCard` + `parseDeckArtifact`；确认出稿 / 改大纲 |
| Live LLM probe | **PASS** | `liveprobe90688` v1→v2 + PNG + SSE |

```bash
conda activate safe_claw
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  python -m pytest test/tools/test_ppt_tools.py test/deepagents/test_mode_policy.py -q

cd test/e2e && FRONTEND_URL=http://localhost:3000 npx playwright test ppt-mode.spec.ts --retries=0
bash scripts/features/ppt-mode/probe_live_llm.sh
```

## What landed

1. **ModePolicy `ppt`**: create-only FS, spawn off, `observability=ppt`, `ppt_tools=True`, PPT system addendum  
2. **First-class tools** `safe_claw/core/tools/ppt.py` — only registered in `/ppt`  
3. **Preview**: Spire/Aspose → PNG; SSE `ppt_preview`; `GET /api/workspace-file` (+ Next rewrite)  
4. **UI**: `/ppt` slash, chips, PPT pack (Exec + Deck), `[PPT_STEER]` page/deck  
5. **Deck Outline artifact**: 确认出稿 → short generate prompt; 改大纲 → revise prompt  
6. **Skill** `pptx-authoring` guidance-only  
7. **Reload**: session mode 粘性 + observability pack 重挂（`chat-input` effect）  

## Follow-ups closed (2026-08-09)

- [x] UI thumbs refresh via `ppt_preview` SSE（Playwright S3）  
- [x] Outline CTA with real assistant message path（Playwright S2 mock SSE）  
- [x] Session sticky `mode=ppt` across reload（Playwright S4）  
- [x] 真 LLM v1→v2（API probe；见 Human spot-check）  

## Regression fix (2026-08-09 · sess-1786243607)

Homework session crashed after `safe_claw_ppt_*` wrote `_v1.pptx`:

1. **`SecureFilesystemBackend.download_files` / `upload_files`** — DeepAgents middleware called protocol methods that were missing → stream Error. Covered by `test/deepagents/test_filesystem_download_files.py`.
2. **Deck Artifact parse** — LLM headings like `### Deck Outline（共 6 页）` failed exact match; now prefix `\b` + markdown table storyboard. Playwright S2 uses suffix headings.
3. **PPT addendum** — allow heading suffixes; do not claim DingTalk upload; prefer ≤5 slides for short kid talks.

## Human spot-check (optional)

- [x] `/ppt` → badge + Deck panel（Playwright S0/S0b）  
- [x] Ask for outline → 确认出稿 → Exec shows `safe_claw_ppt_*` → thumbs appear — **真 LLM live probe PASS**（见下）  
- [x] 提需求·页 → `[PPT_STEER]` turn → `_v2` — **PASS**  

### Live LLM probe · 2026-08-05

```bash
bash scripts/features/ppt-mode/probe_live_llm.sh
```

| 项 | 结果 |
|----|------|
| session | `ppt-live-42b1dcd6` |
| deck | `liveprobe90688` |
| turn1 | ~12s · SSE `ppt_preview`×2 · `…_v1.pptx` + 2 PNG |
| turn2 `[PPT_STEER] slide=1` | ~8s · `…_v2.pptx` + 2 PNG；标题改为「Live Probe v2」 |
| `/api/workspace-file` | v1/v2 slide_01.png → 200 |

证据：`~/Downloads/safe_claw_worksapce/workspace/ppt/_evidence_2026-08-05/summary.json`  
预览样例：`…/previews/liveprobe90688_v1|v2/slide_01.png`
