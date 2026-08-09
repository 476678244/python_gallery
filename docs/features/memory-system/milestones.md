# 测试里程碑

每个里程碑：**准出条件全绿** 才进入下一阶段。

## M0 — 基线冻结（已完成）

| 检查 | 命令 / 标准 |
|------|-------------|
| API memory 契约 | `pytest test/api/test_memory.py -q` |
| 生命周期单测 | `pytest test/unit/test_memory_lifecycle.py -q` |
| Memory 面板 E2E | `npx playwright test memory-panel.spec.ts` |
| DeepSeek 召回（英文/显式 remember） | `npx playwright test deepseek-chat-memory.spec.ts`（需 key） |

**准出**：上表全绿；jargon 已可 ingest（见 scripts）。

---

## M1 — 中文分词检索（对应 Phase A）

| # | 类型 | 用例 | 准出 |
|---|------|------|------|
| M1.1 | unit | `什么是101` search → 含 `101` 词条 | assert content/title |
| M1.2 | unit | `介绍一下皮夹克` → 黄仁勋词条 | |
| M1.3 | api | `GET /memory?search=什么是101` `total>=1` | |
| M1.4 | api | `search=101` 行为不回归 | |

**准出**：M1.* 全绿。

---

## M2 — 元问题（对应 Phase B）

| # | 类型 | 用例 | 准出 |
|---|------|------|------|
| M2.1 | unit/api | `你知道哪些黑话` → hits≥1 且含 jargon/黑话词典 | |
| M2.2 | unit/api | `你有哪些记忆` → hits≥1 或专用 list 注入非空 | |
| M2.3 | api | ingest metadata `collection=jargon` 可被策略使用 | |

**准出**：M2.* 全绿。

---

## M3 — 注入护栏（对应 Phase C）

| # | 类型 | 用例 | 准出 |
|---|------|------|------|
| M3.1 | api stream | 问「什么是101」→ memory step `sub` 含 `N relevant` 且 N≥1 | 非假 3 |
| M3.2 | api stream | chips/memories 含「散户」或 `101` | |
| M3.3 | 有头 E2E | Exec/回复可见领域解释（见 e2e.md TC-ZH-03） | |

**准出**：M3.1–M3.2 自动化绿；M3.3 有头人工或 Playwright headed 绿。

---

## M4 — 有头黄金路径（对应 Phase D）

| # | 类型 | 用例 | 准出 |
|---|------|------|------|
| M4.1 | script | `ingest_jargon_wiki.py` 幂等/可重复 | exit 0 |
| M4.2 | script | `verify_jargon_search.sh` | exit 0 |
| M4.3 | headed e2e | `HEADED=1` `memory-jargon-zh.spec.ts` | 全绿 |
| M4.4 | gated | DeepSeek：`什么是101` 回答含散户/接盘语义 | key 存在时必过 |

**准出**：M4.1–M4.3 必过；M4.4 有 key 时必过，无 key 则 skip 并记录。

---

## M5 — 可选向量（对应 Phase E）

| # | 类型 | 准出 |
|---|------|------|
| M5.1 | unit | 开启 vector 后近义句可命中 |
| M5.2 | unit | 关闭时不谎报 `match_type=semantic` |

**准出**：仅当产品决定默认开启时强制；否则可选。

---

## 回归门禁（每阶段结束）

```bash
export NO_PROXY=127.0.0.1,localhost,api.deepseek.com
unset ALL_PROXY all_proxy HTTP_PROXY HTTPS_PROXY SOCKS_PROXY socks_proxy

conda activate safe_claw
pytest test/api/ test/unit/test_memory_lifecycle.py -q

bash scripts/memory/verify_jargon_search.sh

cd test/e2e && npx playwright test \
  memory-panel.spec.ts \
  memory-safety-sessions-smoke.spec.ts \
  slash-commands.spec.ts \
  model-slash-switch.spec.ts \
  skill-autocomplete.spec.ts \
  deepseek-chat-memory.spec.ts \
  --retries=0
```

### 最近一次回归记录（2026-08-01 · 完整开发收尾）

| 套件 | 结果 |
|------|------|
| `pytest test/api/` + `test_memory_lifecycle.py` | **27 passed** |
| `scripts/memory/verify_jargon_search.sh` | **OK** |
| E2E：`memory-jargon-zh` + memory-panel + slash + model + deepseek | **21 passed** |

Phase 完成度：A/B/C/D 完成；E 提供 `rebuild_vector_index` + `MEMORY_REBUILD_VECTORS=1`（默认仍关）。
