# 验收标准

勾选表示已满足。个人自用；Fail Fast；DeepSeek 为全局默认模型。

## A. SoT / Fail Fast

- [x] `GET /skills` 在 SM 不可用时 **HTTP 503**（非空树） — `test_skills_503_when_manager_unavailable`
- [x] Toggle 后 `agent_config.json` 的 `enabled_skills` 立即与树一致 — `test_agent_config_persists_enabled_skills`
- [x] 硬刷新后树状态与配置一致 — E2E S1
- [x] Folder 开关不误伤无关 path（严格匹配） — `test_folder_toggle_strict_no_collateral` + `verify_enabled_filter.sh`

## B. 加载与工具

- [x] 仅 enabled 进入 DeepAgent `skills=` — `test_deep_agent_get_loaded_skills_matches_filter`
- [x] `skill_list_available` / discover **不含** disabled — `test_filtered_paths_and_discovery_honor_enabled`
- [x] 超限不再静默截断 15（error 或可见 truncation） — `ValueError` on `max_skills` / context

## C. 可观测

- [x] SSE（或 Exec）出现 **skills_loaded**（实际 path/名），与 router chips 区分 — curl + E2E S1/S2；UI badge `loaded` vs `router`
- [x] Prompt Inspect 能看到当前 loaded skills — system prompt 注入 `CURRENTLY LOADED SKILLS`（人工有头复验可选）

## D. 有头黄金路径

- [x] S1：只开少量 skill → 问加载列表 → SSE `skills_loaded` 一致 — `skills-activation.spec.ts`
- [x] S2：关 Ljg → `skills_loaded` 无 ljg-* — 同上
- [x] S3：`/skill` 与 enabled 一致（关后 autocomplete 不含） — 同上

## E. 文档 / 回归

- [x] 本目录文档与行为一致
- [x] API skill-tree 合同不回归 — `test/api/test_skills.py`
- [x] 有 `acceptance-report-2026-08-01.md`；过程拒绝项另开 `human-non-accept-report-*`

## 明确不验收（本期）

- Per-session 独立 skill 配置
- 新 skill 内容质量
- Memory 召回
