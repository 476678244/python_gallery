# 方法论 — PPT Mode

SoT：本文件。实现与 Demo 须对齐；冲突时改代码或改合同并记入 acceptance，禁止静默漂移。  
父合同：[agent-modes/methodology.md](../agent-modes/methodology.md)（会话粘性、Fail Fast、观测 pack 模式）。

## 1. 目标

让用户用 `/ppt` 进入**专用创作会话**：

1. Agent 通过**一等 PPT Tools**改结构、存版本、出预览（主路径）。  
2. UI **强制**可见改稿过程与**逐页实时预览**。  
3. 用户对着预览**方便提需求**（短信号，不回灌整份旧稿）。  
4. Skill 只提供审美与调用菜谱；**缺 skill 仍可创作**；**缺 tools 则不可用**。

## 2. 作用域

- Mode 存在 `SessionSettings.mode = "ppt"`，与其它执行 mode 同级粘性。  
- New Chat 默认仍为 `agent`；须显式 `/ppt`。  
- Loop tick 若当时 mode 为 ppt，继承 ppt 策略（含 PPT tools + pack）。  
- 命名：`AgentMode.ppt` ≠ 文件扩展名 `.pptx`；UI 勿混用变量名。

## 3. 行为矩阵（相对父表增量）

| Mode | 读 | 新建写 | Update/Edit | Delete | Skill | Memory 自动写 | Spawn | PPT tools | 可观测 |
|------|----|--------|-------------|--------|-------|---------------|-------|-----------|--------|
| **ppt** | 是 | **是** | **否**（FS） | **否**（FS） | restrained | 否 | 否 | **必开** | **PPT pack** |

- Deck 语义上的「改页 / 删页」= **工具层会话态**操作，**不是** FS update/delete。  
- 落盘：**仅** `save_version` 写出新 `_vN.pptx`；**永不覆盖**已有版本文件。

## 4. Tools vs Skill（硬边界）

| | Tools（`safe_claw_ppt_*`） | Skill（`pptx-authoring`） |
|--|---------------------------|---------------------------|
| 改结构 / 存盘 / 预览 | **必须** | 禁止作为唯一主路径（不得「只跑脚本假装成功」） |
| 版式 / 中文排版 / 故事节奏 | 可选 | **主责** |
| 缺一方 | 缺 skill → 仍可工具改稿；缺 tools → `/ppt` 创作不可用 | — |

注册合同：**仅 `mode=ppt`** 向 agent 暴露 `safe_claw_ppt_*`；其它 mode **不得**注册。

## 5. MVP 工具清单

| Tool | 职责 | Fail Fast 例 |
|------|------|----------------|
| `safe_claw_ppt_deck_init` | deck 会话态：id / 标题 / 主题 / 画布 | 空或非法 `deck_id` |
| `safe_claw_ppt_deck_inspect` | 结构 JSON | deck 未 init |
| `safe_claw_ppt_slide_upsert` | 按 index 新建或替换页 | 缺标题；越界策略显式 |
| `safe_claw_ppt_slide_remove` | 会话态删页 | 不可删尽最后一页 |
| `safe_claw_ppt_slide_reorder` | 重排 | 非法排列 |
| `safe_claw_ppt_theme_apply` | 主题档 | 未知 theme |
| `safe_claw_ppt_image_place` | workspace 图片入页 | 路径越界 / 文件不存在 |
| `safe_claw_ppt_save_version` | 写出新 `_vN.pptx` | 禁止覆盖已存在路径 |
| `safe_claw_ppt_preview` | 已保存版本 → PNG + URLs | **渲染依赖缺失立即失败**；未 save 须先 save |
| `safe_claw_ppt_list_versions` | 版本与预览齐全性 | — |

路径根：`WORKSPACE_DIR/ppt/`（即 `~/Downloads/safe_claw_worksapce/workspace/ppt/`）。越界 → `PptToolError`。

## 6. PPT Observability pack（硬合同）

切入 `/ppt` 立即强制；切出解除。

| # | 强制行为 |
|---|----------|
| 1 | Execution Path 展开；`safe_claw_ppt_*` 步骤可见 |
| 2 | **Deck Preview** 右栏强制打开（缩略图条 + 选中大图） |
| 3 | `ppt_preview` 成功（或 SSE `ppt_preview`）后 **自动刷新** UI；禁止「文件已写 UI 不更新」 |
| 4 | 版本列表可点选；当前版高亮，旧版可对照 |
| 5 | **不**强制 Prompt Inspect / Skills |
| 6 | Halt 可用 |

`ObservabilityPack` 增加 `"ppt"`（与 `default` / `full` / `subagent` 并列）。

## 7. 工作流与 System addendum

1. **首轮**（除非用户明确「直接出稿」）：只产出  
   `### Deck Outline` / `### Slide Storyboard` / `### Pending confirmation` —— 不调用 save/preview。  
2. 确认后：`deck_init` → `slide_upsert*` → `save_version` → `preview`；回复含 `deck_id`、`version`、页数、预览路径。  
3. 禁止用裸 `file_write` 手搓 pptx 作为主路径。  
4. 收到 `[PPT_STEER]`：精确改页/主题 → save → preview；必须新版本。

## 8. 用户提需求（短信号）

对标 sub-agents 的 `[USER_STEER]`：

| 形态 | 含义 |
|------|------|
| `[PPT_STEER] slide=N` + 需求正文 | 改第 N 页（1-based） |
| `[PPT_STEER] scope=deck` + 需求正文 | 全局风格 / 节奏 / 结构 |

- **不**回灌整份旧 transcript 或整包 PNG。  
- 携带当前 `deck_id` / `version`（UI 注入或 agent 从 inspect 读取）。  
- UI 入口：大纲确认出稿、页缩略图「提需求」、全局提需求、composer chips。

## 9. 请求合同

```
/ppt → SessionSettings.mode=ppt
    → POST /chat/stream { mode: "ppt", ... }
    → ModePolicy：create-only FS + ppt tools on + pack=ppt
    → ToolManager 注册 safe_claw_ppt_*
    → UI applyObservabilityPack("ppt")
```

- 非法 mode → 400。  
- `mode=ppt` 但 PPT tools 未装上 → **Fail Fast**（构图失败可见），禁止静默当 agent。

## 10. 明确非目标

- 浏览器内嵌完整 PPT 编辑器  
- 非 ppt mode 暴露 PPT tools  
- Skill 脚本静默替代 tool 合同  
- 强制 Full pack（Inspect/Skills）  
- Streamlit 对等、修改 DeepAgents 上游  
- Cursor 云端 PPT 协议  
