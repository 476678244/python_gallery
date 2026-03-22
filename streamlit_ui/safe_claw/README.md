# SafeClaw 🦞

> 基于 LangGraph Deep Agents + OpenClaw 思想的本地 AI 助手
> 安全优先 · 文件优先 · 隐私可控

---

## 简介

SafeClaw（安全之爪）是一个**安全优先**、**文件优先**的本地 AI 助手，借鉴 OpenClaw 的设计思想，使用 **LangGraph + Streamlit** 技术栈实现。所有数据本地存储，配置可手动编辑，操作透明可审计。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **本地优先** | 数据不出境，隐私完全可控 |
| **文件优先** | 所有配置和记忆都是可编辑的 Markdown/JSON |
| **安全导向** | 敏感操作二次确认，三级安全策略 |
| **LangGraph 架构** | 基于 LangGraph 的 Deep Agents 状态图工作流 |
| **多 Agent 协作** | 支持多 Agent 节点协作处理复杂任务 |
| **智能技能系统** | 技能自动转换为 LLM 可理解的工具定义 |
| **简单易用** | Streamlit 单页应用，无需守护进程 |

---

## 技术栈

- **Python 3.10+**
- **Streamlit** - Web 界面框架
- **LangGraph** - Deep Agents 状态图管理
- **LangChain** - 工具调用和 LLM 抽象
- **Pydantic** - 数据验证和配置管理
- **ChromaDB** (可选) - 向量记忆检索

---

## 安装

### 环境要求

- Python 3.10+
- macOS / Linux / Windows (WSL)

### 快速安装

```bash
# 克隆仓库
git clone <repo-url>
cd safe_claw

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

---

## 项目结构

```
~/.safe_claw/                    # 用户数据目录
├── config.json                  # 主配置
├── sessions/                    # 会话状态
│   └── {session_id}.json
├── agents/                      # 多 Agent 配置
│   ├── default/                 # 默认 Agent
│   │   ├── AGENTS.md           # Agent 提示词
│   │   ├── SOUL.md             # 人格定义
│   │   ├── USER.md             # 用户偏好
│   │   └── skills/             # Agent 专属技能
│   ├── coding/                  # 编程 Agent
│   ├── analysis/                # 分析 Agent
│   └── planning/                # 规划 Agent
├── memory/                      # 全局记忆（跨 Agent 共享）
│   ├── 2026-03-22.md
│   └── index/
├── shared_skills/               # 共享技能（所有 Agent 可用）
│   └── file_operations/
└── graphs/                      # Graph 定义
    ├── default.json             # 简单对话图
    └── multi_agent.json         # 多 Agent 协作图
```

---

## 使用方法

### 首次使用

1. 启动应用后会自动创建工作区
2. 在设置页选择 LLM 提供商并输入 API 密钥
3. 开始对话！

### 日常对话

1. 在聊天框输入问题
2. DeepAgents 状态图自动处理：
   - 分析输入，识别是否需要技能调用
   - 智能选择合适的技能组合
   - 自动检索相关历史记忆
   - 执行技能并整合结果
   - 生成响应并更新长期记忆

### 自定义技能

在 `skills/` 目录下创建技能包：

```
skills/
└── my_skill/
    ├── SKILL.md          # 技能描述
    └── main.py           # 技能实现
```

---

## 配置说明

### AGENTS.md

定义 Agent 的行为和能力范围：

```markdown
# Agent 定义

## 角色
你是一个专业的编程助手...

## 能力
- 代码分析和重构
- Bug 修复建议
- 代码生成
```

### SOUL.md

定义 Agent 的人格特征：

```markdown
# 人格定义

## 性格
严谨、耐心、乐于解释

## 沟通风格
技术准确，通俗易懂
```

### USER.md

存储用户偏好（自动更新）：

```markdown
# 用户偏好

- 编程语言偏好: Python
- 回复风格偏好: 详细解释
```

---

## 安全策略

SafeClaw 采用三级安全策略：

| 级别 | 操作类型 | 处理方式 |
|------|---------|---------|
| **黑名单** | 格式化系统、修改 BIOS 等 | 完全禁止 |
| **白名单** | 文件读取、记忆查询、聊天响应 | 自动允许 |
| **确认级** | 文件删除、系统命令、网络请求 | 需用户确认 |

---

## 路线图

### Phase 1: 基础 Graph (MVP)
- [ ] InputNode + AgentNode + MemoryNode + ResponseNode
- [ ] 简单线性图（单 Agent）
- [ ] 基础 Streamlit UI

### Phase 2: 多 Agent 支持
- [ ] RouterNode（智能路由）
- [ ] 多 Agent Workspace 管理
- [ ] 条件边和循环

### Phase 3: 高级功能
- [ ] SkillNode（工具执行）
- [ ] SupervisorNode（监督者模式）
- [ ] Graph 可视化

### Phase 4: 优化
- [ ] 并行节点执行
- [ ] 状态检查点（断点续传）
- [ ] 人机协同节点

---

## 与 OpenClaw 的关系

SafeClaw 借鉴 OpenClaw 的核心设计思想：

| OpenClaw 特性 | SafeClaw 实现 |
|--------------|--------------|
| 多 Agent 隔离 | 每个 LangGraph 节点是一个独立 Agent |
| 文件优先配置 | AGENTS.md / SOUL.md / USER.md 驱动行为 |
| 会话路由 | Graph 中的条件边实现智能路由 |
| 技能系统 | 节点可调用技能工具 |
| 本地优先 | 所有状态本地存储，可版本控制 |

**差异化**：使用 LangGraph 动态工作流替代静态配置绑定，多 Agent 协作处理复杂任务，流程可视化可追踪。

---

## 许可证

MIT License

---

## 参考

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
- [Streamlit 文档](https://docs.streamlit.io)
