# 里程碑

| ID | 阶段 | 准入 | 准出 |
|----|------|------|------|
| M0 | P0 文档 + Demo | 需求确认 | design/methodology 齐；Demo 含全执行 mode+loop；README 收录 |
| M1 | A ModePolicy + API | M0 | ask/plan 只读；safe create-only；非法/loop→400；缺省 agent |
| M2 | B UI slash + badge | M1 | 全 slash 可切；请求带 mode；芯片三态；New Chat=agent |
| M3 | C 观测 pack | M2 | debug Full / subagent pack；切出解除 |
| M4 | D Plan 产物 | M3 | 结构计划可见；无自动开写 |
| M5 | E Loop | M4 | interval + tick + stop；继承执行 mode |
| M6 | F 有头验收 | M5 | e2e S1–S4 族绿；acceptance-report |

## M0 — 合同

- [x] methodology（含 safe/debug/subagent）  
- [x] [design.md](./design.md)  
- [x] problem / plan / acceptance / e2e / scripts / roundtable  
- [x] Demo 基底 Ask/Agent/Plan/Loop  
- [x] Demo Safe / Debug / Subagent  
- [x] features README 收录  

## M1 — API

- [x] `ModePolicy.resolve`  
- [x] `ChatRequest.mode` + session 默认 mode  
- [x] ask/plan 只读；safe：create✓ edit✗  
- [x] 非法 mode / mode=loop → 400；缺省 agent  

## M2 — UI

- [x] 全 slash + badge + 策略芯片  
- [x] `streamChat` 传 mode  

## M3 — 观测

- [x] Full pack / Subagent pack（面板强制）  
- [ ] 子树 SSE 深展开 — 依赖 sub-agents  

## M4 — Plan

- [x] prompt 合同；无静默转写  
- [x] 专用 Plan 卡片组件  

## M5 — Loop

- [x] 调度 / stop；tick 带执行 mode  

## M6 — 验收

- [x] API/单元 pytest  
- [x] Playwright S0/S0b（2 passed）  
- [x] acceptance-report-2026-08-03  

