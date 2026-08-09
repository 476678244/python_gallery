# 辅助脚本

实现阶段补充可执行脚本路径；此处先约定用途与手工探针。

## 可观测性 Demo（无需服务）

**基于 prod 页面壳层**（Sidebar + Chat + IntelliJ Exec rail，tokens 对齐 `safeclaw-ui/demo.html` / `right-panel`），只重构 Execution Path 的 subagent 展示：

```bash
open docs/features/sub-agents/demo-observability.html
```

| 按钮 | 对应 |
|------|------|
| S1 合法委派 | 前瞻三步 + nested tools 默认展开；主 Chat 只有最终回报 |
| S2 缺三步拦截 | 硬闸门 `failed`，未 spawn |
| S3 返工再 spawn | 子上下文纠正可见；主线程重新 spawn，不回灌失败轨迹 |
| **STOP THE WORLD** | 一键冻结主/子代理与回放；`running`→`cancelled`；Exec 保留现场。快捷键 `Esc`。点「重置」解除 |
| **纠正方向** | 取消当前 subagent（`redirected`）；向 main 注入 `[USER_STEER] 要换个方向`；演示再看三步并新 spawn。快捷键 `R` |

## 拟议脚本（实现时落地）

| 脚本 | 用途 |
|------|------|
| `scripts/features/sub-agents/probe_sse_tree.sh` | POST `/chat/stream`，过滤 `execution_step`，检查 `subagent` / `parent_step_id` / `look_ahead` |
| `scripts/features/sub-agents/probe_isolation.py` | 跑一轮 spawn 后断言主 messages 无 nested transcript |
| `scripts/features/sub-agents/validate_brief_unit.sh` | 包装 `pytest` 指向 `spawn_brief` 单测 |

路径相对于仓库根；落地后与本表对齐。

## 手工：SSE 树探针

```bash
curl -sN -X POST http://127.0.0.1:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "messages":[{"role":"user","content":"用隔离子任务分别处理两件独立事并汇总"}],
    "session_id":"subagent-sse-probe",
    "stream":true
  }' | tee /tmp/subagent-sse.log | head -n 120
```

目标态检查（实现后）：

```bash
rg 'step_type.: .subagent|look_ahead|parent_step_id' /tmp/subagent-sse.log
```

## 手工：brief 校验（代码就绪后）

```bash
conda run -n safe_claw pytest test/deepagents/test_spawn_brief.py -q
```

## 手工：隔离抽检要点

1. 保存一轮 stream 的完整 SSE。  
2. 确认 nested `tool_call` 的 `content` 出现在观测事件中。  
3. 确认同一 `message_id` 的主 `content` / 后续 chat 请求 **没有**整段粘贴上述 nested content。  
4. Fail Fast：若观测为了「方便」把子轨迹写入主 messages → **验收失败**。  

## 与 skills-activation

子代理加载的 skills 必须尊重 `agent_config.enabled_skills`。过滤探针可复用：

- [../skills-activation/scripts.md](../skills-activation/scripts.md)  
