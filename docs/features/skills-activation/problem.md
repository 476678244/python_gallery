# 问题：侧栏开了，聊天里未必真激活

> **2026-08-01**：下列根因已按 plan 修复；本页保留为审计记录。验收见 [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md)。

## 用户可见现象

| 操作 | 实际 | 期望 |
|------|------|------|
| 关掉整个 Ljg Skills 文件夹 | 树显示关；问 ljg 相关题时 router/工具仍可能摸到 `ljg-*` | 关 = 不进 DeepAgent `skills=`，且 `skill_list` / `skill_discover` 不可见 |
| 只开 1～2 个 skill | Prompt / 回复仍像「全家桶」或神秘截断到 15 | 加载列表 = 开启集合；截断必须可见或 Fail Fast |
| 刷新后树状态对，发一条「当前加载了哪些 skill」 | 答非所问 / 与树不一致 | 与 `agent_config.enabled_skills` 一致 |
| Session 切换 | 树全局共享（符合现状） | 明确文档化；勿假装 session 级 `enabled_skills` 生效（字段是死的） |

## 复现步骤（当前）

```bash
# 1) 看持久化 SoT
cat ~/Downloads/safe_claw_worksapce/Data/agent_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('count', len(d.get('enabled_skills') or [])); print((d.get('enabled_skills') or [])[:8])"

# 2) API 树
curl -s http://127.0.0.1:8000/skills | python3 -c "import sys,json; d=json.load(sys.stdin); print('keys', d.keys() if isinstance(d,dict) else type(d))"

# 3) UI：Skill Tree 关掉 Ljg → New Chat（DeepSeek）→ 问「用 skill_list 列出可用技能，有没有 ljg-」
#    期望：无 ljg；现状：工具层可能仍全量扫描
```

## 根因（审计摘要）

### R1 — Chat 不传 / 不用请求级 enabled 列表

- `chat-input` 发 stream 时只有 `messages/sessionId/model`，**不传** `enabledSkills`
- `ChatRequest.enabled_skills` 存在，但 SM 在时 stream **只用** `sm.get_enabled_skills()`，session `settings.enabled_skills` 恒为 `[]` 且从未同步

### R2 — DeepAgent 与 ToolManager 过滤不一致（主因级）

- `create_deep_agent(skills=filtered_paths)` 按 enabled 过滤  
- `skill_list_available` / `skill_discover_and_execute` 走 **全量 scanner** → **关了的 skill 仍可被工具摸到**

### R3 — 静默截断 15

- `_initialize_agent` 上下文超限时静默只留 15 条 path → 「开了但没加载」且无 SSE 说明

### R4 — SoT 分叉风险

- API 全局 `SkillsManager` vs DeepAgent 内可能 `streamlit.session_state` 再 new 一套  
- SM init 失败时 `/skills` 空树、toggle 软失败（违反 Fail Fast）  
- 文件夹 toggle 用 substring `folder_key in raw`，可能误伤

### R5 — 可观测性错位

- SSE「Skills Path / invoked」多来自 **BM25 router chips**，≠ 实际传入 DeepAgent 的 path 列表  
- 既有 E2E（`skills-path-activation`）易绿在 router，验不到「真激活」

## 明确不在本主题

- 重新设计 skill 目录规范 / 写新 skill 内容  
- Per-session 独立 skill 配置（除非后续单独立项）  
- Memory 检索（见 [memory-system](../memory-system/)）
