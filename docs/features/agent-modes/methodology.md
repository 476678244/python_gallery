# 方法论 — Agent Modes

SoT：本文件。实现与 Demo 须对齐此处合同；冲突时改代码或改合同并记入 acceptance，禁止静默漂移。

## 1. 目标

让用户用 slash **显式选择**当前会话的交互策略：

| Mode | Slash | 一句话 |
|------|-------|--------|
| Ask | `/ask` | 只读问答 / 解释；不改工作区、不跑 skill execute |
| Agent | `/agent` | 完整执行（现状行为）；观测保持用户/默认偏好 |
| Plan | `/plan` | 只读规划；产出可展示计划结构；不改文件 |
| Safe | `/safe` | **克制写入**：允许**新建**；禁止 delete / remove / **update** |
| Debug | `/debug` | **工具同 agent**；**强制 Observability Full pack**（全局观测） |
| Subagent | `/subagent` | **工具同 agent + 允许 spawn**；**强制 Subagent Observability pack** |
| PPT | `/ppt` | **create-only FS + 一等 PPT tools**；**强制 PPT Observability pack**（预览 + 提需求）— 详见 [ppt-mode](../ppt-mode/) |
| Loop | `/loop` | 按 interval 定时重跑 prompt；工具策略继承会话当前「执行 mode」 |

执行 mode（ask / agent / plan / **safe** / debug / subagent / **ppt**）**一等公民**；loop 为一等**调度器**（不改写执行 mode）。  
`/ppt` 的工具清单、预览 pack、`[PPT_STEER]` 合同以 [ppt-mode/methodology.md](../ppt-mode/methodology.md) 为 SoT（本文件只登记枚举位）。

## 2. 作用域：会话级

- Mode 存在 **`SessionSettings.mode`**（与 session `model` 同级粘性）。
- `/ask` 等只改**当前会话**，之后每条消息沿用，直到再 slash 切换。
- **不是**全局 `agent_config`；**不是**仅当条消息。
- **New Chat → 默认 `agent`**（保持今日全工具行为，避免惊吓）。
- Loop 是调度器：启动 loop 不自动改写 `mode`；每次 tick 用**当时**会话执行 mode 策略发一轮。

命名隔离：

- UI `SlashMode`（palette）≠ 产品 `AgentMode`
- `AgentMode.subagent`（会话策略）≠ SSE `step_type: "subagent"`（执行树节点）— 实现时勿混用同一变量名空间

## 3. 行为矩阵（硬合同）

| Mode | 读 | 新建写 | Update/Edit | Delete/Remove | Skill execute | Memory 检索 | Memory 自动写 | Spawn | 可观测 |
|------|----|--------|-------------|---------------|---------------|-------------|---------------|-------|--------|
| ask | 是 | 否 | 否 | 否 | 否 | 是 | 否 | 否 | 默认 |
| agent | 是 | 是 | 是 | 是* | 是 | 是 | 是 | 是† | 默认 |
| plan | 是 | 否 | 否 | 否 | 否 | 是 | 否 | explore-only‡ | 默认 |
| **safe** | 是 | **是** | **否** | **否** | **克制§** | 是 | 否 | 否 | 默认 |
| debug | 是 | 是 | 是 | 是* | 是 | 是 | 是 | 是† | **Full pack** |
| subagent | 是 | 是 | 是 | 是* | 是 | 是 | 是 | **必开**† | **Subagent pack** |
| **ppt** | 是 | **是** | **否** | **否** | **克制§** | 是 | 否 | **否** | **PPT pack** ¶ |
| loop | — | — | — | — | — | — | — | — | 继承 |

\* agent/debug/subagent 的 delete 仍受 backend / Safety 配置约束；默认实现可与今日一致。  
† 受 [sub-agents](../sub-agents/) brief 闸门。  
‡ 若已接线；否则否。  
§ Skill execute **允许**，但任何触达 FS 的操作仍受 safe/ppt 门禁（不可 update/delete）；无法保证时 **Fail Fast 拒绝该次调用**，禁止静默成功。  
¶ PPT pack + `safe_claw_ppt_*` 仅 ppt mode；合同见 [ppt-mode](../ppt-mode/methodology.md)。Deck 语义改页≠ FS update。

Loop 行：自身**不定义**工具权限；每次 tick **继承**当时执行 mode。

### 硬门禁（Fail Fast）

**Ask / Plan** 必须同时满足：

1. Filesystem：`allow_write=False`（且无 edit/delete）
2. ToolManager：剥离写 / 执行类工具（至少 `safe_claw_file_write`、会改工作区的 edit/delete、`skill_discover_and_execute` 若无法保证只读）
3. System prompt：声明 mode（辅助，**不能替代** 1–2）

**Safe** 必须同时满足：

1. Filesystem：**允许 create-only write**；**禁止 edit/update**；**禁止 delete/remove**  
   - 现有 `SecureFilesystemBackend.write` 已是 create-only（文件已存在则失败）— safe 应启用 write、关闭 edit、关闭 delete  
   - 实现须增加/接通显式 `allow_edit=False`（或等价：edit 工具不注册 / 调用即失败）；`allow_delete=False`
2. ToolManager：注册克制写；**不注册**或硬拒绝 delete/remove/update/edit 类工具
3. 覆盖写（overwrite）、rename-over、truncate、`sed` 式原地改 = **update**，一律禁止
4. System prompt：声明「仅可新建；不可改删」（辅助，**不能替代** 1–3）

禁止「只改 prompt、工具仍可改删」。被挡操作 → 可见失败或未注册；禁止静默假装成功。

## 4. 各 Mode 细则

### Ask

- 用途：解释代码、答疑、读文件总结。
- 可读：list/read、memory 检索、skill list / get prompt（只读元数据）。
- 禁止：写文件、skill execute、spawn subagent、memory 自动写入。

### Agent

- 与今日 `/chat/stream` 行为一致：全工具 + skills-activation SoT + 可选 subagent。
- 切换到 agent = 恢复完整能力。

### Plan

- 用途：先规划后动手；用户审阅后再 `/agent` 或 `/safe` 执行。
- 工具策略同 Ask（硬只读）。
- 额外：专用 plan-oriented system prompt；UI/消息中可展示结构化计划块。
- 不自动进入 agent/safe；须用户显式切换。

### Safe

- **定义**：在安全前提下允许**克制写入**——**仅新建（create）**；**禁止 delete / remove / update（含 edit、overwrite）**。
- 用途：生成新文件/草稿/导出，而不破坏已有工作区内容。
- 读：允许。新建写：允许（目标路径不得已存在）。Update/Edit：禁止。Delete/Remove：禁止。
- Skill execute：克制允许（§3 §）；FS 门禁仍生效。
- Memory 自动写：关闭。Spawn：关闭。
- 观测：默认偏好（不强制 Full / Subagent pack）。
- 与 ask：ask 完全不写；safe 可新建。与 agent：agent 可改删；safe 不可。
- 切入 `/safe`：策略芯片须显示「create ✓ / update ✗ / delete ✗」。

### Debug

- **定义**：`/debug` = 执行能力与 **agent 相同**，并强制 **Observability Full pack**（§5）。
- 切入：立即 Full pack。切出：解除 Full pack（若切到 `/subagent` 则改挂 Subagent pack）。
- **观测强制开**是 UI/SSE 合同，不单靠 prompt。

### Subagent

- **定义**：`/subagent` = 执行能力与 **agent 相同**，且 **spawn/task 必须启用**，并强制 **Subagent Observability pack**（§5b）。
- 与 debug：Full ⊇ Subagent pack；`/subagent` 不强制 Prompt Inspect / Skills。
- **不放宽** spawn brief 硬闸门。
- 禁止：badge 写 subagent 但 UI 仍扁平、或 spawn 被剥掉。

### Loop

语法：`/loop [interval] <prompt>`

- Interval 例：`30s`、`5m`、`2h`；无 interval → 动态间隔（实现阶段定细节；须可 stop）。
- 空 prompt → 用法提示，不启动。
- **武装前必须与人确认「终止 / 完成条件」**（Fail Fast）：
  1. UI 弹出确认：展示 interval + prompt，并要求用户填写**明确的完成/终止条件**（非空）。
  2. 用户取消或条件为空 → **不武装**，禁止静默开跑。
  3. 条件示例：`CI 全绿`、`文件 X 出现`、`连续 3 次无变化`、`最多 10 tick`、`到 18:00`。
  4. 武装后：每 tick 将完成条件注入上下文（或状态条可见）；满足条件或用户 `/loop stop` → 停止。
  5. 仅有 interval、没有完成条件 = **不合格**，与 spawn brief 同级硬闸门。
- Tick：按当前会话执行 mode 策略调用 chat/stream。
- Demo / UI：可见 interval、完成条件、下次 tick、running/stopped。

## 5. Observability Full pack（`/debug` 硬合同）

| # | 选项 | 强制行为 |
|---|------|----------|
| 1 | Execution Path 面板 | 展开；当前 run 可见 |
| 2 | 嵌套 / subagent 细节 | 默认展开 look_ahead、nested tools（有则显示） |
| 3 | Prompt Inspect 面板 | 展开 |
| 4 | Skills Path 面板 | 展开（或 skills_loaded 可见） |
| 5 | 闸门 / 工具失败 | 默认可见 |
| 6 | Halt / 纠正方向 | Exec 头可用 |
| 7 | SSE 细节 | thinking / tool / execution_step 不静默丢弃 |

非 debug：**不得**因实现方便而永久 Full pack。

## 5b. Subagent Observability pack（`/subagent` 硬合同）

| # | 选项 | 强制行为 |
|---|------|----------|
| 1 | Execution Path | 展开 |
| 2 | Subagent 子树 | look_ahead×3 / nested / 状态默认展开 |
| 3 | 闸门失败 | failed 节点默认可见 |
| 4 | Halt / 纠正方向 | Exec 头可用；旧子树可灰显对照 |
| 5 | 隔离 | 主 messages 不回灌 nested 中间 transcript |
| 6 | SSE | `step_type=subagent` 必须渲染 |

**不**因 `/subagent` 强制 Prompt Inspect / Skills。Full pack ⊇ 本 pack。

## 5c. Safe FS 策略档（实现触点）

目标态配置（名称可调整，语义不可漂）：

```
mode=safe ⇒
  allow_write=True          # create-only write（已存在 → 失败）
  allow_edit=False          # 禁止 update
  allow_delete=False        # 禁止 delete/remove
  skill_execute=restrained  # 允许调用，越权 FS → 失败
  spawn=False
  memory_auto_write=False
```

代码锚点：`safe_claw/core/deepagents/backend.py`（`FilesystemBackendConfig` / `write` / `edit` / delete）；`ToolManager`；`api/main.py` 构图。

## 6. 请求合同（实现目标态）

```
slash → SessionSettings.mode → POST /chat/stream { mode, ... }
                              → Tool + FS gate
                              → ask/plan: readonly
                                 | safe: create-only write, no edit/delete
                                 | agent: full
                                 | debug: full + Full pack
                                 | subagent: full + spawn + Subagent pack
loop scheduler ──tick─────────→ 同上
```

- 未知 / 缺失 `mode`：默认 **`agent`**
- 非法 `mode` → **400** Fail Fast

## 7. 明确不升格为顶层 mode（圆桌 + 用户修订）

| 候选 | 落点 |
|------|------|
| explore | ask/plan 上 `spawn=explore-only` |
| review / teach | 单次动作或 ask/plan 特化提示 |
| yolo / auto | 显式 `require_confirm` 开关，非 mode |

**用户修订**：

1. `debug` — Full pack  
2. `subagent` — Subagent pack + spawn 必开  
3. `safe` — create-only；禁 update/delete/remove（§3–§4 Safe、§5c）

## 8. 边界（明确不在本主题）

- Cursor IDE 云端 Agent / Bugbot 全家桶对等
- Streamlit UI 对等改造
- 修改 DeepAgents 上游包（可在 SafeClaw backend/ToolManager 层接线）
- Per-session skill 配置（见 [skills-activation](../skills-activation/)）
- Subagent **协议 / 硬闸门 / fork 实现**（见 [sub-agents](../sub-agents/)）
