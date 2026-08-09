# 问题：只有全 Agent，没有可选 Mode

> 实现前保留为驱动审计；修复后本页作根因记录。验收见 acceptance。

## 用户可见现象

| 操作 | 实际 | 期望 |
|------|------|------|
| 想只问「这段代码做什么」 | 仍加载写工具 / skill execute；可能改文件 | `/ask`：硬只读，无写无 execute |
| 想先出方案再动手 | 无 Plan；模型可能直接改 | `/plan`：只读 + 结构化计划；不改文件 |
| 想定时复查某状态 | 无 Loop | `/loop 5m <prompt>` + 可 stop |
| 输入 `/ask` | 落入 skill autocomplete 或 unknown | 切换会话 mode + badge |
| 同一会话混用策略 | 无法粘住 | 会话级 `mode`，直到再切 |

## 复现步骤（当前）

```bash
# 1) 起 API + UI，任意 New Chat 发消息
# 2) 观察：始终 allow_write=True 全工具路径；请求体无 mode

curl -sN -X POST http://127.0.0.1:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"只解释不要改文件：README 讲了什么"}],"session_id":"mode-probe","stream":true}' \
  | head -n 40

# 3) UI：输入 /ask — 期望出现 mode 命令；现状：slash 列表无 ask/agent/plan/loop
```

Slash SoT（现状）：`safeclaw-ui/my-app/src/features/chat/slash/commands.ts` 仅  
`help` / `model` / `skill` / `remember` / `memory` / `clear` / `new`。

## 根因（审计摘要）

### R1 — 产品无 AgentMode 概念

- 无 `ask|agent|plan|loop` 枚举或会话字段  
- `SessionSettings` 有 model / skills / temperature 等，无 `mode`

### R2 — Chat 管道单一全权路径

- `/chat/stream` 构图时 FS `allow_write` 写死 `True`  
- ToolManager 始终注册写与 skill execute  
- 无 per-request / per-session 工具配置文件

### R3 — Slash 无 mode 动作

- `SLASH_COMMANDS` 不含四 mode  
- `SlashMode` 仅 palette 状态，与策略无关

### R4 — 无 Loop 调度子系统

- 无 interval 解析、tick、stop、与 chat stream 的重入合同

### R5 — 软约束不足

- System prompt「破坏性操作先确认」无法阻止工具已被注册后的误用  
- 符合本仓 Fail Fast：策略须机器门禁

## 明确不在本主题

- Cursor 云 Agent 协议对等  
- Streamlit 改造  
- Subagent Exec 嵌套 UI（[sub-agents](../sub-agents/)）  
- Skills 开关 SoT（[skills-activation](../skills-activation/)）  
