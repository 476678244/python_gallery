# Skills Activation（可靠激活）

侧栏打开 skill ≠ 真进 DeepAgent / 真可调用。本主题对齐 **UI 开关 → `agent_config` → 加载列表 → 工具过滤 → 可观测**，个人自用 + Fail Fast。

| 项 | 值 |
|----|-----|
| Feature ID | `skills-activation` |
| 驱动案例 | 关掉 Ljg 文件夹后，`ljg-*` 既不进 loaded list，也不能被 `skill_discover` 跑起来 |
| SoT | `SkillsManager` + `~/Downloads/safe_claw_worksapce/Data/agent_config.json` |
| **状态** | Phase A–D **完成**（见 [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md)） |
| 使用语境 | 个人自用；禁止静默 fallback（同 memory NA-04） |

## 能力矩阵

| 能力 | 状态 |
|------|------|
| 树开关持久化到 `agent_config` | ✅ |
| Chat 使用与 SoT 一致的 enabled 集 | ✅（忽略废弃的 request.enabled_skills） |
| DeepAgent `skills=` 与 ToolManager 同一过滤 | ✅ |
| 超过上下文上限时显式失败 | ✅ Fail Fast（无静默 15） |
| SSE / UI 展示 **实际加载** 列表 | ✅ `skills_loaded` vs router |
| 有头黄金路径 S1–S3 | ✅ Playwright 绿（有头可选复验） |

## 文档索引

1. [problem.md](./problem.md) — 失败复现与根因  
2. [plan.md](./plan.md) — 分阶段计划  
3. [milestones.md](./milestones.md) — 测试里程碑  
4. [acceptance.md](./acceptance.md) — 验收标准  
5. [e2e.md](./e2e.md) — 有头 E2E  
6. [scripts.md](./scripts.md) — 辅助脚本  
7. [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md) — 通过报告  

## 相关代码

| 区域 | 路径 |
|------|------|
| UI Skills Path | `safeclaw-ui/my-app/src/components/right-panel.tsx` |
| API SoT | `api/main.py`（`toggle_skill`、`chat_stream`、`_get_skills_manager`） |
| Manager / Discovery | `safe_claw/core/skills/manager.py`、`discovery.py` |
| DeepAgent | `safe_claw/core/deepagents/official_integration.py` |
| Tools | `safe_claw/core/tools/manager.py` |
| 测试 | `test/api/test_skills_activation.py`、`test/e2e/skills-activation.spec.ts` |
