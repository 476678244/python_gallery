# Sub Agents（走一步看三步）

主 agent 编排、subagent 隔离执行；**「看三步」硬闸门防冒进**，用户侧 Exec **默认展开**可观测，且 **返工/纠正不污染主 agent 上下文**。个人自用 + Fail Fast。

| 项 | 值 |
|----|-----|
| Feature ID | `sub-agents` |
| 驱动案例 | 主 agent 调了 `task`，UI/SSE 看不出子树；委派无前瞻；fork 空壳 success |
| SoT（方法论） | [methodology.md](./methodology.md) — 硬闸门 brief + 双通道隔离 |
| **状态** | 本期 A–D2/F 自动化验收 PASS；证据见 [evidence/](./evidence/README.md)；Phase C（fork）未验收 |
| 使用语境 | 个人自用；观测默认展开；禁止静默 fallback |

## 能力矩阵

| 能力 | 状态 |
|------|------|
| 「走一步看三步」方法论文档 | ✅ 见 methodology |
| Spawn brief 硬闸门（缺字段不 spawn） | ✅ |
| SSE 子树（`subagent` + nested `tool_call` + parent） | ✅ |
| Exec 默认展开前瞻三步 + 中间工具/推理 | ✅ |
| 观测通道 ≠ 主上下文（中间步不回灌） | ✅（mock SSE / Demo） |
| 返工 = 重新 spawn（非污染主线程续聊） | ⬜ 部分（Steer 信号已接） |
| Skill `context: fork` 真 spawn | ⬜ Phase C |
| 自定义 `subagents=` + enabled skills SoT | ⬜ |
| 有头黄金路径 E2E | ✅ headless；headed 可选 |
| 一键 Stop the World | ✅ Demo + React Exec 头 |
| 一键纠正方向 → 提示 Main 换向 | ✅ Demo + React Exec 头 |

## 文档索引

1. [methodology.md](./methodology.md) — 走一步看三步 + 硬闸门 + 双通道隔离  
2. [problem.md](./problem.md) — 失败复现与根因  
3. [plan.md](./plan.md) — 分阶段计划  
4. [milestones.md](./milestones.md) — 测试里程碑  
5. [acceptance.md](./acceptance.md) — 验收标准  
6. [e2e.md](./e2e.md) — 有头 E2E  
7. [evidence/README.md](./evidence/README.md) — **验收 Evidence Pack**  
8. [acceptance-report-2026-08-03.md](./acceptance-report-2026-08-03.md) — 验收报告  
9. [scripts.md](./scripts.md) — 辅助脚本  
10. [demo-observability.html](./demo-observability.html) — **可观测性 Demo**（prod 壳 + Exec 嵌套）  
11. [roundtable--observability-ui-demo.md](./roundtable--observability-ui-demo.md) — ljg-roundtable 讨论 Demo 设计  
12. [button-design.md](./button-design.md) — 按钮分层：Exec 头 Halt/Steer vs harness 场景 ghost  

```bash
open docs/features/sub-agents/demo-observability.html
```

实现 React 时以该 Exec 展示为视觉合同，改 [`right-panel.tsx`](../../../safeclaw-ui/my-app/src/components/right-panel.tsx) `ExecutionPathPanel`，勿另起暗色皮肤。

相关主题：[skills-activation](../skills-activation/)（enabled skills SoT，子代理须复用）。

## 相关代码

| 区域 | 路径 |
|------|------|
| DeepAgent stream / prompt | `safe_claw/core/deepagents/official_integration.py` |
| 硬闸门（拟） | `safe_claw/core/deepagents/spawn_brief.py` |
| Skill fork | `safe_claw/core/skills/executor.py`、`manifest.py` |
| ToolManager | `safe_claw/core/tools/manager.py` |
| SSE | `api/main.py`（`/chat/stream`） |
| Exec UI | `safeclaw-ui/my-app/src/entities/execution/`、`stores/execution-store.ts`、`features/agent/components/execution-graph.tsx`、`components/right-panel.tsx` |
| Chat SSE 客户端 | `safeclaw-ui/my-app/src/features/chat/services/chat-api.ts` |
