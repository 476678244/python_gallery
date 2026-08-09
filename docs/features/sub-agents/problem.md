# 问题：有 subagent 能力，看不见、管不住、接不全

> 实现前保留为驱动审计；修复后本页作根因记录。验收见 acceptance / acceptance-report。

## 用户可见现象

| 操作 | 实际 | 期望 |
|------|------|------|
| 主 agent 调用 DeepAgents `task` | 最多扁平 `type: tool`；Exec 无子树；前端常丢弃 `tool` | Exec 默认展开：前瞻三步 + nested tools + 状态 |
| 委派无「看三步」 | 模型可冒进 spawn | 缺 `look_ahead[3]` 等 → 硬拦截，SSE `failed` |
| Skill `context: fork` | 只返回 `subagent_config`，不真跑 | 过闸门后真 spawn；同一套 SSE |
| fork 经 `skill_discover_and_execute` | 通用分支读 `result` → **空壳 success** | 等待真结果或显式失败 |
| 子代理内部返工 | 用户看不见；若误拼进主回复则污染上下文 | 观测默认展开；主 `messages` 仅最终回报 |

## 复现步骤（当前）

```bash
# 1) 起 API + UI 后发一条需要多步隔离调研的任务（易触发 task）
# 2) 观察 SSE：是否只有 content / 扁平 tool，有无 step_type=subagent
curl -sN -X POST http://127.0.0.1:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"分别调研 A 与 B 两个独立问题并汇总"}],"session_id":"subagent-probe","stream":true}' \
  | head -n 80

# 3) UI：右侧 Exec — 期望（目标态）见 Subagent 节点与 ①②③；现状：无嵌套
```

Skill fork（代码路径）：

- `SkillExecutor.execute_in_subagent` 文档写明不创建 subagent  
- `ToolManager` 仅特判 `inline_bash`，`type == "subagent"` 无结果字段

## 根因（审计摘要）

### R1 — 流式层无子代理身份

- `SafeClawDeepAgent.stream` 只 yield 扁平 `{tool, content}`  
- 无 `parent_step_id` / `agent_name` / brief 字段 / start–end 生命周期  
- 多见 ToolMessage **结果**，少见 tool-call **意图**

### R2 — 前端未接 `tool`，Exec 无 `subagent`

- `chat-api.ts` 的 event union / switch 无 `tool`  
- `ExecutionStepType` 无 `subagent`；`parentId` 未从 SSE 接线  
- 默认展开合同不存在

### R3 — 无「看三步」机器闸门

- 无 `validate_spawn_brief`  
- 仅靠模型自觉 → 冒进委派无法 Fail Fast

### R4 — Skill fork 脚手架未接线

- `context: fork` → config dict only  
- `create_deep_agent` 未传自定义 `subagents=`  
- ToolManager 对 `type: subagent` 空壳 success

### R5 — 观测与隔离未产品化

- DeepAgents 对主线程隐藏子中间步（合理）  
- SafeClaw 未用 SSE/Exec 补齐 → 用户不可观测  
- PromptLogger 只挂主 agent；碰 `done` 时还有 `skill_names` 未定义债（`api/main.py`）

### R6 — 返工污染风险（防患）

- 若为「可观测」把 nested transcript 写入主 chat / 下一轮 messages，将违背双通道隔离  
- 本期必须在合同与测试中显式禁止

## 明确不在本主题

- Cursor IDE 式全类型全家桶（Plan/Bugbot 等）  
- Streamlit UI 对等改造  
- 修改 DeepAgents 上游包  
- Per-session skill 配置（见 [skills-activation](../skills-activation/)）  
