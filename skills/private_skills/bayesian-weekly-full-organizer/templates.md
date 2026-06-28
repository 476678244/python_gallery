# Templates — copy-paste skeletons

Reusable structures for `bayesian-weekly-full-organizer`. Replace `26wXX` and fill brackets.

---

## 总本 / 半年切片 top prose block

```markdown
### 26wXX · [一句话核心模式]

**来源**：

- `raw/26wXX，贝叶斯事件，周报，完整版.pdf`（南老师原文完整版 · 最新校准母版）
- Source 切分：[[26wXX-00-index]]（9 主题 + 全部图）
- OCR 底本：[[weekly-full-26wXX-raw]]

#### 一、#模式识别
现象重复 → 模式识别 → 人性 → 演化
[本周核心现象 + 南老师原文 + 嵌 ⭐ 图]

#### 二、本周世界要闻
[中东/日韩/俄乌/欧美… 每子节最新在最上]

#### 三、#美元秩序
[美元指数 / 美债一二级 / 数字货币 / 黄金]

#### 四、显著变化的 #西方共识
[本周新增；若无，明确写"本周无新增，最新仍为 26wYY…"]

#### 五、美股市场
[流动性(NAAIM/ETF flow) / 自下而上估值 / 消费·基本面 / 走势 / 季报]

#### 六、A股市场
[基本面 / 自上而下宏观 / 走势·资金面]

#### 七、laolao 推演
本周最大的贝叶斯更新：
> [上周结论 → 本周更新]

下周重点验证：

| 信号 | 关注理由 | 验证条件 |
|------|----------|----------|
| | | |

自己的缺口：
- [极值/无变化/数据口径等待证伪点]
```

---

## 总演化线 row

```markdown
| 26wXX | [一句话核心模式] | [本周主导力量] | [哪个假设被证实/证伪] |
```

---

## Atom — event

```markdown
---
date: YYYY-MM-DD
tags:
  - 事件
  - [实体]
  - [概念]
  - 南添
  - 贝叶斯事件周报
  - 26wXX
source: 26wXX-bayesian-weekly-report-full
author: nan-tian
rating: 6
confidence: 中
status: active
---

# [事件标题]

**核心观点**: [一句话，费曼式]

## 事实 (Facts)
- [具体数据/事件]

## 解读 (Interpretation)
- **观点**: [理解/洞察]
- **置信度**: 中 — 理由：
- **时间戳**: [[时间: 26wXX]]

## 关键影响
- **直接影响**:
- **连锁反应**:
- **时限/窗口**:

## 验证清单
- [ ] 1周后验证
- [ ] 1月后验证

---
**连接数**: 0 | **相关**: [[ ]] | [[ ]]
**来源切片**: [[26wXX-00-index]] | [[weekly-full-all_weeks_all_years]]
```

---

## Atom — data

```markdown
---
date: YYYY-MM-DD
tags:
  - 数据
  - [主题]
  - 南添
  - 贝叶斯事件周报
  - 26wXX
source: 26wXX-bayesian-weekly-report-full
author: nan-tian
rating: 5
---

# [数据标题]

## 核心数据
[一句话 + 关键数字]

## 事实
- [数据点]

## 解读
[含义 / 背离 / 验证点]

## 费曼式解释
[12 岁能懂]

## 追踪要点
- [后续验证]

## 相关笔记
- [[ ]]
```

---

## Atom — quote / insight

```markdown
---
date: YYYY-MM-DD
tags:
  - 金句
  - 模式识别
  - 南添
  - [概念]
  - 贝叶斯事件周报
  - 26wXX
source: 26wXX-bayesian-weekly-report-full
author: nan-tian
rating: 7
---

# [金句标题]（26wXX）

> "[南老师原文引用]"

- **核心**: [一句话]
- **为什么重要**: 
- **时间**: [YYYY-MM, 26wXX]

---
## 模式识别链 / 应用框架
[chain or table]

---
**方法论框架**: [[pattern-recognition]] | [[bayesian-events]] | [[nan-tian]]
**来源切片**: [[26wXX-00-index]] | [[weekly-full-all_weeks_all_years]]
```

---

## pattern-recognition-thread row

```markdown
| **26wXX** | [模式识别一句话] | [主导力量 / 演化] | [[atom-or-block-link]] |
```

---

## Breadcrumb (half-year pruning)

```markdown
*（更早脉络：25w51 [关键节点] → 25w50 [关键节点] → wYY [更早] → 见总本）*
```

---

## 子时间线回溯回填 — inserted rows + provenance note

```markdown
- 26wYY：[该周该子角色的自身动作，南老师原文]
- 26wXX：[更早一周…]（详见「中东（其他）」26wXX）   ← de-dup via cross-ref where broader timeline overlaps
- 26w9 周末：[topic 起点行]

> 26wYY→26wXX 的[子角色]子时间线，由各周**完整版「焦点·中东战争」**回填（南老师原文，非 Agent 推演）；
> 26wZZ 该周无完整版/摘要版底本，暂缺。
```

---

## Log entries

```markdown
## [YYYY-MM-DD] ingest | 26wXX 贝叶斯事件周报·完整版
- MinerU 解析 → OCR 底本；九分法切 source；全部图归档 + charts-index
- 渗透总本（含回填 26wYY）；总演化线 +N 行；半年切片同步 + 滚动剪除
- 核心模式识别：[一句话]
- 更新页面：[列表]
```

```markdown
## [YYYY-MM-DD] create | 26wXX 关键贝叶斯事实 → N 张原子卡片
- [金句/事件/数据 列表 + 回链]
- 更新 index.md（Events/Data/Quotes 计数）、atoms/README
```

```markdown
## [YYYY-MM-DD] update | [子角色]子时间线回填至[起点]（26wYY→26wXX）
- 缘起：[子节]原仅 26w..→26w..（最新完整版回溯只到此）
- 底本：MinerU 提取 raw/ 各周完整版（[列表]）；发现各周「焦点·中东战争」均有独立「[子角色]：…」行
- 关键新增：[最早信号 / 比原记录提前 N 周]
- 同步 总本 + 半年切片；26wZZ 无底本暂缺；与「中东（其他）」重叠处用「详见」交叉引用
```
