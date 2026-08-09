# 计划 — Skills 可靠激活

```mermaid
flowchart LR
  A[PhaseA_SoT_FailFast] --> B[PhaseB_LoadAndToolFilter]
  B --> C[PhaseC_Observability]
  C --> D[PhaseD_HeadedAccept]
```

## Phase A — 单一真相源 + Fail Fast 合同（P0）

**交付**

- 文档与代码对齐：SoT = `SkillsManager` + `agent_config.json`  
- Session `settings.enabled_skills`：标注废弃或真正接线（本期倾向废弃，避免双写）  
- SM init 失败 → `/skills` **503**，禁止空树装正常  
- Folder toggle：严格 path 段匹配，禁止松散 substring  
- DeepAgent **复用 API 全局 SM**，去掉 Streamlit session_state 分叉（API 路径）  
- 对齐 `project_root` parent 深度（linked_skills 扫描一致）

**退出**：`pytest` — toggle → `get_filtered_skills_paths` 名称精确匹配

## Phase B — 激活 = 加载 + 工具过滤（P0）

**交付**

- `SkillDiscovery` / `skill_list_*` / `skill_discover_and_execute` 共用 enabled 集合  
- 去掉静默「限 15」：超限 → **显式 error SSE** 或可见 truncation chip + Fail Fast 配置项  
- （可选）chat 请求带 `enabled_skills` 作审计：与 SM 不一致 → **409**

**退出**：stream/API 测试 — 禁用文件夹后 filtered paths **与** tool list 均不含该集合

## Phase C — 可观测（P1）

**交付**

- SSE step：`skills_loaded` = 实际传入 `create_deep_agent` 的名字列表（不是仅 router）  
- Prompt Inspect / Exec 可见 loaded skills  
- 右侧面板「N enabled」优先显示上一轮后端回报的 active set

**退出**：E2E 断言 loaded list，不只 chips

## Phase D — 有头黄金路径（P0 验收）

**交付**

- `test/e2e/skills-activation-zh.spec.ts`（或等价）覆盖 [e2e.md](./e2e.md) S1–S3  
- [acceptance.md](./acceptance.md) 勾选 + acceptance-report / human-non-accept-report  

**退出**：人工 — 关则不能跑；开则在 loaded list 且可用

## 非目标（本期）

- Per-session skill 配置  
- 向量 / Memory  
- 重做 Skill 作者体验
