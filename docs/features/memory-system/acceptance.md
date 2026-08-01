# 验收标准

勾选表示已满足。驱动场景：`wiki/jargon` 已 ingest。

## A. 检索层

- [x] `GET /memory?search=101` → `total >= 1`，content 含「散户」或「边际」
- [x] `GET /memory?search=什么是101` → `total >= 1`（**中文问句**）
- [x] `GET /memory?search=你知道哪些黑话` → `total >= 1`
- [x] `GET /memory?search=皮夹克` → 命中黄仁勋词条
- [x] 非法 `layer=foo` → HTTP 400（不回归）

## B. Stream / 注入

- [x] 问「什么是101」时 SSE memory step `status=completed` 且命中数 ≥ 1（`test_chat_stream_zh_jargon_query_hits_memory_step`）
- [x] chips 或 `memories[]` 出现 101 / 散户相关摘要
- [x] 注入后的 LLM 回复 **不是**「大学导论课 / Route 101」为主结论（`memory-jargon-zh` TC-ZH-03）
- [x] 有命中时优先记忆（DeepAgent 合并 system memory + AUTHORITATIVE 护栏）

## C. UI / Slash

- [x] Memory 面板可见 jargon 词条（无 Porsche stub）— TC-ZH-05 / memory-panel
- [x] `/remember` 仍可用；`/memory` 命令在 slash 面板
- [x] badge/stats 来自 API（非硬编码 3）

## C2. 全局默认模型（DeepSeek）— 人工验收硬门槛

> DeepSeek V4 Flash **就是**全局默认模型选择（产品默认，不是验收临时切换）。

- [x] **DeepSeek V4 Flash 是全局默认**（`DEFAULT_MODEL` / `isDefault` / `/settings/models.default`）— 代码已对齐
- [ ] 点 **+ New Chat** → header + 输入框 chip **无需再选手动**即为 DeepSeek — **待 Human Accept**
- [x] `POST /sessions` 不传 `model` → `settings.model == deepseek-v4-flash`
- [x] E2E：`test/e2e/new-chat-default-model.spec.ts` **2 passed**（2026-08-01）

## D. 脚本与可重复性

- [x] `python scripts/memory/ingest_jargon_wiki.py` 可重复执行
- [x] `bash scripts/memory/verify_jargon_search.sh` 退出码 0
- [x] 文档 `docs/features/memory-system/` 与行为一致

## E. 有头 E2E

- [x] `npx playwright test memory-jargon-zh.spec.ts` 全绿（含 DeepSeek gated UI）
- [x] `deepseek-chat-memory.spec.ts` 绿

有头复验：

```bash
cd test/e2e && HEADED=1 npx playwright test memory-jargon-zh.spec.ts --retries=0
```

## F. Fail Fast（人工常驻，非可选）

> 系统给本人自用：出错必须立刻暴露，禁止「怕吓到用户」式静默兜底。

- [x] 模型路径禁止静默 fallback（见 [human-non-accept-report](./human-non-accept-report-2026-08-01.md) NA-04）
- [x] `/settings/model` 缺失/空/未知 id → 抛错并 UI 可见，不 invent 默认
- [x] New Chat / 发消息在全局模型未就绪时 **拒绝执行**

## 明确不验收（本期）

- 默认开启语义向量（可选：`MEMORY_REBUILD_VECTORS=1` + `enable_vector_search`）
- 自动从 Obsidian 监听文件变更
- 完美 NER
