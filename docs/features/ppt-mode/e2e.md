# E2E — PPT Mode

前置：API + UI 已起；个人自用。有头：`HEADED=1`。

SoT：[acceptance.md](./acceptance.md) · [methodology.md](./methodology.md)

## S0 — Slash + badge + chips

1. New Chat（默认 agent）  
2. 输入 `/ppt` 回车  
3. **期望**：`mode-badge` 为 `ppt`；芯片 create ✓ / update ✗ / delete ✗  

## S0b — PPT pack 强制面

1. 在 ppt mode  
2. **期望**：Exec 面板展开；**Deck Preview** 面板打开（`data-testid` 待实现时写入本条）  
3. Prompt Inspect / Skills **不**被强制钉开  

## S1 — Tools 出稿 + 预览（可 mock 渲染）

1. 用户：「直接出稿：两页，标题 A/B」  
2. **期望**：Exec 出现 `safe_claw_ppt_*`（至少 init/upsert/save/preview）  
3. Deck Preview 至少 1 张缩略图（真渲染或测试夹具）  
4. workspace `ppt/` 下出现 `_v1.pptx`  

## S2 — 大纲卡 + 确认出稿

1. `/ppt`  
2. 用户要大纲（mock SSE 含 `### Deck Outline`）  
3. **期望**：`deck-artifact` 可见；点「确认出稿」→ 下一轮 user 消息含 `确认出稿` + `safe_claw_ppt_*`  

## S3 — ppt_preview 刷新缩略图

1. `/ppt`  
2. mock SSE 含两次 `ppt_preview`（v1/v2 + preview_urls）  
3. **期望**：`deck-preview-main`、`deck-thumb-1/2`、版本列表 v1/v2  

## S4 — mode sticky 重载

1. `/ppt` → reload  
2. **期望**：badge 仍为 `ppt`；Deck Preview 因 pack 重挂而打开  

## S5 — 非 ppt 无 PPT tools（API/单测）

见 pytest ToolManager；E2E 可选。

## 命令

```bash
cd test/e2e && FRONTEND_URL=http://localhost:3000 npx playwright test ppt-mode.spec.ts --retries=0
# 有头：HEADED=1 FRONTEND_URL=http://localhost:3000 npx playwright test ppt-mode.spec.ts --retries=0
```
