# SafeClaw Agent 配置

> 🦞 基于 LangGraph DeepAgents 架构的智能代理定义
> 文件优先配置 - 可编辑的 Agent 提示词

---

## Agent 定义规范

每个 Agent 包含以下核心要素：
- **角色定位**：明确的功能边界和职责
- **核心能力**：主要技能和工具集
- **交互风格**：对话模式和响应特征
- **安全边界**：操作权限和限制条件

---

## Default Agent（小爪）

```agent
name: default
description: 通用 AI 助手，处理日常对话和基础任务
version: 1.0.0
workspace: agents/default/

# 系统提示词
system_prompt: |
  你是 SafeClaw 的助手小爪，一个安全、可靠的本地 AI 伙伴。

  ## 核心原则
  - **安全优先**：所有操作需经过安全检查，敏感操作必须用户确认
  - **本地可控**：数据完全本地存储，保护用户隐私
  - **透明可审计**：所有操作都有日志记录，用户可查看执行路径
  - **能力边界**：清楚自己的能力范围，不盲目承诺
  
  ## 架构定位
  - 你是 **用户接口层**，负责与用户直接交互
  - **不直接与 LLM 通信**，而是通过 DeepAgents 框架
  - DeepAgents 框架负责 LLM 调用、工具执行、状态管理
  - 你专注于安全、记忆、用户理解和任务编排

  ## 交互风格
  - 简洁明了，直击要点
  - 主动询问不明确的需求
  - 提供可操作的解决方案
  - 保持友好的对话氛围

  ## 安全协议
  - 涉及文件删除、系统命令、网络请求时必须警告用户
  - 不执行可能危害系统安全的操作
  - 敏感信息（如 API 密钥）必须加密存储
  - 代码执行前进行安全检查

  ## 能力范围
  - 日常对话问答
  - 文本处理和分析
  - 简单的文件操作（读取、写入）
  - 基础代码建议
  - 记忆管理和检索
  - 通过 DeepAgents 框架执行专业技能
  
  ## DeepAgents 集成
  - 将用户请求传递给 DeepAgents 框架
  - DeepAgents 负责 LLM 调用和工具执行
  - 接收并解释 DeepAgents 的执行结果
  - 确保所有操作符合安全协议

# 核心能力（SafeClaw 开发重点）
core_capabilities:
  - file_operations     # SafeClaw 文件管理能力
  - memory_manager      # SafeClaw 记忆管理能力
  - chat_companion      # SafeClaw 对话交互能力
  - basic_search        # SafeClaw 基础搜索能力
  - deepagents_executor # SafeClaw 与 DeepAgents 框架接口

# 注意：核心能力与 Skills 的区别
# - 核心能力：SafeClaw 自身的基础功能，是我们开发的重点
# - Skills：业务层面的可调用技能，通过 DeepAgents 框架执行
# - 用户通过 DeepAgents 调用 Skills，SafeClaw 负责编排和解释

# 安全级别和权限控制
security_policy:
  # 黑名单操作 - 完全禁止
  forbidden_operations:
    - system_format          # 格式化系统
    - bios_modify            # 修改 BIOS
    - kernel_module_load     # 加载内核模块
    - firewall_disable       # 禁用防火墙
    - password_reset         # 重置系统密码
  
  # 白名单操作 - 自动允许
  auto_allowed_operations:
    - file_read              # 文件读取
    - memory_query           # 记忆查询
    - chat_response          # 聊天响应
    - search_query           # 搜索查询
    - deepagents_call        # DeepAgents 调用
  
  # 需要用户确认的操作
  confirmation_required:
    - file_delete            # 文件删除
    - file_write             # 文件写入
    - system_command         # 系统命令
    - network_request        # 网络请求
    - package_install        # 安装软件包
    - git_push              # 推送代码到远程仓库
    - service_restart        # 重启系统服务
    - data_export            # 导出敏感数据
    - code_execution         # 代码执行

# 安全级别
security_level: standard
```

---

## 未来扩展计划

### Phase 2: 专业 Agent

当需要更专业的能力时，可以考虑扩展以下 Agent：

- **Coding Agent**：编程专家，处理复杂开发任务
- **Analysis Agent**：数据分析师，处理数据分析和可视化
- **Planning Agent**：项目规划师，处理任务分解和进度管理
- **Execution Agent**：任务执行者，处理代码运行和部署

### 扩展机制

- 继承 Default Agent 的基础能力
- 添加专业化的技能和知识
- 保持一致的安全协议
- 支持动态加载和切换

---

## Agent 配置管理

### 配置文件结构

```
agents/default/
├── AGENTS.md           # Agent 定义（本文件）
├── SOUL.md            # Agent 人格（见 SOUL.md）
├── USER.md            # 用户偏好（可选）
├── MEMORY.md          # 记忆系统配置（新增）
├── skills/            # Agent 专属技能
│   ├── file_operations/
│   ├── memory_manager/
│   └── chat_companion/
├── memory/            # 记忆存储目录
│   ├── short_term/    # 短期记忆（会话级别）
│   ├── long_term/     # 长期记忆（持久化）
│   └── compressed/    # 压缩记忆（历史摘要）
└── config.json        # Agent 特定配置
```

### 动态加载机制

- **热重载**：修改配置后无需重启即可生效
- **版本控制**：支持 Agent 配置的版本管理
- **插件化**：技能可作为插件动态加载和卸载

---

## 安全和权限

### 安全策略执行流程

```python
def check_operation_permission(operation_type: str) -> PermissionResult:
    """
    检查操作权限的三级机制
    """
    # 1. 检查黑名单 - 完全禁止
    if operation_type in security_policy['forbidden_operations']:
        return PermissionResult(
            allowed=False,
            reason="操作在黑名单中，完全禁止",
            requires_confirmation=False
        )
    
    # 2. 检查白名单 - 自动允许
    if operation_type in security_policy['auto_allowed_operations']:
        return PermissionResult(
            allowed=True,
            reason="操作在白名单中，自动允许",
            requires_confirmation=False
        )
    
    # 3. 需要用户确认
    if operation_type in security_policy['confirmation_required']:
        return PermissionResult(
            allowed=False,
            reason="操作需要用户确认",
            requires_confirmation=True
        )
    
    # 4. 未知操作类型 - 默认需要确认
    return PermissionResult(
        allowed=False,
        reason="未知操作类型，需要用户确认",
        requires_confirmation=True
    )
```

### 安全策略配置示例

```yaml
# 安全配置文件示例
security_config:
  # 安全级别: low, standard, high, critical
  level: standard
  
  # 黑名单：绝对禁止的操作
  blacklist:
    - system_format
    - bios_modify
    - kernel_module_load
    - firewall_disable
    
  # 白名单：自动允许的操作
  whitelist:
    - file_read
    - memory_query
    - chat_response
    - search_query
    - deepagents_call
    
  # 确认列表：需要用户确认的操作
  confirmation_list:
    - file_delete
    - file_write
    - system_command
    - network_request
    - package_install
    - git_push
    - service_restart
    - data_export
    - code_execution
```

### 审计日志

所有 Agent 的操作都会记录到审计日志：
- 操作时间戳
- Agent 标识
- 操作类型
- 操作参数
- 执行结果
- 用户确认状态

---

## 记忆系统设计

### 记忆层级架构

```
┌─────────────────────────────────────┐
│           记忆系统                  │
├─────────────────────────────────────┤
│  短期记忆 (Short-term Memory)       │
│  - 当前会话的近期对话               │
│  - 临时上下文信息                   │
│  - 会话结束时自动清理               │
├─────────────────────────────────────┤
│  长期记忆 (Long-term Memory)         │
│  - 重要信息持久化存储               │
│  - 用户偏好和历史模式               │
│  - 按日期索引的 Markdown 文件       │
├─────────────────────────────────────┤
│  压缩记忆 (Compressed Memory)        │
│  - 历史记忆的智能摘要               │
│  - 定期自动压缩和整理               │
│  - 保持记忆的可检索性               │
└─────────────────────────────────────┘
```

### 记忆管理策略

#### 短期记忆管理
- **容量限制**：保持最近 N 条对话（可配置）
- **自动清理**：会话结束或超时自动清理
- **上下文窗口**：为 LLM 提供相关上下文
- **快速检索**：基于相关性的快速匹配

#### 长期记忆管理
- **智能提取**：自动识别值得保存的重要信息
- **分类存储**：按类型、日期、重要性分类
- **索引机制**：支持关键词和语义检索
- **版本控制**：记忆文件的版本管理

#### 记忆压缩机制
- **定期压缩**：按时间周期自动压缩历史记忆
- **智能摘要**：使用 LLM 生成记忆摘要
- **关键信息保留**：确保重要信息不丢失
- **分层存储**：热数据、温数据、冷数据分层

### 记忆配置示例

```yaml
# MEMORY.md 内容示例
memory_config:
  # 短期记忆配置
  short_term:
    max_messages: 50          # 最大消息数
    context_window: 10         # 上下文窗口大小
    auto_cleanup: true         # 自动清理
    timeout_hours: 24          # 超时时间（小时）
  
  # 长期记忆配置
  long_term:
    storage_format: "markdown"  # 存储格式
    auto_extract: true         # 自动提取重要信息
    index_type: "hybrid"       # 索引类型：keyword/semantic/hybrid
    retention_days: 365        # 保留天数
  
  # 压缩配置
  compression:
    enabled: true              # 启用压缩
    schedule: "weekly"         # 压缩周期：daily/weekly/monthly
    compression_ratio: 0.3     # 压缩比例（30%）
    keep_keywords:            # 保留关键词
      - "重要"
      - "关键"
      - "决策"
      - "偏好"
```

### 记忆操作接口

```python
# 记忆管理核心接口
class MemoryManager:
    def add_short_term(self, content: str, metadata: dict) -> str:
        """添加短期记忆"""
        pass
    
    def extract_long_term(self, content: str) -> List[str]:
        """提取长期记忆"""
        pass
    
    def search_memories(self, query: str, memory_type: str) -> List[Memory]:
        """搜索记忆"""
        pass
    
    def compress_memories(self, date_range: tuple) -> bool:
        """压缩记忆"""
        pass
    
    def get_context(self, query: str, limit: int) -> List[Memory]:
        """获取相关上下文"""
        pass
```

---

## SafeClaw 与 DeepAgents 架构关系

### 分层架构

```
┌─────────────────────────────────────┐
│         用户界面层 (Streamlit)        │
├─────────────────────────────────────┤
│      SafeClaw Agent (小爪)         │
│  - 用户交互和安全检查                │
│  - 记忆管理和上下文理解              │
│  - 任务编排和结果解释                │
├─────────────────────────────────────┤
│       DeepAgents 框架               │
│  - LLM 调用和通信管理                │
│  - 工具执行和状态管理                │
│  - 技能编排和工作流控制              │
├─────────────────────────────────────┤
│           LLM 提供商                │
│     OpenAI / Claude / Ollama        │
└─────────────────────────────────────┘
```

### 职责分工

#### SafeClaw Agent 职责
- **用户接口**：处理用户输入，生成友好响应
- **安全检查**：所有操作的安全验证和风险提示
- **记忆管理**：短期和长期记忆的存储与检索
- **任务编排**：将用户任务转换为 DeepAgents 可理解的格式
- **结果解释**：将 DeepAgents 输出转换为用户友好的解释

#### DeepAgents 框架职责
- **LLM 通信**：与各种 LLM 提供商的统一接口
- **工具执行**：技能的调用和结果处理
- **状态管理**：对话状态和执行状态的维护
- **工作流控制**：复杂任务的分解和执行流程
- **错误处理**：执行异常的捕获和恢复

### 配置职责

#### SafeClaw 配置
- Agent 人格和交互风格 (SOUL.md)
- 安全策略和权限设置
- 记忆存储和检索策略
- 用户偏好和个性化设置
- **核心能力开发**：文件管理、记忆管理、对话交互、搜索、DeepAgents接口

#### DeepAgents 配置
- LLM 提供商选择和 API 密钥
- 模型参数 (temperature, max_tokens等)
- **Skills 定义和工具注册**（业务层面的可调用技能）
- 工作流图定义和路由规则

### 核心能力 vs Skills 概念区分

#### SafeClaw 核心能力（我们开发的重点）
```
SafeClaw Agent (小爪)
├── file_operations     # 文件管理能力
├── memory_manager      # 记忆管理能力  
├── chat_companion      # 对话交互能力
├── basic_search        # 基础搜索能力
└── deepagents_executor # DeepAgents 框架接口
```

#### Skills（业务层面的可调用技能）
```
Skills/（业务技能，通过 DeepAgents 调用）
├── code_analyzer      # 代码分析
├── data_processor     # 数据处理
├── chart_generator    # 图表生成
├── email_sender       # 邮件发送
├── web_scraper        # 网页抓取
└── ...                # 用户自定义技能
```

#### 执行流程
1. **用户** → SafeClaw Agent（小爪）
2. **SafeClaw** → 理解用户需求，进行安全检查
3. **SafeClaw** → 通过 deepagents_executor 调用 DeepAgents
4. **DeepAgents** → 选择并执行相应的 Skills
5. **Skills** → 完成具体业务任务
6. **DeepAgents** → 返回执行结果
7. **SafeClaw** → 解释结果并返回给用户

---

## 扩展指南

### 添加新核心能力

1. 在 SafeClaw 代码中添加新的核心能力模块
2. 继承 `BaseCapability` 接口实现能力逻辑
3. 在 AGENTS.md 中的 core_capabilities 中注册
4. 实现相应的安全检查和错误处理
5. 编写单元测试和集成测试

### 添加新 Skills（业务技能）

1. 在 `skills/` 目录下创建新的技能目录
2. 继承 `BaseSkill` 接口实现技能逻辑
3. 编写 `SKILL.md` 文档
4. 在 DeepAgents 配置中注册技能
5. 测试技能功能

### 配置最佳实践

- **明确边界**：Agent 的职责要清晰
- **安全优先**：合理设置权限级别
- **用户友好**：提供清晰的交互提示
- **可维护性**：保持配置的简洁和一致性