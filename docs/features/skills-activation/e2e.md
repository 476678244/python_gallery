# E2E 用例（含有头）

## 前置

- UI `http://localhost:3000`，API `http://localhost:8000`  
- 全局模型 DeepSeek（New Chat 继承）  
- Playwright：`test/e2e/`  
- 有头：`HEADED=1 npx playwright test <spec> --retries=0`

## 规格文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `skills-activation.spec.ts` | **已绿** | 本主题黄金路径 S1–S3 |
| `skills-path-activation.spec.ts` | 已有 | T5 已断言 SSE `skills_loaded`（无 ljg） |
| `skill-tree-*.spec.ts` | 已有 | 树/持久化回归 |
| `skill-autocomplete.spec.ts` | 已有 | `/skill` 与 enabled 一致 |

---

## S1 — Persist / reload / loaded list

1. API 或 UI：只启用 `flow_coding_testing`（+ 可选 1 个对照）  
2. 确认 `agent_config.enabled_skills`  
3. 硬刷新 → 树仍仅这些 on  
4. New Chat → 问：「列出当前加载进 agent 的 skills」  
5. **期望**：与 enabled 一致；不含已关集合  

## S2 — Disable folder → tools cannot see

1. 禁用 Ljg Skills 文件夹；启用一个 private skill  
2. 要求模型用 skill 列表工具 / 说明是否有 `ljg-roundtable`  
3. **期望**：无 ljg；SSE `skills_loaded` 无 ljg  

## S3 — Slash + 领域 skill

1. 启用一明确 skill（如 `flow_coding_chrome_cdp` 或 `pptx`）  
2. `/skill` 选中 → 发需该 skill 的任务  
3. **期望**：loaded 含该 skill；关掉后 autocomplete 消失且不可执行  

## 有头复验

```bash
cd test/e2e && HEADED=1 npx playwright test skills-activation.spec.ts --retries=0
```
