---
name: bayesian-weekly-full-organizer
description: >-
  Use this skill to ingest a 南老师/laolao 贝叶斯事件 weekly report PDF (完整版 or 摘要版) into the
  investment wiki and maintain the "自组完整版" system. It extracts the PDF via MinerU, splits it into
  thematic sources, archives all charts, infiltrates ("渗透") the new week into the master file
  weekly-full-all_weeks_all_years.md following a fixed 7-chapter structure, syncs the rolling half-year
  slice with pruning, upgrades key bayes facts into atom cards, builds a 交换·比较·反复 reading note, and
  maintains the #模式识别 thread. Also covers a secondary operation — 子时间线回溯回填: extending a sub-section
  timeline (伊朗/以色列/美国/… ) backward by mining earlier weeks' 完整版 PDFs. Trigger on requests like
  "整理完整版", "周报渗透", "跟踪更新周报", "贝叶斯周报", "weekly-full 更新", "南老师/laolao 周报",
  "回溯/追述子时间线", "用 Raw 材料构建更多 weeks", "回填某子节", or when a new "贝叶斯事件，周报" PDF appears.
---

# 贝叶斯事件周报 · 自组完整版整理 (laolao system)

## What this is

A repeatable practice for following 南老师 (Zonghan/laolao) weekly bayes-event reports and maintaining a
self-organized "完整版" knowledge system inside the Obsidian investment wiki. Each new PDF (full or summary)
is turned into structured, cross-linked, time-stamped knowledge that stays consistent week over week.

**Target wiki repo**: `obsidian_wiki_investment/` (this skill assumes that layout). Always re-read its
`AGENTS.md` first — it is the authoritative schema; this skill is the operational SOP layered on top.

## Files this practice maintains

| File | Role |
|------|------|
| `wiki/laolao/weekly_full_monitor_bayes_facts/weekly-full-all_weeks_all_years.md` | **总本** · master, all weeks, newest on top |
| `wiki/laolao/weekly_half_year_monitor_bayes_facts/weekly-full-recent-half-year.md` | **半年切片** · rolling ~26-week window |
| `wiki/laolao/weekly_full_monitor_bayes_facts/weekly-full-26wXX-raw.md` | OCR 底本 (read-only) |
| `assets/sources/26wXX/` | thematic source split (九分法) |
| `assets/pictures/26wXX/` + `charts-index.md` | all extracted charts + semantic index |
| `wiki/atoms/{events,data,quotes}/` | upgraded atomic cards |
| `wiki/laolao/weekly-reading-26wXX.md` | 交换·比较·反复 reading note |
| `wiki/laolao/pattern-recognition-thread.md` | #模式识别 cumulative thread |
| `wiki/laolao/index.md`, `index.md`, `log/YYYY-MM.md` | catalogs + log |

## 母版结构（七章顺序，永远沿用）

The structural master is `raw/26w22…完整版.pdf`. The latest content/calibration master is the newest 完整版
(e.g. 26w25). Every week follows this chapter order:

```
一、#模式识别        现象重复 → 模式识别 → 人性 → 演化
二、本周世界要闻      中东、贸易战、中美、俄乌、日韩、拉美、亚洲
三、#美元秩序        美元指数、美债（一/二级）、数字货币、黄金
四、显著变化的#西方共识
五、美股市场         流动性、自下而上宏观、本周走势、季报
六、A股市场          基本面、自上而下宏观、本周走势、资金面
七、laolao推演        贝叶斯更新、下周验证信号、自己的缺口
```

## 五条核心原则（违反即返工）

1. **渗透 ≠ 堆叠**: do NOT stack each new week as one block on top. Infiltrate the new week's data into each
   chapter's relevant **sub-section timeline**, newest line on top. Each sub-node (伊朗/以色列/数字货币/季报…)
   is a continuously-updated timeline. *(Exception: the 总本 also keeps a per-week prose block at the top of
   `## 2026` for narrative — see reference.md; both coexist.)*
2. **原文优先**: 南老师原文 > agent 解读. Quote verbatim where possible (金句、框架、非对称逻辑、精确数字).
   Agent's own inference goes only in `七、laolao推演`, marked "非南老师原文".
3. **最新在最上**: every timeline and the 总演化线 table put the newest entry first/last per their existing
   convention; keep it consistent with the file.
4. **区分事实与观点**: data = fact, reading = opinion. Atom cards must separate 事实 / 解读.
5. **反例也要记**: keep falsifying observations (e.g. "没有稳定重复"), not just confirming ones.

⚠️ **Year-tag trap**: a tag like `w44` (no `26` prefix) usually means **2025** (25w44), not 26w44. Verify
before placing into a 26wXX timeline.

⚠️ **Filename trap**: `raw/` PDFs contain full-width commas (`，`) and `#` (e.g.
`第10周，#贝叶斯事件，完整版.pdf`, `26w15，贝叶斯事件，周报，完整版.pdf`). These **break naive `Glob`/`**.pdf`
patterns** — a glob can silently return 0 files. Inventory `raw/` with shell `ls`/`find` instead, and always
double-quote paths when passing to MinerU.

⚠️ **完整版 ≠ 摘要版 as a source**: only **完整版** carries the per-week 焦点 sub-actor tracking lines
(时限 / 背景 / 伊朗: … / 以色列: …) and full per-sub-section detail. 摘要版 (and the `raw/bayes2025/` archive)
condense history into a few lines that are usually already in 总本 — good for cross-checking, weak for backfill.
When you need to densify a sub-timeline, reach for the earlier weeks' **完整版**.

## SOP — copy this checklist and track progress

```
- [ ] 0. Read AGENTS.md; copy PDF into raw/; confirm exact filename (watch # ， spaces)
- [ ] 1. MinerU extract → save OCR 底本 weekly-full-26wXX-raw.md (read-only)
- [ ] 2. Split into thematic sources assets/sources/26wXX/ (九分法; normalize garbled CJK)
- [ ] 3. Archive ALL images → assets/pictures/26wXX/ + build charts-index.md
- [ ] 4. 渗透 into 总本 weekly-full-all_weeks_all_years.md (per-chapter + top prose block + embed key charts)
- [ ] 5. Update 总演化线 table (add new week row(s))
- [ ] 6. Sync 半年切片 + rolling pruning (advance window, drop oldest weeks, leave breadcrumbs)
- [ ] 7. Upgrade key bayes facts → atom cards (events/data/quotes), separate 事实/解读
- [ ] 8. Build reading note weekly-reading-26wXX.md (交换·比较·反复; livestream prep if before 直播)
- [ ] 9. Append to pattern-recognition-thread.md (new 模式识别 rows + element it into 元模式 chains)
- [ ] 10. Update index.md (catalog + counts) and append log/YYYY-MM.md
```

### Step 1 — Extract (MinerU)

Use the `pdf-to-markdown` skill. Typical call:

```bash
conda run -n safe_claw python \
  "<repo>/.../pdf-to-markdown/scripts/run.py" \
  "raw/26wXX，贝叶斯事件，周报，完整版.pdf" "/tmp/pdf-out-26wXX" --lang ch
```

Save the resulting markdown verbatim as the OCR 底本. For large PDFs (>10MB / 100+ pages), extract once then
work from the split sources, not the raw — see Step 2.

### Step 2–3 — Split + archive

- Split the OCR md into the 9 thematic sources (mapping table in [reference.md](reference.md)).
- Copy **every** image from MinerU `images/` into `assets/pictures/26wXX/`; build `charts-index.md` mapping
  each hash → semantic caption, grouped by chapter, marking ⭐ the key charts to embed.

### Step 4–6 — Infiltrate, evolve, prune

- Per-chapter 渗透 mapping and the rolling-pruning rules are in [reference.md](reference.md).
- Half-year window = rolling ~26 weeks. When advancing, prune the oldest weeks' sub-entries and leave one
  breadcrumb line per affected sub-section: `*（更早脉络：… → 见总本）*`. History always lives in 总本.

### Step 7–10 — Atoms, reading note, thread, catalog

- Atom conventions, reading-note skeleton, thread maintenance, and log formats are in
  [reference.md](reference.md); all reusable templates are in [templates.md](templates.md).

## Secondary operation — 子时间线回溯回填 (sub-timeline backfill)

Separate from the weekly ingest. Use when a sub-section timeline (e.g. `伊朗` / `以色列` / `美国` under
二、中东战争, or any 子节) only reaches back to week N, because the latest 完整版's **retrospective** started
tracking that sub-actor there — even though the war/topic began earlier. Each earlier week's own **完整版**
records that sub-actor's move that week (in 焦点·中东战争: `时限 / 背景 / 伊朗: …`), which the later
retrospective dropped. You can mine those to extend the sub-timeline backward to its true origin.

```
- [ ] 1. Confirm the gap: what's the earliest week in the sub-node now? when did the topic actually start?
- [ ] 2. Inventory raw/ 完整版 with shell ls/find (NOT Glob — filename trap); list which gap weeks have a 底本
- [ ] 3. MinerU-extract each gap week's 完整版 (batch in background; ~3 min each)
- [ ] 4. Per week, pull the sub-actor's OWN line from 焦点·中东战争 (+ the 中东/topic timeline). Verbatim.
- [ ] 5. Insert `- 26wXX：…` rows BELOW the existing earliest row, newest-of-the-backfill on top, oldest last
- [ ] 6. De-dup: where the broader timeline (e.g. 「中东（其他）」) already covers it, cross-ref「详见…」not copy
- [ ] 7. No底本 week → write the row as `暂缺` with the reason; NEVER invent a week
- [ ] 8. Add a provenance note under the sub-node (see templates.md): mark 南老师原文 vs Agent 推演
- [ ] 9. Mirror into 半年切片 if the backfilled weeks fall inside the rolling window
- [ ] 10. Log as `update` (not ingest — no new PDF week was published); bump counts
```

Highest value of this op: it surfaces **early signals the retrospective compressed away** — e.g. backfilling
伊朗 from full versions revealed 26w14 "通行海峡船只越来越多，伊朗事实上在放松'威胁'", 7 weeks earlier than
the retrospective's first "恢复经济" note (26w21). Reconstruction can beat the author's own summary.

## Checkpointing

After Steps 3, 4, and 6 (weekly ingest), pause and let the user review before proceeding — these are the
highest-risk, hardest-to-undo edits. For backfill, checkpoint after Step 4 (extracted evidence) before editing
the master file.

## Related files

- [reference.md](reference.md) — per-chapter 渗透 mapping, pruning rules, atom/reading/thread conventions,
  §10 子时间线回溯回填 (backfill) detail
- [templates.md](templates.md) — atom frontmatter, week-block skeleton, log entry formats, backfill
  provenance-note + row
- Companion skill: `pdf-to-markdown` (the MinerU extractor used in Step 1)
