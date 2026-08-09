# Acceptance Report — Agent Modes · 2026-08-03

## Scope delivered

| Area | Status |
|------|--------|
| ModePolicy (`ask/agent/plan/safe/debug/subagent`) | ✅ |
| API `ChatRequest.mode` + 400 on invalid/`loop` | ✅ |
| FS `allow_edit` + safe create-only | ✅ |
| Tool filter + create-only write wrapper | ✅ |
| Session default `mode=agent` | ✅ |
| UI slash / badge / chips / stream `mode` | ✅ |
| Observability packs (`applyObservabilityPack`) | ✅ |
| Loop arm/stop (client scheduler) | ✅ |
| Demo Safe/Debug/Subagent scenarios | ✅ |
| pytest ModePolicy + API + FS edit | ✅ |
| Playwright `agent-modes.spec.ts` | ✅ **2 passed** (S0/S0b) |

## Commands

```bash
conda activate safe_claw
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  python -m pytest test/deepagents/test_mode_policy.py \
    test/deepagents/test_filesystem_allow_edit.py \
    test/api/test_agent_modes.py -q

cd test/e2e && npx playwright test agent-modes.spec.ts --retries=0
open docs/features/agent-modes/demo-modes.html
```

## Notes

- Loop ticks send execution `mode` (not `mode=loop`) via session sticky badge.
- Subagent brief hard-gate remains in [sub-agents](../sub-agents/); this feature forces the observability pack + spawn policy only.
- Plan artifact is prompt-shaped (`### Plan` / Risks); dedicated Plan card UI can harden later.
- Cross-check follow-up: [cross-check.md](./cross-check.md) — SpawnGateMiddleware for ask/plan/safe; Full pack exit releases Skills/Prompts. pytest **22 passed**.
- Plan artifact card + Exec Halt/Steer (worldStopped latch, Steer streams via `safeclaw:send-prompt`). Playwright agent-modes S3 + sub-agents S2b green.
