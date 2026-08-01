# 里程碑

| ID | 阶段 | 准入 | 准出 |
|----|------|------|------|
| M1 | A SoT / Fail Fast | 复现 R4/R1 文档化 | API toggle + filtered paths 单测绿；SM 挂 → 503 |
| M2 | B 工具过滤 | M1 | 禁用文件夹后 tool list / discover 无该集合；无静默 15 |
| M3 | C 可观测 | M2 | SSE `skills_loaded` 与 agent 一致；Inspect 可见 |
| M4 | D 有头验收 | M3 | S1–S3 有头绿；acceptance 人工勾选 |

## M1 — 单一真相源

- [x] `agent_config.enabled_skills` ↔ `get_enabled_skills()` ↔ 树勾选  
- [x] 无 Streamlit SM 分叉（API 进程）  
- [x] Folder toggle 严格匹配  

## M2 — 加载 = 工具可见

- [x] DeepAgent `skills=` ⊆ enabled  
- [x] ToolManager 列表 ⊆ enabled  
- [x] 截断策略显式（error），禁止静默丢 skill  

## M3 — 可观测

- [x] Stream 事件含实际 loaded 名列表  
- [x] 与 BM25 router chips 字段分离命名（`skills_loaded` vs `skills_invoked`）  

## M4 — 人工门禁

- [x] S1 persist + reload + loaded（Playwright；有头可选复验）  
- [x] S2 关 Ljg → loaded / tools 不可见  
- [x] S3 slash 选 skill → enabled 一致  

回归：`skill-tree*`、`skill-autocomplete`、`skills-path-activation`（T5 已断言 `skills_loaded`）。
