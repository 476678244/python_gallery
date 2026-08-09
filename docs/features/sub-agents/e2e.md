# E2E 用例（含有头）

## 前置

| 项 | 值 |
|----|-----|
| UI | `http://localhost:3000`（S1 React；可仅跑 Demo/API） |
| API | `http://localhost:8000` |
| Playwright | `test/e2e/` |
| 有头 | `HEADED=1 npx playwright test <spec> --retries=0` |

## 规格文件

| 文件 | 覆盖 |
|------|------|
| `test/e2e/sub-agents.spec.ts` | S1（React + mock SSE）、S1b（Demo HTML）、S2（闸门 API/单元）、S3（隔离断言） |
| `test/deepagents/test_spawn_brief.py` | 硬闸门单元 |
| `test/api/test_subagent_sse.py` | SSE 合同 / `skill_names` |

## 验收映射

| 用例 | acceptance | 断言要点 |
|------|------------|----------|
| S1 | C 前端默认展开 | Exec DOM：`data-testid=subagent-block`、三条 `look_ahead`、nested tool |
| S1b | Demo 合同 | `demo-observability.html` S1 回放后同上结构 |
| S2 | A 硬闸门 | `validate_spawn_brief` 拒；或 SSE `status=failed` + 缺字段 |
| S3 | D 不污染 | mock 流结束后主气泡无 nested `web_search` 长正文 |

## S1 — React Exec（mock SSE，不依赖真 LLM）

1. `page.route('**/chat/stream', …)` 注入含 `subagent` + nested `tool_call` 的 SSE  
2. New Chat → 发任意短消息 → 打开 Exec  
3. **期望**：
   - `[data-testid="exec-step-subagent"]` 可见  
   - `[data-testid="look-ahead-item"]` count = 3  
   - `[data-testid="exec-step-nested-tool"]` 可见  
   - 主区 assistant 文本 **不含** nested tool 全文（如 `NESTED_TOOL_BODY_MARKER`）

## S1b — Demo HTML 合同

```bash
cd test/e2e && npx playwright test sub-agents.spec.ts -g "S1b"
```

对 `docs/features/sub-agents/demo-observability.html`：点 S1 → 断言 Exec 子块与 Halt/Steer 在 panel head。

## S2 — 硬闸门

- pytest：`look_ahead` 2 条 / 空 `expected_output` / 未知 agent → `ValueError` 含字段名  
- （可选）stream mock：`status=failed` 的 subagent step 在 Exec 可见

## S3 — 隔离

同 S1 mock：assistant 气泡不含 `NESTED_TOOL_BODY_MARKER`；观测事件可含该 marker。

## 有头复验

```bash
# Prefer 127.0.0.1 if proxy breaks localhost
export NO_PROXY='*' FRONTEND_URL=http://127.0.0.1:3000
cd test/e2e && HEADED=1 npx playwright test sub-agents.spec.ts --retries=0
cd ../.. && NO_PROXY='*' PYTHONPATH=. conda run -n safe_claw pytest \
  test/deepagents/test_spawn_brief.py test/api/test_subagent_sse.py -q
```
