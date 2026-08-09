# 验收标准 — PPT Mode

勾选表示已满足。个人自用；Fail Fast。SoT：[methodology.md](./methodology.md) · [design.md](./design.md)。

## 0. 文档合同（Phase 0）

- [x] [methodology.md](./methodology.md) 含 mode 矩阵、tools vs skill、pack、steer、非目标  
- [x] [design.md](./design.md) 架构 / ModePolicy / tools / SSE / UI  
- [x] [plan.md](./plan.md) 分阶段交付  
- [x] [problem.md](./problem.md) / [e2e.md](./e2e.md) / [scripts.md](./scripts.md)  
- [x] [docs/features/README.md](../README.md) 收录 `ppt-mode`  
- [x] [agent-modes](../agent-modes/) 交叉引用 `/ppt`（methodology + design）  

---

## A. ModePolicy / API

- [x] `mode` 缺省 → 仍为 `agent`（不误进 ppt）  
- [x] `mode=ppt` 合法；非法 mode → HTTP **400**  
- [x] `mode=loop` → 400（调度器，非执行 mode）  
- [x] ppt：FS **create-only**（`allow_edit=False`，`allow_delete=False`）  
- [x] ppt：`spawn=off`；`memory_auto_write=False`；`skill_execute=restrained`  
- [x] ppt：`observability=ppt`  
- [x] 会话 settings 可粘住 `mode=ppt`；New Chat 默认 **不是** ppt  

---

## T. 一等 PPT Tools

- [x] 存在 methodology §5 全部 MVP `safe_claw_ppt_*` tools  
- [x] **仅** `mode=ppt` 时工具列表包含它们；`mode=agent`（及 ask/plan/safe/debug/subagent）**不包含**  
- [x] `deck_init` / `slide_upsert` / `save_version` / `preview` / `inspect` / `list_versions` 快乐路径单测  
- [x] `slide_remove` 不可删尽最后一页（Fail Fast）  
- [x] `image_place` / 任意写路径越出 `WORKSPACE_DIR/ppt`（或约定根）→ 可见失败  
- [x] `save_version` **永不覆盖**已存在的 `_vN.pptx`（新版本或显式错误）  
- [x] **禁止**「仅跑 skill 脚本、无 tool 调用」作为验收主路径；不开 skill 时 tools 路径仍能完成出稿+预览  
- [x] `mode=ppt` 但 PPT tools 未注册 → 构图 / 请求 **Fail Fast**，禁止静默当 agent（缺 workspace_path 抛错）  

---

## P. 预览管线

- [x] `safe_claw_ppt_preview` 在已 save 版本上产出每页 PNG  
- [x] 渲染引擎缺失 → **显式错误**（含缺什么），禁止空成功  
- [x] dirty 未 save 时 preview 行为符合 design（推荐：要求先 save；若实现自动 save 须文档化且测死）  
- [x] SSE（或等价）携带 `deck_id` / `version` / `preview_urls`  
- [x] 受控文件 GET：workspace 内可读；越界拒绝  

---

## U. UI · PPT Observability pack

- [x] `/ppt` 出现在 slash 帮助；切换后 badge = `ppt`  
- [x] 策略芯片：create ✓ / update ✗ / delete ✗  
- [x] 切入 `/ppt` → `applyObservabilityPack("ppt")`：Exec 展开 + **Deck Preview 强制打开**  
- [x] **不**因 ppt 强制 Prompt Inspect / Skills  
- [x] 切出 ppt → 解除 PPT pack 强制态  
- [x] `ppt_preview` 后缩略图 **自动刷新**（有数据时 DOM 可见至少一页） — store + panel 已接 SSE；有头 LLM 长跑可选  
- [x] 版本列表可区分当前版  

---

## S. 提需求

- [x] 页级入口发送含 `[PPT_STEER] slide=N` 的用户消息（或等价 stream）  
- [x] 全局入口含 `[PPT_STEER] scope=deck`  
- [x] Steer **不**回灌整份旧子 transcript / 全量 PNG 进主气泡作为历史污染  
- [x] 大纲「确认出稿」可触发新一轮（短指令）；不自动改 mode  

---

## K. Skill（可选 · Phase D）

- [x] `pptx-authoring` SKILL 存在且说明 **tools 主路径**  
- [x] 未启用该 skill 时，acceptance T/P 主路径仍可通过  

---

## E. E2E / 报告

- [x] [e2e.md](./e2e.md) S0–S4 自动化绿（S5/tools 由 pytest 覆盖；有头可选） — `ppt-mode.spec.ts` **5 passed**  
- [x] 有 `acceptance-report-YYYY-MM-DD.md` — [acceptance-report-2026-08-05.md](./acceptance-report-2026-08-05.md)  

---

## 明确不验收（本期）

- 浏览器内嵌完整 PPT 编辑器  
- 非 ppt mode 下的 PPT tools  
- Streamlit 对等 UI  
- 修改 DeepAgents 上游  
- Cursor 云端 PPT / 全类型 subagent 全家桶  
- Full pack（Inspect/Skills）强制随 `/ppt` 打开  
