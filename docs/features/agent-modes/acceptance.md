# 验收标准

勾选表示已满足。个人自用；Fail Fast；执行 mode（含 safe / debug / subagent）+ loop 调度；会话级粘性。

## 0. 文档合同（Phase 0）

- [x] [methodology.md](./methodology.md) 含 ask/agent/plan/**safe**/debug/subagent/loop、写权限拆列、观测 pack  
- [x] [design.md](./design.md) 架构与 ModePolicy  
- [x] [problem.md](./problem.md) / [plan.md](./plan.md) / [e2e.md](./e2e.md) 齐备  
- [x] [demo-modes.html](./demo-modes.html) Ask/Agent/Plan/Loop 剧本 + 工具策略芯片  
- [x] Demo 含 **Safe / Debug / Subagent** 并列剧本  
- [x] [docs/features/README.md](../README.md) 收录 `agent-modes`  

## A. API 门禁

- [x] `mode` 缺省 → 行为同今日 agent  
- [x] 非法 `mode` → HTTP 400（非静默当 agent）  
- [x] Ask：write / skill execute 不可用（工具未注册或调用失败可见） — ToolManager filter  
- [x] Plan：同上硬只读  
- [x] **Safe**：create-only + `allow_edit=False`（单元测试）  
- [x] Agent / Debug / Subagent：满工具策略（ModePolicy）  
- [x] Subagent：spawn=required（策略）  
- [x] Ask / Plan / Safe：`task` 被 SpawnGateMiddleware 硬挡（pytest）  
- [x] 会话 settings 默认 `mode=agent`（create session）  

## A2. Safe FS

- [x] `allow_edit=False`；create-only write（backend + tool wrapper）  
- [x] overwrite / edit 失败可见（pytest）  
- [x] 策略芯片：create ✓ / update ✗ / delete ✗（UI）  

## B. UI

- [x] `/ask` `/agent` `/plan` `/safe` `/debug` `/subagent` `/loop` 出现在 slash 帮助列表  
- [x] 切换后输入区 / header 可见 mode badge  
- [x] New Chat 默认 badge = agent  
- [x] 发消息请求体含当前 session `mode`  

## B2. Debug · Observability Full pack

- [x] `/debug` → `applyObservabilityPack("full")`（Exec+Skills+Prompts）  
- [x] 嵌套 / subagent / 闸门失败节点默认可见（有数据时）— Exec 树 + look_ahead  
- [x] Halt / 纠正方向在 Exec 头可用（Esc / R；Steer 真发流）  
- [x] 切到其它 mode 时按 pack 切换（default **释放** Full 强制的 Skills/Prompts）  

## B3. Subagent · Subagent Observability pack

- [x] `/subagent` → Exec 强制展开（不强制 Inspect/Skills）  
- [x] 子树 / look_ahead 默认展开（有委派时）  
- [x] **不**强制打开 Prompt Inspect / Skills  
- [x] 切到 `/agent` 后不再强制 Full/Sub pack  
- [x] 不放宽 spawn brief 硬闸门（合同 + sub-agents）  

## C. Plan 产物

- [x] Plan system prompt 要求 ### Plan / Risks / Pending  
- [x] 专用 Plan 卡片组件（步骤 / 风险 / 待确认 + 显式切 Agent/Safe）  
- [x] Plan 不会自动改文件或静默切到 agent  

## D. Loop

- [x] `/loop [interval] <prompt>` 先弹出完成/终止条件确认，**空条件不可 Arm**  
- [x] 取消确认 → 不武装  
- [x] Arm 后 status 显示 stop 条件；tick 带当时 session mode  
- [x] `/loop stop` 或点 status 停止  
- [x] 空 prompt → 用法提示  

## E. 有头黄金路径

- [x] Playwright `agent-modes.spec.ts` S0/S0b/S3/S4（slash + Plan 卡 + loop）  
- [x] Playwright `sub-agents.spec.ts` S1/S1b/S2b/S3（嵌套树 + Halt banner）  
- [x] API/单元门禁验收 — 见 [acceptance-report-2026-08-03.md](./acceptance-report-2026-08-03.md)  

## 明确不验收（本期实现阶段仍不纳入）

- 全局 `agent_config.mode`  
- Streamlit 对等  
- Cursor 云 Agent 协议  
- Subagent brief 闸门 / fork 协议实现细节（归 [sub-agents](../sub-agents/)；本主题只验「mode 强制打开观测面」）  
