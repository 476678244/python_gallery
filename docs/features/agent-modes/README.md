# Agent Modes（/ask /agent /plan /safe /debug /subagent /loop）

会话级交互 mode：同一会话粘住一种策略，直到 slash 再切。

- **权限档**：ask（零写）→ **safe（仅新建）** → agent（满写）
- **观测档**：`/debug` = Full pack；`/subagent` = 子树 pack + spawn 必开
- **调度**：`/loop` 继承当时执行 mode

个人自用 + Fail Fast（硬门禁，非仅 prompt）。

| 项 | 值 |
|----|-----|
| Feature ID | `agent-modes` |
| SoT（方法论） | [methodology.md](./methodology.md) |
| **状态** | **核心验收通过** — [acceptance-report-2026-08-03.md](./acceptance-report-2026-08-03.md) |
| 使用语境 | 个人自用；禁止静默 fallback |

## 能力矩阵

| 能力 | 状态 |
|------|------|
| 执行 mode（ask / agent / plan / **safe** / debug / subagent） | ✅ |
| Safe：create-only；禁 update/delete | ✅ |
| Debug → Full pack | ✅ |
| Subagent → Subagent pack + spawn | ✅ |
| Loop 调度 | ✅ |
| 会话级粘性 | ✅ |
| Demo HTML | ✅ |
| API pytest + Playwright S0/S0b | ✅ |

## 文档索引

1. [methodology.md](./methodology.md) — 行为合同（矩阵 / 门禁 / pack）  
2. [design.md](./design.md) — **架构设计**（ModePolicy / 数据流 / UI）  
3. [plan.md](./plan.md) — **分阶段实现计划**（P0→F）  
4. [problem.md](./problem.md) — 失败复现与根因  
5. [milestones.md](./milestones.md) — 里程碑  
6. [acceptance.md](./acceptance.md) — 验收标准  
7. [e2e.md](./e2e.md) — 有头 E2E  
8. [scripts.md](./scripts.md) — 辅助脚本  
9. [cross-check.md](./cross-check.md) — 合同 vs 实现交叉核对  
10. [demo-modes.html](./demo-modes.html) — Demo  
11. [roundtable--modes-ui-demo.md](./roundtable--modes-ui-demo.md) — 圆桌  

```bash
open docs/features/agent-modes/demo-modes.html
```

相关：[skills-activation](../skills-activation/)、[sub-agents](../sub-agents/)、[ppt-mode](../ppt-mode/)（`/ppt` 扩展）。

## 相关代码（实现触点）

| 区域 | 路径 |
|------|------|
| Slash | `safeclaw-ui/my-app/src/features/chat/slash/commands.ts` |
| Chat 输入 / 发流 | `.../chat/components/chat-input.tsx`、`chat-api.ts` |
| Session settings | `.../entities/session/model.ts`、`stores/session-store.ts` |
| SSE / ChatRequest | `api/main.py` |
| FS 门禁 | `safe_claw/core/deepagents/backend.py`（write create-only；需接通 `allow_edit`） |
| Tools | `safe_claw/core/tools/manager.py` |
