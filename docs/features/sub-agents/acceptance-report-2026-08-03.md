# Sub-agents — Acceptance Report (2026-08-03)

## Verdict

**Automated chain PASS（A–D2 / F）。** Evidence pack: [evidence/](./evidence/README.md). Phase C（E fork）与 skills-activation 回归未纳入。

## Evidence gates

| Gate | Result | Artifact |
|------|--------|----------|
| pytest spawn_brief + SSE gate helpers | **PASS (10)** | [evidence/logs/pytest-spawn-brief-sse.txt](./evidence/logs/pytest-spawn-brief-sse.txt) |
| Playwright `sub-agents.spec.ts` S1/S1b/S3 | **PASS (3)** | [evidence/logs/playwright-sub-agents.txt](./evidence/logs/playwright-sub-agents.txt) |
| Gate case matrix (机读) | valid OK / 4 REJECT | [evidence/logs/spawn-brief-gate-cases.json](./evidence/logs/spawn-brief-gate-cases.json) |
| React DOM snapshot | look_ahead=3, marker isolation | [evidence/logs/s1-react-dom.json](./evidence/logs/s1-react-dom.json) |
| Demo S2 gate DOM | fail-fast err visible | [evidence/logs/s2-gate-dom.json](./evidence/logs/s2-gate-dom.json) |
| Screenshots S1/S1b/S2/S3 | archived | [evidence/screenshots/](./evidence/screenshots/) |

## What landed

1. **Hard gate**: `safe_claw/core/deepagents/spawn_brief.py` — Fail Fast，缺字段不 spawn  
2. **SSE 子树**: `execution_step` `subagent` + nested `tool_call` + `parent_step_id`  
3. **Exec UI**: 默认展开 look_ahead×3；嵌套工具；闸门失败可见  
4. **双通道**: nested marker 仅在 Exec；主气泡仅 summary  
5. **产品控件**: Exec 头 **纠正方向 / Halt**（`[USER_STEER]` 短信号）

## Explicitly not accepted this round

- Skill `context: fork` 真执行（Phase C）  
- 拦截 DeepAgents 上游 `task` 在运行前强制 abort（观测层已 `status=failed`）  
- skills-activation 全量回归  
- 有头人工视觉复验（可选）

## Human spot-check (optional)

- [ ] `HEADED=1 FRONTEND_URL=http://127.0.0.1:3000 npx playwright test sub-agents.spec.ts --retries=0`
- [ ] `open docs/features/sub-agents/demo-observability.html` → S2 闸门红框 + Halt/Steer

If any human item fails, open `human-non-accept-report-*.md` with NA-id.
