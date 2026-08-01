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
| Memory System（含黑话词典 / 中文检索） | [memory-system/](./memory-system/) | 增强中（中文问句检索缺口） |

## 与代码的关系

- 产品行为说明可与 `safe_claw/Docs/` 交叉引用（如 [MEMORY.md](../../safe_claw/Docs/MEMORY.md)）。
- **过程与验收**以本目录为准；实现细节以代码为准。
- Flow Coding 通用方法见 [../flow_coding.md](../flow_coding.md)。
