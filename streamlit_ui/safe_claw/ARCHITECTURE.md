# SafeClaw v2.0 架构设计

> 🦞 基于 LangGraph Deep Agents + OpenClaw 思想的本地 AI 助手

---

## 1. 核心设计理念

### 1.1 LangGraph Deep Agents 模式

采用 **LangGraph** 构建 Agent 工作流，将复杂任务分解为可组合、可路由的节点网络：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Graph (LangGraph)                       │
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│   │  Input   │───▶│  Router  │───▶│  Memory  │               │
│   │  Node    │    │   Node   │    │   Node   │               │
│   └──────────┘    └────┬─────┘    └────┬─────┘               │
│                        │               │                        │
│           ┌────────────┴───────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│   ┌───────────────┐    ┌──────────┐    ┌──────────┐          │
│   │  Supervisor   │───▶│  Agent A │───▶│  Agent B │          │
│   │    Node       │    │(Coding)  │    │(Analysis)│          │
│   └───────────────┘    └────┬─────┘    └────┬─────┘          │
│                             │               │                   │
│                             └───────────────┘                   │
│                                     │                            │
│                                     ▼                            │
│                             ┌──────────┐                        │
│                             │ Response │                        │
│                             │   Node   │                        │
│                             └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 借鉴 OpenClaw 的关键设计

| OpenClaw 特性 | SafeClaw 实现 |
|--------------|--------------|
| **多 Agent 隔离** | 每个 LangGraph 节点是一个独立 Agent，有自己的 Workspace |
| **文件优先配置** | AGENTS.md / SOUL.md / USER.md 驱动 Agent 行为 |
| **会话路由** | Graph 中的条件边实现智能路由 |
| **技能系统** | 节点可调用技能工具 |
| **本地优先** | 所有状态本地存储，可版本控制 |

### 1.3 与 OpenClaw 的差异化

| 维度 | OpenClaw | SafeClaw (LangGraph 版) |
|------|---------|------------------------|
| **Agent 编排** | 静态配置绑定 | LangGraph 动态工作流 |
| **任务分解** | 单 Agent 内部处理 | 多 Agent 协作 (Graph 节点) |
| **流程可视化** | 黑盒 | 可追踪的 Graph 执行路径 |
| **扩展性** | 插件系统 | 节点即插件，Graph 即流程 |
| **技术栈** | Node.js + 自建 | Python + LangGraph |
| **部署** | 守护进程 | Streamlit 单应用 |

---

## 2. 系统架构

### 2.1 分层架构图

```
┌────────────────────────────────────────────────────────────────────┐
│  UI Layer (Streamlit)                                               │
│  ├── Chat Interface    - 对话展示 + 流式响应                        │
│  ├── Graph Visualizer - 显示当前执行的工作流图                    │
│  ├── Session Manager  - 多会话切换                                │
│  ├── Workspace Editor - 编辑 AGENTS.md / SOUL.md                  │
│  └── Settings         - LLM 配置 + 安全配置                       │
├────────────────────────────────────────────────────────────────────┤
│  Application Layer                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                Session Graph Manager                         │  │
│  │  - 每个会话对应一个 LangGraph 实例                           │  │
│  │  - 管理 Graph 生命周期 (创建/保存/恢复)                      │  │
│  │  - 会话间状态隔离                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  Agent Graph Builder                       │  │
│  │  - 从配置文件动态构建 Graph                                  │  │
│  │  - 支持预定义模板 + 自定义 Graph                             │  │
│  │  - 节点注册与发现                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────┤
│  Domain Layer (LangGraph Nodes)                                      │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────────────┐  │
│  │  Input   │  Router  │  Memory  │  Skill   │  Response       │  │
│  │  Node    │  Node    │  Node    │  Node    │  Node           │  │
│  ├──────────┼──────────┼──────────┼──────────┼─────────────────┤  │
│  │  Supervisor │  Agent Nodes (by workspace)                   │  │
│  │  Node       │  - Coding Agent                               │  │
│  │             │  - Analysis Agent                             │  │
│  │             │  - Planning Agent                             │  │
│  │             │  - Execution Agent                             │  │
│  └──────────┴──────────┴─────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                                │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────────────┐     │
│  │  LLM     │  Memory  │  Skills  │  Safety  │  File Store     │     │
│  │  Gateway │  Store   │  Registry│  Layer   │  (Workspace)    │     │
│  └──────────┴──────────┴──────────┴──────────┴─────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 LangGraph State 定义

```python
class SafeClawState(TypedDict):
    """LangGraph 共享状态"""
    # 输入
    user_input: str                    # 用户原始输入
    session_id: str                    # 会话标识
    
    # 上下文
    messages: List[BaseMessage]        # 对话历史 (LangChain 格式)
    system_prompt: str                 # 组装后的系统提示词
    memories: List[str]                # 召回的相关记忆
    
    # Agent 执行
    current_agent: str                 # 当前执行的 Agent ID
    agent_outputs: Dict[str, Any]     # 各 Agent 的输出结果
    
    # 工具/技能
    tool_calls: List[ToolCall]         # 待执行的工具调用
    tool_results: List[ToolResult]     # 工具执行结果
    
    # 输出
    response: str                      # 最终响应
    stream_chunks: List[str]           # 流式输出块
    
    # 元数据
    execution_path: List[str]         # 执行路径（用于可视化）
    start_time: datetime
    end_time: Optional[datetime]
```

---

## 3. Graph 节点设计

### 3.1 核心节点

#### Input Node（输入处理）
```python
class InputNode:
    """处理用户输入，初始化状态"""
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 1. 加载会话配置
        # 2. 组装系统提示词 (AGENTS.md + SOUL.md + USER.md)
        # 3. 召回相关记忆
        return {
            **state,
            "system_prompt": self._build_system_prompt(),
            "memories": self._retrieve_memories(state["user_input"]),
            "execution_path": ["input"]
        }
```

#### Router Node（智能路由）
```python
class RouterNode:
    """根据输入决定执行路径"""
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 使用 LLM 或规则判断路由
        route = self._determine_route(state)
        return {**state, "current_agent": route}
    
    def _determine_route(self, state) -> str:
        # 简单关键词匹配 / LLM 意图识别
        # 返回: "coding" | "analysis" | "planning" | "execution" | "direct"
```

#### Agent Node（Agent 执行）
```python
class AgentNode:
    """特定领域 Agent 执行"""
    
    def __init__(self, agent_id: str, workspace_path: Path):
        self.agent_id = agent_id
        self.workspace = Workspace(workspace_path)
        self.llm_gateway = create_gateway()
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 1. 加载该 Agent 的专属配置
        system_prompt = self.workspace.get_agents_prompt()
        
        # 2. 组装消息
        messages = self._build_messages(state, system_prompt)
        
        # 3. 流式调用 LLM
        response = ""
        for chunk in self.llm_gateway.stream(messages):
            response += chunk
            state["stream_chunks"].append(chunk)
        
        # 4. 检测工具调用
        tool_calls = self._parse_tool_calls(response)
        
        return {
            **state,
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                self.agent_id: response
            },
            "tool_calls": tool_calls,
            "execution_path": [*state["execution_path"], self.agent_id]
        }
```

#### Memory Node（记忆管理）
```python
class MemoryNode:
    """提取和保存记忆"""
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 1. 从对话中提取重要信息
        memories = self._extract_memories(state)
        
        # 2. 保存到文件
        for memory in memories:
            self.memory_store.add(memory)
        
        return state
    
    def _extract_memories(self, state) -> List[str]:
        # 使用 LLM 判断哪些内容值得长期保存
        prompt = f"""
        分析以下对话，提取需要长期记住的重要信息：
        用户: {state['user_input']}
        助手: {state['response']}
        
        只返回具体的事实、偏好或决策，每行一个。
        """
        return self.llm.extract_memories(prompt)
```

#### Skill Node（技能执行）
```python
class SkillNode:
    """执行技能/工具"""
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        results = []
        for tool_call in state["tool_calls"]:
            # 安全检查
            if not self.safety.check(tool_call):
                results.append({"error": "安全检查未通过"})
                continue
            
            # 执行技能
            result = self.skill_registry.execute(
                tool_call["name"],
                tool_call["arguments"]
            )
            results.append(result)
        
        return {**state, "tool_results": results}
```

### 3.2 Graph 构建示例

#### 简单对话图
```python
def build_simple_graph() -> StateGraph:
    """最简单的单 Agent 对话"""
    graph = StateGraph(SafeClawState)
    
    # 添加节点
    graph.add_node("input", InputNode())
    graph.add_node("agent", AgentNode("default", DEFAULT_WORKSPACE))
    graph.add_node("memory", MemoryNode())
    graph.add_node("response", ResponseNode())
    
    # 添加边
    graph.set_entry_point("input")
    graph.add_edge("input", "agent")
    graph.add_edge("agent", "memory")
    graph.add_edge("memory", "response")
    graph.add_edge("response", END)
    
    return graph.compile()
```

#### 多 Agent 协作图
```python
def build_multi_agent_graph() -> StateGraph:
    """多 Agent 协作处理复杂任务"""
    graph = StateGraph(SafeClawState)
    
    # 节点
    graph.add_node("input", InputNode())
    graph.add_node("router", RouterNode())
    graph.add_node("planner", AgentNode("planner", PLANNER_WORKSPACE))
    graph.add_node("executor", AgentNode("executor", EXECUTOR_WORKSPACE))
    graph.add_node("reviewer", AgentNode("reviewer", REVIEWER_WORKSPACE))
    graph.add_node("skill", SkillNode())
    graph.add_node("memory", MemoryNode())
    
    # 入口
    graph.set_entry_point("input")
    graph.add_edge("input", "router")
    
    # 条件路由
    graph.add_conditional_edges(
        "router",
        lambda state: state["current_agent"],
        {
            "direct": "response",
            "planning": "planner",
            "execution": "executor",
        }
    )
    
    # Planning -> Execution -> Reviewer 链
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "skill")
    graph.add_edge("skill", "reviewer")
    
    # 条件循环：如果 reviewer 不通过，回到 executor
    graph.add_conditional_edges(
        "reviewer",
        lambda state: "retry" if state.get("needs_retry") else "done",
        {"retry": "executor", "done": "memory"}
    )
    
    graph.add_edge("memory", END)
    
    return graph.compile()
```

---

## 4. 工作区结构（多 Agent）

```
~/.safe_claw/
├── config.json                      # 主配置
├── sessions/                        # 会话状态（每个会话一个 Graph 实例）
│   ├── default.json
│   └── {session_id}.json
│
├── agents/                          # 多 Agent 配置（类似 OpenClaw）
│   ├── default/                     # 默认 Agent
│   │   ├── AGENTS.md               # Agent 提示词
│   │   ├── SOUL.md                 # 人格定义
│   │   ├── USER.md                 # 用户偏好
│   │   └── skills/                 # Agent 专属技能
│   │
│   ├── coding/                      # 编程 Agent
│   │   ├── AGENTS.md
│   │   ├── SOUL.md
│   │   └── skills/
│   │       └── code_analyzer/
│   │
│   ├── analysis/                    # 分析 Agent
│   │   ├── AGENTS.md
│   │   └── SOUL.md
│   │
│   └── planning/                    # 规划 Agent
│       ├── AGENTS.md
│       └── SOUL.md
│
├── memory/                          # 全局记忆（跨 Agent 共享）
│   ├── 2026-03-22.md
│   └── index/
│
├── shared_skills/                   # 共享技能（所有 Agent 可用）
│   └── file_operations/
│
└── graphs/                          # Graph 定义（可选自定义）
    ├── default.json                 # 简单对话图
    └── multi_agent.json             # 多 Agent 协作图
```

---

## 5. 关键技术决策

### 5.1 为什么用 LangGraph？

| 优势 | 说明 |
|------|------|
| **可视化** | Graph 结构天然可追踪、可调试 |
| **模块化** | 每个节点独立开发和测试 |
| **灵活性** | 条件边支持复杂路由逻辑 |
| **状态管理** | 内置状态流转和持久化 |
| **生态** | 与 LangChain/LangSmith 生态兼容 |

### 5.2 Agent vs Node 的关系

```
Agent (概念) = Node (LangGraph 实现)

每个 Agent 是一个 Node 类，包含：
- 自己的 Workspace (AGENTS.md, SOUL.md, skills/)
- 自己的 LLM 配置
- 自己的工具集

多个 Agent Nodes 通过 Edge 连接成 Graph
```

### 5.3 会话与 Graph 实例

```
Session 1 ──▶ Graph Instance A (独立状态)
Session 2 ──▶ Graph Instance B (独立状态)
Session 3 ──▶ Graph Instance C (独立状态)

每个会话 = 一个 LangGraph 运行时实例
会话持久化 = 序列化 Graph 状态到文件
```

---

## 6. 实现路线图

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

## 7. 依赖项

```
# 核心
langgraph>=0.0.50
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0

# UI
streamlit>=1.28.0
streamlit-graphviz>=0.0.1  # Graph 可视化

# 配置与存储
pydantic>=2.0.0
python-dotenv>=1.0.0

# 可选
chromadb>=0.4.0          # 向量记忆
keyring>=24.0.0          # 密钥存储
```

---

## 8. 与参考项目的关系

| 来源 | 借鉴内容 | SafeClaw 实现 |
|------|---------|--------------|
| **OpenClaw** | 文件优先、多 Agent 隔离、Workspace 结构 | 完全一致 |
| **OpenClaw** | Agent/Session/Binding 概念 | 对应 Node/Session/Edge |
| **LangGraph** | Graph 工作流、状态管理 | 核心架构 |
| **LangGraph** | Supervisor/Worker 模式 | Multi-Agent Graph |
| **SafeClaw v1** | 安全控制层 | 保留并强化 |
