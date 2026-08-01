# Skills Activation — Acceptance Report (2026-08-01)

## Verdict

**Automated chain PASS.** SoT Fail Fast + tool filter + `skills_loaded` SSE + S1–S3 Playwright green. Headed visual / Prompt Inspect still recommended for human spot-check.

## Evidence

| Gate | Result |
|------|--------|
| `pytest test/api/test_skills.py test/api/test_skills_activation.py` | PASS (9) |
| `pytest test/api/` | PASS (23) |
| `scripts/skills/verify_enabled_filter.sh` | PASS |
| curl: enable only `flow_coding_testing` → stream `skills_loaded` | `['flow_coding_testing']` |
| `npx playwright test skills-activation.spec.ts --retries=0` | PASS (S1–S3) |

## What landed

1. **SoT**: `SkillsManager` + `agent_config.json`; SM init fail → `/skills` **503**
2. **Folder toggle**: strict collection id match (`_skill_collection_id`); no empty→all soft-reset
3. **DeepAgent**: inject API `skills_manager`; no Streamlit fork on API path
4. **Tools**: `skill_list_*` / discovery honor enabled allowlist
5. **No silent 15**: over `max_skills` / context → `ValueError` (Fail Fast)
6. **Observability**: SSE `skills_loaded` (+ UI Skills Path “loaded” vs “router”)
7. **Deprecated**: `ChatRequest.enabled_skills` ignored (logged)

## Human spot-check (optional)

- [ ] Headed: `HEADED=1 npx playwright test skills-activation.spec.ts --retries=0`
- [ ] Prompt Inspect shows CURRENTLY LOADED SKILLS matching tree
- [ ] Ask model “列出当前加载的 skills” verbally matches SSE list

If any human item fails, open `human-non-accept-report-*.md` with NA-id.
