# E2E 用例（含有头）

## 前置

- UI `http://localhost:3000`，API `http://localhost:8000`
- 已执行 jargon ingest（见 [scripts.md](./scripts.md)）
- Playwright：`test/e2e/`
- **有头**：`HEADED=1`（见 `test/e2e/playwright.config.ts`：`headless: process.env.HEADED !== "1"`）

## 规格文件（待实现 / 已有）

| 文件 | 状态 | 说明 |
|------|------|------|
| `test/e2e/memory-jargon-zh.spec.ts` | **已落地** | 本主题黄金路径（TC-ZH-01…05） |
| `test/e2e/new-chat-default-model.spec.ts` | **已落地** | New Chat 继承全局默认 DeepSeek（C2 / 人工硬门槛） |
| `test/e2e/memory-panel.spec.ts` | 已有 | 面板可见 + `/remember` |
| `test/e2e/deepseek-chat-memory.spec.ts` | 已有 | DeepSeek 显式 remember 召回 |
| `test/e2e/memory-safety-sessions-smoke.spec.ts` | 已有 | API 结构 smoke |

---

## TC 清单 — `memory-jargon-zh.spec.ts`

### TC-ZH-01 API：中文问句检索

1. `GET /memory?search=什么是101&limit=5`  
2. **期望**：`total >= 1`；任一条 content 匹配 `/101|散户|接盘/`  

### TC-ZH-02 API：元问题黑话

1. `GET /memory?search=你知道哪些黑话&limit=5`  
2. **期望**：`total >= 1`；命中含「黑话」或 `Jargon` 或多条 slang 标题  

### TC-ZH-03 有头 UI：什么是101

1. `HEADED=1` 打开首页，确保 session  
2. （可选）侧栏选 DeepSeek V4 Flash；否则当前模型  
3. 发送：`什么是101`  
4. 等待 assistant 气泡  
5. **期望**：  
   - 文本匹配投资义项（`散户` 或 `接盘` 或 `边际`）  
   - **不**以「大学课程」「经济学导论」「Highway 101」为唯一义项  
6. （有头人工）Exec → Memory retrieval chips 显示命中数 ≥ 1  

### TC-ZH-04 有头 UI：你知道哪些黑话

1. 发送：`你知道哪些黑话？请列举记忆里的投资黑话`  
2. **期望**：回复出现至少 2 个已知词条名（如 `懂王`/`TACO`/`皮夹克`/`101`/`老钱` 中的任意组合）  

### TC-ZH-05 回归：面板仍可见 ingest 内容

1. 打开 Memory rail  
2. **期望**：`data-testid=memory-panel` 可见；搜索或列表中可见 `Investment Jargon` 或 `101`  

---

## 有头运行命令

```bash
# 终端 1/2：API + UI 已启动
export NO_PROXY=127.0.0.1,localhost,api.deepseek.com
unset ALL_PROXY all_proxy HTTP_PROXY HTTPS_PROXY

# ingest + verify
python scripts/memory/ingest_jargon_wiki.py
bash scripts/memory/verify_jargon_search.sh

# 有头 E2E（slowMo 便于肉眼看 Memory step）
cd test/e2e
HEADED=1 npx playwright test memory-jargon-zh.spec.ts --retries=0
```

DeepSeek 黄金（gated）：

```bash
cd test/e2e
HEADED=1 npx playwright test deepseek-chat-memory.spec.ts memory-jargon-zh.spec.ts --retries=0
```

Skip DeepSeek：`SAFECLAW_E2E_SKIP_DEEPSEEK=1`

## 录屏 / 截图约定

- 失败时 Playwright 已截图到 `test/e2e/test-results/`  
- 有头验收通过后，可选保存：`test-results/memory-jargon-zh-pass.png`（用例内 `page.screenshot`）
