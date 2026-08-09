# 脚本

Phase 0 以文档 + Demo 为主。实现后用 API / pytest / Playwright；下列为建议核对命令。

## 快速核对（实现后）

```bash
# 非法 mode → 期望 400
curl -s -o /tmp/mode-bad.json -w "%{http_code}\n" -X POST http://127.0.0.1:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}],"mode":"nope","stream":true}'

# Ask mode 流（实现后应无 write 工具成功）
curl -sN -X POST http://127.0.0.1:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"只读解释：1+1"}],"session_id":"mode-ask","mode":"ask","stream":true}' \
  | head -n 40
```

## 建议新增（Phase A+）

| 脚本 / 测试 | 用途 |
|-------------|------|
| `test/api/test_agent_modes.py` | mode 缺省 / 非法 / ask 工具集 |
| `test/e2e/agent-modes.spec.ts` | S1–S4 |
| Demo `demo-modes.html` | 视觉合同；无需后端 |

## Demo

```bash
open docs/features/agent-modes/demo-modes.html
```

## 现状对照（无 mode）

```bash
# 今日请求体无 mode；一律全 agent
rg -n "allow_write" api/main.py safe_claw/core/deepagents/
rg -n "SLASH_COMMANDS" -A 80 safeclaw-ui/my-app/src/features/chat/slash/commands.ts
```
