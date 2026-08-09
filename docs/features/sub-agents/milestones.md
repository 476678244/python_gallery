# 里程碑

| ID | 阶段 | 准入 | 准出 |
|----|------|------|------|
| M0 | Phase 0 硬闸门 | [problem.md](./problem.md) / [methodology.md](./methodology.md) 齐 | `validate_spawn_brief` 单测绿；缺字段不 spawn |
| M1 | Phase A SSE + 隔离 | M0 | SSE 父子树完整；主 messages 无 nested 中间内容；`done.skills_used` 无 NameError |
| M2 | Phase B UI 默认展开 | M1 | Exec DOM 可见前瞻三步 + nested tools；主气泡不粘贴子 transcript |
| M3 | Phase C fork / 自定义 | M2 | fork 真跑；ToolManager 无空壳 success；再 spawn 返工不污染主上下文 |
| M4 | Phase D 有头验收 | M3 | [e2e.md](./e2e.md) S1–S3 有头绿；[acceptance.md](./acceptance.md) 人工勾选 |

## M0 — 硬闸门

- [ ] `spawn_brief.validate_spawn_brief`：缺 / 空 / `look_ahead`≠3 / 未知 agent → ValueError（含字段名）  
- [ ] `task` / fork 入口先校验  
- [ ] methodology 与 acceptance「硬闸门」项可引用  

## M1 — 观测 SSE + 隔离

- [ ] `execution_step`：`subagent` + nested `tool_call` + `parent_step_id`  
- [ ] failed 闸门事件可观测  
- [ ] 隔离单测：main messages 增量不含 nested tool transcript  
- [ ] 修 `api/main.py` `skill_names` 未定义  

## M2 — Exec 默认展开

- [ ] 前端处理权威 `execution_step`（及兼容 `tool`）  
- [ ] 默认展开：`step_now`、`look_ahead` ①②③、`expected_output`、nested tools  
- [ ] 观测数据只进 execution store  

## M3 — 真 spawn

- [ ] `subagents=` + skills SoT  
- [ ] fork 接线；ToolManager `type == "subagent"`  
- [ ] 返工 = 新 brief 再 spawn  

## M4 — 人工门禁

- [ ] S1 合法委派 → Exec 展开可见  
- [ ] S2 缺三步 → failed 拦截  
- [ ] S3 隔离抽检 → 主上下文无子 transcript  

回归：skills-activation 相关用例不破。  
