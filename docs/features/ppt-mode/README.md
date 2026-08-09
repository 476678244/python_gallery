# PPT Mode（`/ppt`）

会话级执行 mode：用**一等 PPT Tools**创作与改稿，配合 **PPT Observability pack**（Exec + 幻灯片实时预览）与页级 **提需求**（`[PPT_STEER]`）。Skill 仅作风格/流程指引，**不能**替代 tools。

| 项 | 值 |
|----|-----|
| Feature ID | `ppt-mode` |
| Slash | `/ppt` |
| SoT（行为） | [methodology.md](./methodology.md) |
| 系统设计 | [design.md](./design.md) |
| 执行计划 | [plan.md](./plan.md) |
| 验收标准 | [acceptance.md](./acceptance.md) |
| **状态** | **验收报告已出** — [acceptance-report-2026-08-05.md](./acceptance-report-2026-08-05.md) |
| 使用语境 | 个人自用；Fail Fast；禁止静默 fallback |
| 父主题 | [agent-modes](../agent-modes/)（枚举扩展） |

## 能力矩阵（目标态）

| 能力 | 状态 |
|------|------|
| `/ppt` 会话粘性 + ModePolicy（create-only FS） | ✅ |
| 一等 `safe_claw_ppt_*` tools（仅 ppt mode 注册） | ✅ |
| PPT Observability pack（Exec + Deck Preview） | ✅ |
| `save_version` → `preview` → UI 实时缩略图 | ✅（SSE `ppt_preview` + `/api/workspace-file`） |
| 页级 / 全局 `[PPT_STEER]` 提需求 | ✅ |
| `pptx-authoring` skill（指引，可选） | ✅ |
| pytest + Playwright 验收 | ✅ pytest + Playwright S0–S4（5）+ live LLM probe |

## 文档索引

1. [methodology.md](./methodology.md) — 行为合同（mode / tools / pack / steer）  
2. [design.md](./design.md) — **系统设计**（架构、数据流、模块边界）  
3. [plan.md](./plan.md) — **执行计划**（分阶段）  
4. [acceptance.md](./acceptance.md) — **验收标准**  
5. [problem.md](./problem.md) — 驱动问题  
6. [e2e.md](./e2e.md) — E2E 用例  
7. [scripts.md](./scripts.md) — 辅助脚本  

相关：[agent-modes](../agent-modes/)、[skills-activation](../skills-activation/)、[sub-agents](../sub-agents/)（steer 信号模式参考）。

## 相关代码（实现触点 · 目标）

| 区域 | 路径 |
|------|------|
| ModePolicy | `safe_claw/core/agent_modes/policy.py` |
| PPT Tools | `safe_claw/core/tools/ppt.py` |
| ToolManager | `safe_claw/core/tools/manager.py` |
| SSE / preview API | `api/main.py` |
| Slash / mode UI | `safeclaw-ui/my-app/src/features/chat/slash/commands.ts`、`entities/agent-mode.ts` |
| Deck Preview | `safeclaw-ui/my-app/src/components/`（新面板） |
| Skill（辅助） | `skills/private_skills/pptx-authoring/` |
