# 脚本

路径约定：仓库根下 `scripts/memory/`（本 feature 专用）。

| 脚本 | 用途 |
|------|------|
| [ingest_jargon_wiki.py](../../../scripts/memory/ingest_jargon_wiki.py) | 将 Obsidian jargon 目录写入 SafeClaw Memory |
| [verify_jargon_search.sh](../../../scripts/memory/verify_jargon_search.sh) | 验收检索问句（含中文） |

## ingest_jargon_wiki.py

**输入目录（默认）**

`/Users/nicole/workspace/github/a476678244/obsidian_wiki_investment/wiki/jargon`

**行为**

- 遍历 `*.md`，`POST /memory`
- content 前缀：`[Investment Jargon Wiki] {title}` + `source: wiki/jargon/{file}`
- `importance: 0.92`
- `metadata.collection = jargon`，`source = obsidian_wiki_investment`
- keywords：stem、title 分词、`jargon`、`investment`

**用法**

```bash
conda activate safe_claw
export NO_PROXY=127.0.0.1,localhost
# 可选：JARGON_DIR=... API=http://localhost:8000
python scripts/memory/ingest_jargon_wiki.py
```

**注意**

- `max_active_memories` 默认 20 → 大量词条会进入 dormant；**跨层 search 仍应命中**
- 重复执行会新增条目（非 upsert）；验收前如需干净库，手动清理 `workspace/memory/` 或接受重复后靠 consolidate

## verify_jargon_search.sh

对下列 query 断言 `total >= 1`（Phase A/B 完成后应全过；**当前** `什么是101` / `你知道哪些黑话` 会失败，用于红灯驱动）：

| Query | 最低期望 |
|-------|----------|
| `101` | ≥1 |
| `什么是101` | ≥1 （Phase A） |
| `黑话` | ≥1 |
| `你知道哪些黑话` | ≥1 （Phase B） |
| `皮夹克` | ≥1 |

```bash
bash scripts/memory/verify_jargon_search.sh
echo $?   # 0 = pass
```

## 一键演示（文档用）

```bash
python scripts/memory/ingest_jargon_wiki.py && bash scripts/memory/verify_jargon_search.sh
```
