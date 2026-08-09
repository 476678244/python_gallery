# 问题：黑话已写入，中文问句召不回

## 用户可见现象（UI）

模型为 Qwen3.5 9B（或任意当前模型）时：

| 用户问 | 实际回答 | 期望 |
|--------|----------|------|
| 你有哪些记忆？ | 声称无特定记忆，只谈 workspace/skills | 能列出 / 摘要已 ingest 的黑话或至少承认有 jargon 记忆 |
| 你知道哪些黑话？ | 通用互联网黑话，非投资词典 | 命中 `wiki/jargon` 词条（懂王/101/TACO…） |
| 什么是101？ | 大学导论课 / 公路 101 | **散户 / 边际接盘流动性**（jargon `101.md`） |

同时 Memory 面板与 `GET /memory` 中 **已有** 47 篇 jargon 词条（ingest 成功）。

## 复现步骤

```bash
# 1) 确认词条在库（应 hits>=1）
curl -sG 'http://localhost:8000/memory' --data-urlencode 'search=黑话' --data-urlencode 'limit=3'

# 2) 精确问句（当前失败：hits=0）
curl -sG 'http://localhost:8000/memory' --data-urlencode 'search=什么是101' --data-urlencode 'limit=3'

# 3) 对照：单独 token（当前成功：hits>=1）
curl -sG 'http://localhost:8000/memory' --data-urlencode 'search=101' --data-urlencode 'limit=3'

# 4) UI：选任意模型 → 问「什么是101」→ 看 Exec 面板 Memory step chips / 回复内容
```

## 根因

### R1 — 检索器只按空白分词（主因）

`MemoryRetriever.keyword_search`：

1. 整句 `query.lower()` 子串匹配 → `什么是101` 不会出现在正文里  
2. `query.split()` 按空格切词 → 中文整句是 **一个 token**，无法拆出 `101`  
3. 单独搜 `101` / `散户` / `黑话` 能命中  

诊断结果（当时）：

```
'101'        -> 3 hits
'什么是101'   -> 0 hits
'黑话'       -> 3 hits
'你知道哪些黑话' -> 0 hits
```

### R2 — 元问题无专用策略

`你有哪些记忆` / `你知道哪些黑话` 与词条正文关键词重叠少，即使修好分词，仍需要：

- 问句意图识别（list-memories / list-jargon），或  
- 查询改写（抽取「黑话」「记忆」→ 搜 collection / tags），或  
- 注入 jargon index 摘要记忆

### R3 — 模型侧（次要）

即便注入了 system memory context，弱模型可能忽略；需：

- 更强的 system 指令（优先使用 Relevant memories）  
- Exec 面板展示真实命中，便于有头验收  
- DeepSeek 路径作黄金验收（已有 `deepseek-chat-memory.spec.ts`）

## 不在本问题范围

- 向量检索默认关闭（增强项，见 plan Phase C）  
- Obsidian 语料本身对错（以 wiki 文件为准）  
- Session 聊天历史 ≠ Memory 层（两套存储）
