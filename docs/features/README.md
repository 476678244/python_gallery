# Feature 文档约定

**一个功能主题 = 一个文件夹**，放在 `docs/features/<feature-id>/`。

记录该主题从问题 → 计划 → 实现 → 测试 → 验收的全过程，作为后续增强与回归的唯一入口。

## 命名

| 项 | 规则 | 示例 |
|----|------|------|
| 文件夹 ID | `kebab-case`，稳定、可引用 | `memory-system` |
| 标题 | README 首行 H1 | `# Memory System` |

## 建议文件清单

每个 feature 文件夹至少包含：

| 文件 | 用途 |
|------|------|
| `README.md` | 主题概述、当前状态、文档索引、相关代码路径 |
| `problem.md` | 驱动问题 / 失败案例（复现步骤 + 根因） |
| `plan.md` | 分阶段开发计划与交付物 |
| `milestones.md` | 测试里程碑与准入/准出 |
| `acceptance.md` | 验收标准（可勾选） |
| `e2e.md` | E2E 用例（含 **有头** 跑法） |
| `scripts.md` | 辅助脚本路径与用法 |

可按需要追加：`decisions.md`（ADR）、`changelog.md`、`notes.md`。

## 现有主题

| Feature | 路径 | 状态 |
|---------|------|------|
| Memory System（含黑话词典 / 中文检索） | [memory-system/](./memory-system/) | Phase A–D 已落地；C2 待人工 Accept |
| Skills Activation（可靠激活） | [skills-activation/](./skills-activation/) | Phase A–D **完成**（见 acceptance-report） |
| Sub Agents（走一步看三步 / 可观测 / 隔离） | [sub-agents/](./sub-agents/) | A–D2/F 自动化 PASS；Phase C fork 未验收 |
| Agent Modes（ask/agent/plan/**safe**/debug/subagent/loop） | [agent-modes/](./agent-modes/) | **核心验收通过**（pytest + Playwright S0/S0b） |
| PPT Mode（`/ppt` · 一等 tools · 预览 pack · 提需求） | [ppt-mode/](./ppt-mode/) | **验收通过**（pytest + Playwright S0/S0b/S2；见 acceptance-report） |
| （纠正）ljg-roundtable 用于讨论设计 | [sub-agents 圆桌](./sub-agents/roundtable--observability-ui-demo.md) · [agent-modes 圆桌](./agent-modes/roundtable--modes-ui-demo.md) | 方法论文档；非产品 UI |

## 与代码的关系

- 产品行为说明可与 `safe_claw/Docs/` 交叉引用（如 [MEMORY.md](../../safe_claw/Docs/MEMORY.md)）。
- **过程与验收**以本目录为准；实现细节以代码为准。
- Flow Coding 通用方法见 [../flow_coding.md](../flow_coding.md)。
