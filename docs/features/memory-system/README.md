# Memory System

SafeClaw 长期记忆体系：四层文件存储、聊天检索注入、Slash 写入、UI 面板，以及以 **投资黑话词典** 为驱动场景的中文检索增强。

| 项 | 值 |
|----|-----|
| Feature ID | `memory-system` |
| 驱动案例 | 「什么是101」→ 投资黑话「散户/接盘」而非大学导论 |
| 存储根 | `~/Downloads/safe_claw_worksapce/workspace/memory/` |
| 行为说明 | [safe_claw/Docs/MEMORY.md](../../../safe_claw/Docs/MEMORY.md) |
| **状态** | Phase A–D 能力已落地；**完整人工验收未关闭**（见 Non-Accept：New Chat 默认 DeepSeek / C2） |
| 使用语境 | **个人自用** → Fail Fast，禁止静默 fallback（NA-04） |

## 能力矩阵

| 能力 | 状态 |
|------|------|
| 四层存储 + API CRUD/搜索 | 已落地 |
| `/chat/stream` 真检索 + prompt 注入 + 阈值写入 | 已落地 |
| UI Memory 面板 + `/remember` `/memory` | 已落地 |
| 中文问句分词（`什么是101`） | 已落地 |
| 元问题 inventory（`你知道哪些黑话`） | 已落地 |
| Prompt 护栏 + DeepAgent system 合并 | 已落地 |
| 有头/无头 E2E `memory-jargon-zh.spec.ts` | 已落地 |
| `enable_vector_search` 默认 | 关；`rebuild_vector_index` + ingest 可选重建 |

## 文档索引

1. [problem.md](./problem.md) — 失败复现与根因  
2. [plan.md](./plan.md) — 分阶段开发计划  
3. [milestones.md](./milestones.md) — 测试里程碑  
4. [acceptance.md](./acceptance.md) — 验收标准（含 C2 全局默认 DeepSeek）  
5. [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md) — 验收报告  
6. [human-non-accept-report-2026-08-01.md](./human-non-accept-report-2026-08-01.md) — **人工不接受过程报告**  
7. [e2e.md](./e2e.md) — 有头 E2E 用例  
8. [scripts.md](./scripts.md) — ingest / 验证脚本  

## 快速验证

```bash
bash scripts/memory/verify_jargon_search.sh
cd test/e2e && npx playwright test memory-jargon-zh.spec.ts --retries=0
# 有头：HEADED=1 npx playwright test memory-jargon-zh.spec.ts --retries=0
```

## 相关代码

| 区域 | 路径 |
|------|------|
| Manager / context | `safe_claw/core/memory/manager.py` |
| Retriever（CJK + inventory） | `safe_claw/core/memory/retriever.py` |
| DeepAgent system 合并 | `safe_claw/core/deepagents/official_integration.py` |
| Chat 接线 | `api/main.py` |
| E2E | `test/e2e/memory-jargon-zh.spec.ts` |
| 语料 | `obsidian_wiki_investment/wiki/jargon` |
