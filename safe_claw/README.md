# SafeClaw 🦞

> **TRASA (The Real AI Safety Assistant)** - 安全优先的本地 AI 助手
> 基于 LangGraph Deep Agents + 4层记忆系统 + 安全策略
> 安全优先 · 文件优先 · 隐私可控

---

## 🎯 项目概述

SafeClaw（安全之爪）是一个**安全优先**、**文件优先**的本地 AI 助手，采用 **LangGraph + Streamlit** 技术栈实现。具备完整的 4 层记忆系统、多 Agent 协作、安全策略和技能系统。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **🛡️ 安全优先** | 三级安全策略，敏感操作确认，完整审计日志 |
| **🧠 4层记忆系统** | Active/Dormant/Deep/Forgotten 智能记忆管理 |
| **🤖 多 Agent 架构** | Chat/Memory/Router/Safety Agent 协作 |
| **🔧 技能系统** | 文件操作、代码分析、可扩展技能框架 |
| **📊 可视化界面** | Streamlit 多页面应用，实时统计 |
| **🔒 本地优先** | 数据不出境，配置可编辑，完全透明 |

---

## 🏗️ 技术架构

### 核心组件
- **LangGraph 工作流**: 状态图驱动的多 Agent 协作
- **4层记忆系统**: 智能记忆分层和自动管理
- **安全检查器**: 实时安全策略和审计日志
- **技能框架**: 可扩展的工具和技能系统
- **LLM 网关**: 支持 OpenAI/Anthropic/Ollama

### 技术栈
- **Python 3.10+**
- **Streamlit** - Web 界面框架
- **LangGraph** - Deep Agents 状态图管理
- **LangChain** - 工具调用和 LLM 抽象
- **Pydantic** - 数据验证和配置管理

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- 8GB+ RAM 推荐
- OpenAI/Anthropic API 密钥

### 安装步骤

```bash
# 1. 克隆仓库
git clone <repository-url>
cd safe_claw

# 2. 创建环境
conda env create -f environment.yml
conda activate safe_claw

# 3. 配置 API 密钥
cp .env.example .env
# 编辑 .env 添加你的 API 密钥

# 4. 启动应用
streamlit run app.py
```

### 首次配置
1. 打开设置页面配置 LLM 提供商
2. 测试连接确保 API 密钥有效
3. 开始在聊天页面与 SafeClaw 对话

---

## 📁 项目结构

```
safe_claw/
├──                 # Streamlit UI 层
│   ├── app.py                   # 主应用入口
│   ├── pages/                   # 多页面
│   │   ├── 00_💬_Chat.py       # 主聊天页
│   │   ├── 01_📚_Memory.py     # 记忆管理
│   │   ├── 02_⚙️_Settings.py  # 设置页
│   │   └── 03_📊_Stats.py      # 统计页
│   ├── components/              # UI 组件
│   └── styles/                  # CSS 样式
│
├── core/                        # 核心业务层
│   ├── agents/                  # LangGraph Agents
│   ├── graph/                   # 工作流定义
│   ├── memory/                  # 4层记忆系统
│   ├── skills/                  # 技能系统
│   └── safety/                  # 安全策略
│
├── services/                    # 服务层
├── models/                      # 数据模型
├── utils/                       # 工具函数
├── workspace/                   # 用户数据
└── docs/                        # 文档
```

---

## 🧠 记忆系统

SafeClaw 采用 4 层智能记忆架构：

### Active Layer (活跃层)
- **容量**: 20 条记忆
- **内容**: 最近对话和重要信息
- **特点**: 快速访问，优先检索

### Dormant Layer (休眠层)
- **触发**: 重要性 ≥ 0.6 或 24 小时前
- **唤醒**: 关键词匹配阈值 0.6
- **特点**: 中等重要性，可被唤醒

### Deep Layer (深层层)
- **压缩**: 内容智能压缩存储
- **触发**: 重要性 < 0.6 或 30 天前
- **特点**: 长期存储，节省空间

### Forgotten Layer (遗忘层)
- **归档**: 重要性 < 0.2 或 1 年前
- **清理**: 定期清理机制
- **特点**: 可恢复，可永久删除

---

## 🛡️ 安全策略

### 三级安全策略

| 级别 | 操作类型 | 处理方式 |
|------|---------|---------|
| **黑名单** | `rm -rf /`, `format`, 系统破坏 | 完全禁止 |
| **确认级** | 文件删除、系统命令、网络请求 | 用户确认 |
| **白名单** | 文件读取、聊天、记忆查询 | 自动允许 |

### 安全特性
- **实时检查**: 所有操作实时安全验证
- **审计日志**: 完整的操作审计记录
- **策略引擎**: 可配置的安全策略
- **确认机制**: 危险操作二次确认

---

## 🔧 技能系统

### 内置技能

#### 文件操作技能
- `read_file` - 安全文件读取
- `write_file` - 文件写入
- `list_files` - 目录浏览
- `delete_file` - 文件删除（需确认）
- `create_directory` - 目录创建

#### 代码分析技能
- `analyze_code` - 代码结构分析
- `code_quality` - 代码质量检查
- `format_code` - 代码格式化

### 自定义技能
```python
from core.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    def __init__(self):
        super().__init__("my_skill", "My custom skill")
    
    def execute(self, **kwargs):
        # 技能实现
        return {"success": True, "result": "..."}
```

---

## 📊 使用界面

### 💬 聊天页面
- 实时对话界面
- 记忆上下文显示
- Agent 执行路径追踪
- 调试信息展示

### 📚 记忆管理
- 4层记忆浏览
- 记忆搜索和过滤
- 重要性调整
- 批量操作

### ⚙️ 设置页面
- LLM 配置
- 安全策略设置
- 记忆系统配置
- 连接测试

### 📊 统计页面
- 使用统计图表
- 性能指标
- 记忆分布
- 系统健康状态

---

## 🔄 工作流程

### 用户输入处理流程
1. **初始化** - 创建状态，设置会话
2. **记忆检索** - 搜索相关记忆
3. **路由决策** - 选择合适的 Agent
4. **Agent 执行** - 处理用户请求
5. **安全检查** - 验证操作安全性
6. **结果整合** - 生成响应
7. **记忆更新** - 存储新记忆

### 多 Agent 协作
- **Router Agent**: 智能路由决策
- **Chat Agent**: 主要对话处理
- **Memory Agent**: 记忆管理操作
- **Safety Agent**: 安全策略执行

---

## 📈 开发状态

### ✅ 已完成 (Phase 1 MVP)
- [x] 基础项目结构
- [x] 核心模型定义
- [x] LLM 网关服务
- [x] 4层记忆系统
- [x] LangGraph Agent 系统
- [x] Streamlit UI 界面
- [x] 安全策略层
- [x] 基础技能系统

### 🚧 进行中 (Phase 2)
- [ ] 向量搜索集成
- [ ] 更多内置技能
- [ ] 性能优化
- [ ] 错误处理增强

### 📋 计划中 (Phase 3)
- [ ] Graph 可视化编辑器
- [ ] 插件系统
- [ ] 多语言支持
- [ ] 分布式部署

---

## 🔧 配置说明

### 环境变量 (.env)
```bash
# LLM 配置
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# 安全设置
ENABLE_CONFIRMATION=true
SAFETY_LOG_LEVEL=INFO

# 记忆设置
ACTIVE_MEMORY_MAX=20
ENABLE_VECTOR_SEARCH=false
```

### 配置文件 (config.json)
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7
  },
  "safety": {
    "enable_confirmation": true,
    "blacklist_commands": ["rm -rf /", "format"]
  },
  "memory": {
    "active_memory_max": 20,
    "dormant_wakeup_threshold": 0.6
  }
}
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| **[📖 快速开始](STARTUP_GUIDE.md)** | 安装配置和启动指南 |
| **[🔧 开发指南](docs/DEVELOPMENT_GUIDELINES.md)** | 开发规范和常见错误 |
| **[📋 检查清单](docs/CHECKLIST.md)** | 代码质量和发布检查 |
| **[🧪 测试指南](tests/README.md)** | 测试策略和运行方法 |
| **[📋 API 文档](docs/API.md)** | 接口文档和示例 |

---

## 🤝 贡献指南

### 开发环境设置
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black .
flake8 .
```

### 贡献流程
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LangGraph](https://python.langchain.com/docs/langgraph) - 状态图工作流
- [Streamlit](https://docs.streamlit.io) - Web 应用框架
- [LangChain](https://python.langchain.com) - LLM 应用框架
- OpenClaw 项目 - 设计思想启发

---

**SafeClaw TRASA** - Version 0.1.0  
*The Real AI Safety Assistant* | Built with ❤️ for safety and privacy
