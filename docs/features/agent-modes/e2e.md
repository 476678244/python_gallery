# E2E 用例（含有头）

## 前置

- UI `http://localhost:3000`，API `http://localhost:8000`  
- Playwright：`test/e2e/`（实现阶段新增 spec）  
- 有头：`HEADED=1 npx playwright test <spec> --retries=0`  
- Phase 0：可用 Demo 手工过剧本；下列 S1–S4 为**实现后**合同  

## 规格文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `agent-modes.spec.ts`（拟） | ⬜ 未落地 | 本主题黄金路径 S1–S4 |
| `demo-modes.html` | ✅ | 视觉 / 剧本合同（非 Playwright） |

---

## S1 — Ask 硬只读

1. New Chat → `/ask` → badge 为 ask  
2. 发：「读取 workspace 某文件并总结；不要改任何文件」  
3. **期望**：请求 `mode=ask`；Exec/工具侧无 write / skill execute 成功；工作区文件未改  

## S1b — Safe 仅新建

1. `/safe` → badge = safe；芯片 create ✓ / update ✗ / delete ✗  
2. 新建一受控新路径文件 → **期望**成功  
3. 对已存在文件 write/overwrite 或 edit → **期望**失败可见；文件内容未改  
4. 尝试 delete/remove → **期望**失败可见  

## S2 — Agent 完整执行

1. 同会话或新会话 → `/agent`  
2. 发一条需写文件或明确工具写入的任务（受控临时路径）  
3. **期望**：`mode=agent`；写工具可用；与今日行为一致  

## S2b — Debug 全开可观测

1. `/debug` → badge = debug  
2. **期望**：Exec、Prompt Inspect、Skills（或等价）面板均展开；工具能力同 agent  
3. `/agent` → **期望**：解除强制全开（面板可回到默认折叠偏好）  

## S2c — Subagent 强制子代理观测

1. `/subagent` → badge = subagent  
2. 触发合法委派（或注入含 subagent 子树的 SSE）  
3. **期望**：Exec 展开；子块 look_ahead / nested 可见；Halt/Steer 可用；Prompt Inspect **未**被本 mode 强制打开  
4. `/agent` → **期望**：解除 Subagent pack 强制  

## S3 — Plan 结构 + 只读

1. `/plan`  
2. 发：「规划如何为 X 加功能，先不要改代码」  
3. **期望**：出现结构化计划；无文件写入；不会自动变 agent  

## S4 — Loop：先确认完成条件再武装

1. `/loop 30s ping workspace status`  
2. **期望**：出现确认框；未填完成条件时 Arm 禁用  
3. 填写「最多 3 tick」→ Arm → 至少 1 次 tick；status 含 stop 条件  
4. Stop（或 `/loop stop`）  
5. **期望**：stop 后无新 tick；取消确认则从未武装  

---

## 有头复验（人工）

```bash
cd test/e2e
HEADED=1 npx playwright test agent-modes.spec.ts --retries=0
```

Demo（Phase 0）：

```bash
open docs/features/agent-modes/demo-modes.html
```
