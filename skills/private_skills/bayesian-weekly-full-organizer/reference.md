# Reference — detailed conventions

Layered detail for `bayesian-weekly-full-organizer`. Read the section you need; SKILL.md has the overview.

---

## 1. 九分法 source split (Step 2)

Split the OCR 底本 into `assets/sources/26wXX/` with this mapping. Normalize garbled CJK glyphs
(⼈→人, ⼤→大, ⽉→月, etc.) while transcribing.

| File | Chapter / content |
|------|-------------------|
| `26wXX-00-index.md` | split map + image-archive note + link to charts-index |
| `26wXX-01-pattern.md` | 一、#模式识别 |
| `26wXX-02-world-news.md` | 二、本周世界要闻 |
| `26wXX-03-dollar-order.md` | 三、#美元秩序 |
| `26wXX-04-consensus.md` | 四、显著变化的 #西方共识 |
| `26wXX-05a-equities-market.md` | 五、美股（流动性/自下而上/走势） |
| `26wXX-05b-equities-earnings.md` | 五、美股（季报大全） |
| `26wXX-05c-us-macro.md` | 五、美国国内基本面 |
| `26wXX-06-a-shares.md` | 六、A股市场 |
| `26wXX-07-laolao.md` | 七、南老师收尾原文 + laolao 推演 |

Each source file: keep 南老师 verbatim text, fix image refs to **real hash filenames** (not invented semantic
names), and if the OCR has no chart for a point, note `OCR 底本此处无独立配图` rather than inventing one.

---

## 2. Per-chapter 渗透 mapping (Step 4)

Two coexisting structures in 总本:

- **A. Top prose block** under `## 2026`: one narrative block per week (`### 26wXX · 一句话主题`), seven
  chapters in prose, embedding ⭐ key charts. Newest week's block goes at the very top. Backfill any skipped
  week (e.g. 26w24) inline where relevant, marked `（回填 26w24：…）`.
- **B. Sub-section timelines** (in the long master母版 block): infiltrate `- **26wXX**：…` at the TOP of each
  relevant sub-node.

When a 完整版 arrives, prioritize building/refreshing the top prose block (A). When only a 摘要版 arrives,
infiltrate into both A and B per this table:

| 章节 | 渗透要点 |
|------|---------|
| 一、#模式识别 | top of chapter, after `现象重复→…` |
| 二、伊朗/以色列/美国/俄乌/中东其他/日韩/亚洲 | each sub-node: add `- **26wXX**：…` on top |
| 三、美元指数 | update the "26wXX~..." range |
| 三、美债二级 / 数字货币 / 黄金 | top `- **26wXX**：…` |
| 四、西方共识 | top `- **26wXX**：…` (if none this week, say so explicitly) |
| 五、机构仓位/ETF flow | update to this week's latest values |
| 五、全市场扫描 | add this week's Factset row on top |
| 五、消费/半导体季报表 | insert new earnings row(s) |
| 五、走势/共识/AI | top `- **26wXX**：…` |
| 六、A股基本面 / 走势 / 资金面 | top `- **26wXX**：…` |
| 七、laolao推演 | refresh 贝叶斯更新结论 + 下周验证信号表 |

Chart embed: `![指标 · 时间范围 · 核心数字/结论](../../../assets/pictures/26wXX/文件名.jpg)` placed right after
its analysis paragraph (not as a standalone section).

---

## 3. 总演化线 table (Step 5)

Append one row per new week (newest at the bottom of the table, matching existing order):

```markdown
| 26wXX | 一句话核心模式 | 本周主导力量 | 从上周到本周，哪个假设被证实/证伪 |
```

In the 半年切片 the same table only keeps rows inside the window.

---

## 4. 半年切片 rolling pruning (Step 6)

Window = rolling ~26 weeks. SOP when advancing to a new week:

1. Insert the new week's prose block at top (mirror 总本).
2. Add new 总演化线 row(s); table keeps only in-window weeks.
3. **Prune**: remove out-of-window weeks' sub-entries from each chapter timeline.
4. **Breadcrumb**: at the end of each pruned sub-section keep one line picking 2–4 key nodes:
   `*（更早脉络：25w51 … → 25w50 … → 见总本）*`
5. **Window edge**: cross-window range entries (e.g. `25w53~w50`) are KEPT and labeled `（窗口边缘）`.
6. Update frontmatter `window:` and `date:`, and the intro window line.
7. Never delete history — full history always lives in 总本.

---

## 5. Atom card upgrade (Step 7)

Pick the highest-signal facts (typically 5–8). Use atom templates in templates.md. Conventions:

- `source: 26wXX-bayesian-weekly-report-full` (or `-summary` for 摘要版), `author: nan-tian`.
- Filenames: lowercase-hyphen, end with `-26wXX`, e.g. `retail-no-fear-only-greedy-101-26w25.md`.
- Type → folder: market events → `events/`, data points → `data/`, insights/金句 → `quotes/`.
- Always separate **事实 (Facts)** from **解读 (Interpretation)**; add a 费曼式解释 and a 验证清单.
- Cross-link reciprocally to prior related atoms and to the 总本.
- After adding: bump category counts/headers in `index.md` (the catalog is canonical; its event/data counts
  match real files) and in `wiki/atoms/README.md` (uses its own self-consistent scheme — increment by the
  same deltas).

---

## 6. Reading note (Step 8)

Copy `wiki/laolao/reading-template.md`. Structure: 读前准备（回验上周「下周关注」）→ 模式识别 → 交换(diff焦点)
→ 比较(最大贝叶斯更新) → 反复(追问) → 金句 → 下周关注 → 吸收度自评 → 南添元模式观察.

If the note is **prep for tonight's livestream** (听直播准备), add a "今晚直播：要带着听的清单 🎧" table (听点 /
为什么重要 / 留意南老师怎么说) and frame open questions to bring into the stream. After the stream, fill the
推演 + 金句 sections with his live judgment, and use his "下周看什么" as next week's 读前准备.

If a week was skipped (no reading note), point 读前准备 at the most recent existing note.

---

## 7. #模式识别 thread (Step 9)

`wiki/laolao/pattern-recognition-thread.md` is a cumulative standalone index of 南老师's pattern recognitions.

- **By-week table** (newest on top): `| 周次 | 模式识别一句话 | 主导力量/演化 | 回链 |`.
- **元模式 chains**: group recurring motifs (流动性洪水→单向 / 买单的人 / 死亡走势·TACO / 半导体估值) and append
  the new week to the relevant chain.
- One-line-only principle: full text/charts stay in 总本; here only a sentence + backlink.
- Keep falsifying patterns too.

---

## 8. Catalog + log (Step 10)

- `wiki/laolao/index.md`: add the new week to 周报阅读记录 table; note new 校准母版 if a 完整版 arrived.
- `index.md` (root): add atom entries; bump category headers + `…张卡片统计`.
- `log/YYYY-MM.md`: append entries under the right type section (`ingest` for the PDF processing, `create` for
  new pages/atoms). Bump that section's `(n)` count, the 本月概览 table, and the `共 N 条操作` header. Use the
  documented format:
  ```
  ## [YYYY-MM-DD] ingest | Source Title
  - what was processed
  - pages updated
  ```

---

## 9. MinerU technical notes

- Env: conda `safe_claw`; may need `required_permissions: ["all"]` (multiprocess rendering).
- Script: `…/pdf-to-markdown/scripts/run.py "<input.pdf>" "<output_dir>" --lang ch`.
- Output: `<output_dir>/<pdf_filename>/auto/<pdf_filename>.md`; images under `auto/images/` (hash-named).
- A 133-page PDF ≈ 120 s. Quote paths with `#`, `，`, spaces.
- **Inventory raw/ with shell, not Glob**: `ls -la raw/` / `find raw -name "*.pdf"`. The full-width `，` and
  `#` in filenames make `Glob "**/*.pdf"` silently miss them. Locate an extracted md with
  `ls /tmp/pdf-out-*/*/auto/*.md`.
- **Batch backfill extractions**: loop several gap weeks in one backgrounded shell (each ≈ 3 min); poll the
  terminal file for an `ALL_DONE` sentinel instead of blocking.

---

## 10. 子时间线回溯回填 (backfill from earlier 完整版)

**When**: a sub-node timeline stops short because the latest 完整版's retrospective only traced that sub-actor
back to week N — but the topic started earlier, and each earlier week's own 完整版 still records that actor's
weekly move. (SKILL.md "Secondary operation" has the checklist; this is the detail.)

### Where the per-week sub-actor line lives
In each 完整版, chapter 二 → `焦点 / 中东战争` (early weeks) or the split `伊朗 / 以色列 / 美国` sub-nodes
(later weeks) carry a recurring tracking stanza:

```
时限：本周通行霍尔木兹海峡的船只（国家）越来越多…
背景：日韩在内的能源下游国家的库存不断消耗…
伊朗：继续坚持对等反击；言论上继续强调"高油价高通胀是人质"
```

The later all-weeks retrospective usually keeps only the headline 中东 narrative and **drops these per-actor
stanzas** — that's exactly the increment to recover.

### Method
1. **Gap map**: list the sub-node's current earliest week vs the topic's real start; enumerate which gap weeks
   have a 完整版 底本 in `raw/` (shell `ls`). Note 完整版-missing weeks.
2. **Extract** each gap week's 完整版 (batch, background).
3. **Mine** per week: the sub-actor's own line(s) from 焦点/sub-node + the 中东/topic timeline. Keep verbatim;
   normalize garbled CJK.
4. **Insert** `- 26wXX：…` rows below the existing earliest row (descending: newest backfill week on top,
   war-start week at the bottom, e.g. `…26w13 → 26w12 → 26w11 → 26w10 → 26w9 周末`).
5. **De-dup**: if 「中东（其他）」/another sub-node already carries the same fact, write the essence + 「详见
   …」 rather than duplicating a long paragraph.
6. **Gap weeks** with no 底本 (no 完整版 nor 摘要版): do not fabricate. State it in the provenance note as
   `26wYY 该周无完整版/摘要版底本，暂缺`.
7. **Provenance note** right under the backfilled list (template in templates.md): say the range was 回填 from
   各周完整版「焦点·中东战争」, that it is 南老师原文 (non-Agent), and which week is 暂缺.
8. **Mirror** to 半年切片 if backfilled weeks are in-window (they often are, for a months-long topic).
9. **Log** as `update` — no new published week, so it is not an `ingest`.

### Sanity bar
Backfill should reach the topic's true origin (e.g. war start 26w9/26w10) or the earliest available 底本.
A good backfill often surfaces an **earlier-than-recorded signal** (the retrospective compresses; the
contemporaneous 完整版 is more granular) — flag such finds explicitly to the user.
