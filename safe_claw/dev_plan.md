# SafeClaw TRASA 开发方案与实施计划

> **项目代号**: TRASA (The Real AI Safety Assistant)  
> **技术栈**: Streamlit + LangGraph DeepAgents + Python 3.10+  
> **目标**: 构建安全优先、文件优先的本地AI助手

---

## 📋 执行摘要

基于对以下文档的深入分析：
- **ARCHITECTURE.md** - LangGraph Deep Agents架构设计
- **MEMORY.md** - 四层记忆系统设计
- **PRD.md** - 产品需求文档
- **mockup图片** - UI/UX设计参考

本计划采用**三阶段递进式**开发模式，优先实现 **MVP → 核心功能 → 高级特性**。

---

## 🎯 第一阶段：基础架构搭建 (2-3周)

### 目标
构建可运行的 MVP，实现**单 Agent 对话 + 基础记忆 + 简单技能**

### 1.1 环境与项目初始化

#### 任务清单
- [x] ✅ 已有环境配置 (environment.yml, requirements.txt)
- [ ] 创建标准项目结构
- [ ] 配置开发环境 (Conda/venv)
- [ ] 初始化 Git 仓库和分支策略

#### 项目结构 (最终目标)
```
safe_claw/
├──                 # Streamlit UI 层
│   ├── __init__.py
│   ├── app.py                   # 主入口
│   ├── pages/                   # 多页面
│   │   ├── 00_💬_Chat.py       # 主聊天页
│   │   ├── 01_📚_Memory.py     # 记忆浏览
│   │   ├── 02_⚙️_Settings.py  # 设置页
│   │   └── 03_📊_Stats.py      # 统计页
│   ├── components/              # UI 组件
│   │   ├── sidebar.py          # 侧边栏
│   │   ├── chat_message.py     # 消息组件
│   │   ├── session_manager.py  # 会话管理器
│   │   └── memory_browser.py   # 记忆浏览器
│   └── styles/                  # CSS 样式
│       └── custom.css
│
├── core/                        # 核心业务层
│   ├── __init__.py
│   ├── agents/                  # LangGraph Agents
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Agent 基类
│   │   ├── chat_agent.py       # 对话 Agent
│   │   ├── router_agent.py     # 路由 Agent
│   │   └── memory_agent.py     # 记忆 Agent
│   │
│   ├── graph/                   # LangGraph 工作流
│   │   ├── __init__.py
│   │   ├── state.py            # 状态定义
│   │   ├── nodes.py            # 节点实现
│   │   ├── builder.py          # Graph 构建器
│   │   └── templates/          # Graph 模板
│   │       ├── simple_chat.py  # 简单对话图
│   │       └── multi_agent.py  # 多 Agent 图
│   │
│   ├── memory/                  # 记忆系统
│   │   ├── __init__.py
│   │   ├── manager.py          # 记忆管理器
│   │   ├── storage.py          # 文件存储
│   │   ├── retriever.py        # 记忆检索
│   │   ├── layers/             # 记忆层级
│   │   │   ├── active.py       # 活跃记忆
│   │   │   ├── dormant.py      # 沉睡记忆
│   │   │   ├── deep.py         # 深层记忆
│   │   │   └── forgotten.py    # 遗忘记忆
│   │   └── wakeup/             # 唤醒机制
│   │       ├── keyword.py      # 关键词唤醒
│   │       ├── context.py      # 情境唤醒
│   │       ├── time.py         # 时间唤醒
│   │       └── emotion.py      # 情绪唤醒
│   │
│   ├── skills/                  # 技能系统
│   │   ├── __init__.py
│   │   ├── base_skill.py       # Skill 基类
│   │   ├── registry.py         # 技能注册表
│   │   ├── adapter.py          # Tool 适配器
│   │   └── built_in/           # 内置技能
│   │       ├── file_ops.py     # 文件操作
│   │       ├── code_analyzer.py # 代码分析
│   │       └── web_search.py   # 网络搜索
│   │
│   └── safety/                  # 安全控制层
│       ├── __init__.py
│       ├── checker.py          # 安全检查器
│       ├── policies.py         # 安全策略
│       └── audit.py            # 审计日志
│
├── services/                    # 服务层
│   ├── __init__.py
│   ├── llm_gateway.py          # LLM 调用网关
│   ├── session_service.py      # 会话服务
│   └── config_service.py       # 配置服务
│
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── config.py               # 配置模型
│   ├── session.py              # 会话模型
│   ├── memory.py               # 记忆模型
│   └── message.py              # 消息模型
│
├── utils/                       # 工具函数
│   ├── __init__.py
│   ├── file_utils.py
│   ├── logger.py
│   └── encryption.py
│
├── workspace/                   # 工作区配置 (用户数据)
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── USER.md
│   ├── config.json
│   └── skills/                 # 用户自定义技能
│
├── tests/                       # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                        # 文档
│   ├── ARCHITECTURE.md
│   ├── MEMORY.md
│   ├── PRD.md
│   └── API.md
│
├── .env.example
├── .gitignore
├── requirements.txt
├── environment.yml
├── setup.py
└── README.md
```

### 1.2 核心模型定义

#### 优先级：P0 (必须完成)

**State 模型** (`core/graph/state.py`)
```python
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage

class SafeClawState(TypedDict):
    """LangGraph 共享状态"""
    # 输入
    user_input: str
    session_id: str
    
    # 消息历史
    messages: List[BaseMessage]
    system_prompt: str
    
    # 记忆
    active_memories: List[Dict]
    dormant_memories: List[Dict]
    deep_memories: List[Dict]
    
    # Agent 执行
    current_agent: str
    agent_outputs: Dict[str, Any]
    
    # 技能/工具
    tool_calls: List[Dict]
    tool_results: List[Dict]
    
    # 输出
    response: str
    stream_chunks: List[str]
    
    # 元数据
    execution_path: List[str]
    start_time: datetime
    needs_confirmation: bool
    confirmed: bool
```

**Config 模型** (`models/config.py`)
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class LLMConfig(BaseModel):
    provider: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)

class SafetyConfig(BaseModel):
    enable_confirmation: bool = True
    blacklist_commands: List[str] = [
        "rm -rf /", "format", "mkfs"
    ]
    whitelist_operations: List[str] = [
        "read_file", "chat"
    ]

class MemoryConfig(BaseModel):
    enable_vector_search: bool = False
    active_memory_max: int = 20
    dormant_wakeup_threshold: float = 0.6
    deep_memory_compression: str = "maximum"
```

### 1.3 LLM Gateway 实现

#### 优先级：P0

**统一 LLM 接口** (`services/llm_gateway.py`)
```python
from abc import ABC, abstractmethod
from typing import Iterator, List, Dict
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class BaseLLMGateway(ABC):
    @abstractmethod
    def stream(self, messages: List[Dict]) -> Iterator[str]:
        """流式调用 LLM"""
        pass
    
    @abstractmethod
    def invoke(self, messages: List[Dict]) -> str:
        """同步调用 LLM"""
        pass

class OpenAIGateway(BaseLLMGateway):
    def __init__(self, config: LLMConfig):
        self.llm = ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            streaming=True
        )
    
    def stream(self, messages: List[Dict]) -> Iterator[str]:
        for chunk in self.llm.stream(messages):
            yield chunk.content

class GatewayFactory:
    @staticmethod
    def create(config: LLMConfig) -> BaseLLMGateway:
        if config.provider == "openai":
            return OpenAIGateway(config)
        elif config.provider == "anthropic":
            return AnthropicGateway(config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")
```

### 1.4 简单 LangGraph 实现

#### 优先级：P0

**基础对话 Graph** (`core/graph/templates/simple_chat.py`)
```python
from langgraph.graph import StateGraph, END
from core.graph.state import SafeClawState
from core.graph.nodes import InputNode, ChatNode, MemoryNode, ResponseNode

def build_simple_chat_graph():
    """最简单的单 Agent 对话流程"""
    graph = StateGraph(SafeClawState)
    
    # 添加节点
    graph.add_node("input", InputNode())
    graph.add_node("chat", ChatNode())
    graph.add_node("memory", MemoryNode())
    graph.add_node("response", ResponseNode())
    
    # 定义边
    graph.set_entry_point("input")
    graph.add_edge("input", "chat")
    graph.add_edge("chat", "memory")
    graph.add_edge("memory", "response")
    graph.add_edge("response", END)
    
    return graph.compile()
```

**节点实现** (`core/graph/nodes.py`)
```python
class InputNode:
    """输入处理节点"""
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 1. 加载系统提示词
        system_prompt = self._load_system_prompt()
        
        # 2. 检索活跃记忆
        active_memories = self.memory_manager.get_active()
        
        return {
            **state,
            "system_prompt": system_prompt,
            "active_memories": active_memories,
            "execution_path": ["input"]
        }

class ChatNode:
    """对话生成节点"""
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 1. 组装消息
        messages = self._build_messages(state)
        
        # 2. 流式调用 LLM
        response = ""
        for chunk in self.llm_gateway.stream(messages):
            response += chunk
            # 这里需要通过 Streamlit callback 实时显示
        
        return {
            **state,
            "response": response,
            "execution_path": [*state["execution_path"], "chat"]
        }

class MemoryNode:
    """记忆更新节点"""
    def __call__(self, state: SafeClawState) -> SafeClawState:
        # 提取重要信息作为长期记忆
        memories = self._extract_memories(
            state["user_input"], 
            state["response"]
        )
        self.memory_manager.add_memories(memories)
        
        return state
```

### 1.5 基础 Streamlit UI

#### 优先级：P0

**主应用** (`app.py`)
```python
import streamlit as st
from core.graph.templates.simple_chat import build_simple_chat_graph

st.set_page_config(
    page_title="SafeClaw TRASA",
    page_icon="🦞",
    layout="wide"
)

# 初始化会话状态
if "graph" not in st.session_state:
    st.session_state.graph = build_simple_chat_graph()
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("Ask me anything..."):
    # 添加用户消息
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用 Graph 生成响应
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # 执行 Graph
        state = {
            "user_input": prompt,
            "session_id": "default",
            "messages": st.session_state.messages,
            # ... 其他状态
        }
        
        result = st.session_state.graph.invoke(state)
        
        response_placeholder.markdown(result["response"])
        
    # 保存助手消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"]
    })
```

### 1.6 基础记忆系统

#### 优先级：P1 (重要但可延后)

**记忆管理器** (`core/memory/manager.py`)
```python
class MemoryManager:
    """记忆管理器 - 文件优先"""
    
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path
        self.active_dir = workspace_path / "memory" / "active"
        self.dormant_dir = workspace_path / "memory" / "dormant"
        self.deep_dir = workspace_path / "memory" / "deep"
    
    def add_memory(self, content: str, memory_type: str = "active"):
        """添加记忆"""
        memory = {
            "id": str(uuid.uuid4()),
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": memory_type
        }
        
        # 写入文件
        if memory_type == "active":
            self._save_to_active(memory)
        elif memory_type == "dormant":
            self._save_to_dormant(memory)
    
    def get_active_memories(self, limit: int = 10) -> List[Dict]:
        """获取活跃记忆"""
        memories = []
        for file in sorted(self.active_dir.glob("*.json")):
            with open(file) as f:
                memories.append(json.load(f))
        return memories[-limit:]  # 返回最近的
    
    def search_memories(self, query: str) -> List[Dict]:
        """搜索记忆（简单关键词匹配）"""
        results = []
        for dir_path in [self.active_dir, self.dormant_dir, self.deep_dir]:
            for file in dir_path.glob("*.json"):
                with open(file) as f:
                    memory = json.load(f)
                    if query.lower() in memory["content"].lower():
                        results.append(memory)
        return results
```

---

## 🚀 第二阶段：核心功能实现 (3-4周)

### 目标
实现**多 Agent 协作 + 技能系统 + 完整记忆系统 + 安全控制**

### 2.1 多 Agent Graph 实现

#### 优先级：P0

**多 Agent 协作图** (`core/graph/templates/multi_agent.py`)
```python
def build_multi_agent_graph():
    """多 Agent 协作处理复杂任务"""
    graph = StateGraph(SafeClawState)
    
    # 节点
    graph.add_node("input", InputNode())
    graph.add_node("router", RouterNode())
    graph.add_node("planner", PlannerAgent())
    graph.add_node("executor", ExecutorAgent())
    graph.add_node("reviewer", ReviewerAgent())
    graph.add_node("skill", SkillNode())
    graph.add_node("memory", MemoryNode())
    
    # 入口
    graph.set_entry_point("input")
    graph.add_edge("input", "router")
    
    # 条件路由
    graph.add_conditional_edges(
        "router",
        route_decision,  # 决策函数
        {
            "simple": "executor",     # 简单任务直接执行
            "complex": "planner",     # 复杂任务先规划
            "memory_only": "memory"   # 仅记忆查询
        }
    )
    
    # Planning -> Execution -> Review 链
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "skill")
    graph.add_edge("skill", "reviewer")
    
    # 条件循环：Review 不通过则重试
    graph.add_conditional_edges(
        "reviewer",
        lambda state: "retry" if state.get("needs_retry") else "done",
        {"retry": "executor", "done": "memory"}
    )
    
    graph.add_edge("memory", END)
    
    return graph.compile()
```

**路由节点** (`core/agents/router_agent.py`)
```python
class RouterNode:
    """智能路由节点 - 根据输入决定执行路径"""
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        user_input = state["user_input"]
        
        # 使用 LLM 判断意图
        intent = self._classify_intent(user_input)
        
        route = "simple"
        if intent in ["coding", "analysis", "planning"]:
            route = "complex"
        elif intent == "memory_search":
            route = "memory_only"
        
        return {
            **state,
            "current_agent": route,
            "execution_path": [*state["execution_path"], "router"]
        }
    
    def _classify_intent(self, text: str) -> str:
        """使用 LLM 分类意图"""
        prompt = f"""
        分类以下用户请求的意图类型：
        - simple: 简单对话
        - coding: 需要编程辅助
        - analysis: 需要数据分析
        - planning: 需要制定计划
        - memory_search: 查询历史记忆
        
        用户输入: {text}
        
        只返回意图类型，无需解释。
        """
        return self.llm_gateway.invoke([{"role": "user", "content": prompt}]).strip()
```

### 2.2 技能系统实现

#### 优先级：P0

**技能基类** (`core/skills/base_skill.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class SkillMetadata(BaseModel):
    """技能元数据"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    returns: Dict[str, Any]
    examples: List[str]
    requires_confirmation: bool = False

class BaseSkill(ABC):
    """技能基类 - 所有技能必须继承"""
    
    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata:
        """返回技能元数据"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行技能"""
        pass
    
    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
        # 基于 JSON Schema 验证
        return True
```

**文件操作技能** (`core/skills/built_in/file_ops.py`)
```python
class FileReadSkill(BaseSkill):
    """文件读取技能"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="read_file",
            description="读取文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path"]
            },
            returns={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "size": {"type": "integer"}
                }
            },
            examples=[
                "读取 README.md",
                "read_file(file_path='config.json')"
            ],
            requires_confirmation=False  # 读操作不需确认
        )
    
    def execute(self, file_path: str, encoding: str = "utf-8") -> Dict:
        """执行文件读取"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return {
                "success": True,
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

**技能注册表** (`core/skills/registry.py`)
```python
class SkillRegistry:
    """技能注册与发现"""
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill):
        """注册技能"""
        self._skills[skill.metadata.name] = skill
    
    def discover_skills(self, skills_dir: Path):
        """自动发现并注册技能"""
        for skill_path in skills_dir.glob("*/main.py"):
            skill = self._load_skill(skill_path)
            if skill:
                self.register(skill)
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self._skills.get(name)
    
    def list_skills(self) -> List[SkillMetadata]:
        """列出所有技能"""
        return [s.metadata for s in self._skills.values()]
    
    def to_tool_definitions(self) -> List[Dict]:
        """转换为 LLM 可理解的工具定义"""
        tools = []
        for skill in self._skills.values():
            tools.append({
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "parameters": skill.metadata.parameters
            })
        return tools
```

**技能执行节点** (`core/graph/nodes.py`)
```python
class SkillNode:
    """技能执行节点"""
    
    def __init__(self, registry: SkillRegistry, safety_checker: SafetyChecker):
        self.registry = registry
        self.safety_checker = safety_checker
    
    def __call__(self, state: SafeClawState) -> SafeClawState:
        results = []
        
        for tool_call in state.get("tool_calls", []):
            skill_name = tool_call["name"]
            params = tool_call["arguments"]
            
            # 获取技能
            skill = self.registry.get_skill(skill_name)
            if not skill:
                results.append({"error": f"Unknown skill: {skill_name}"})
                continue
            
            # 安全检查
            if not self.safety_checker.check(skill, params):
                results.append({"error": "Safety check failed"})
                continue
            
            # 需要确认？
            if skill.metadata.requires_confirmation:
                if not state.get("confirmed", False):
                    return {
                        **state,
                        "needs_confirmation": True,
                        "pending_skill": skill_name,
                        "pending_params": params
                    }
            
            # 执行技能
            result = skill.execute(**params)
            results.append(result)
        
        return {
            **state,
            "tool_results": results,
            "execution_path": [*state["execution_path"], "skill"]
        }
```

### 2.3 完整记忆系统

#### 优先级：P1

**四层记忆实现** (`core/memory/layers/`)

```python
# active.py - 活跃记忆
class ActiveMemory:
    """活跃记忆 - 高频访问"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.max_items = 20
        self.decay_hours = 2
    
    def add(self, memory: Dict):
        """添加活跃记忆"""
        memory["activated_at"] = datetime.now().isoformat()
        memory["access_count"] = 1
        self._save(memory)
        self._auto_decay()  # 自动衰减
    
    def _auto_decay(self):
        """活跃记忆自动衰减为沉睡记忆"""
        for file in self.storage_path.glob("*.json"):
            with open(file) as f:
                memory = json.load(f)
            
            activated_at = datetime.fromisoformat(memory["activated_at"])
            hours_passed = (datetime.now() - activated_at).total_seconds() / 3600
            
            if hours_passed > self.decay_hours:
                # 移动到沉睡记忆
                self._move_to_dormant(memory)
                file.unlink()

# dormant.py - 沉睡记忆
class DormantMemory:
    """沉睡记忆 - 需要唤醒"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.wakeup_threshold = 0.6
    
    def wakeup_by_keyword(self, query: str, limit: int = 5) -> List[Dict]:
        """关键词唤醒"""
        awakened = []
        for file in self.storage_path.glob("**/*.json"):
            with open(file) as f:
                memory = json.load(f)
            
            # 简单关键词匹配
            if query.lower() in memory["content"].lower():
                awakened.append(memory)
        
        return awakened[:limit]
    
    def wakeup_by_context(self, current_context: Dict, limit: int = 5) -> List[Dict]:
        """情境关联唤醒"""
        # 基于向量相似度（如果启用）
        # 或基于标签匹配
        pass
    
    def wakeup_by_time(self, current_time: datetime) -> List[Dict]:
        """时间触发唤醒"""
        # 周期性唤醒、纪念日唤醒
        pass

# deep.py - 深层记忆
class DeepMemory:
    """深层记忆 - 核心稳定"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
    
    def get_core_values(self) -> Dict:
        """获取核心价值观"""
        values_file = self.storage_path / "values_system.md"
        if values_file.exists():
            return self._parse_markdown(values_file)
        return {}
    
    def get_fundamental_preferences(self) -> Dict:
        """获取基本偏好"""
        pref_file = self.storage_path / "fundamental_preferences.md"
        if pref_file.exists():
            return self._parse_markdown(pref_file)
        return {}
```

**记忆整合管理器** (`core/memory/manager.py`)
```python
class MemoryManager:
    """统一记忆管理 - 整合四层记忆"""
    
    def __init__(self, workspace: Path):
        self.active = ActiveMemory(workspace / "memory" / "active")
        self.dormant = DormantMemory(workspace / "memory" / "dormant")
        self.deep = DeepMemory(workspace / "memory" / "deep")
        self.forgotten = ForgottenMemory(workspace / "memory" / "forgotten")
    
    def retrieve_for_query(self, query: str, limit: int = 10) -> List[Dict]:
        """为查询检索相关记忆"""
        memories = []
        
        # 1. 活跃记忆（直接获取）
        memories.extend(self.active.get_recent(limit=5))
        
        # 2. 沉睡记忆（唤醒）
        awakened = self.dormant.wakeup_by_keyword(query, limit=3)
        memories.extend(awakened)
        
        # 3. 深层记忆（始终包含）
        core_values = self.deep.get_core_values()
        if core_values:
            memories.insert(0, {
                "type": "deep",
                "content": core_values
            })
        
        return memories[:limit]
    
    def add_from_conversation(self, user_input: str, assistant_response: str):
        """从对话中提取并添加记忆"""
        # 1. 短期活跃记忆
        self.active.add({
            "content": f"Q: {user_input}\nA: {assistant_response}",
            "timestamp": datetime.now().isoformat(),
            "type": "conversation"
        })
        
        # 2. 提取长期记忆（使用 LLM）
        important_info = self._extract_important_info(
            user_input, assistant_response
        )
        if important_info:
            self.dormant.add(important_info)
    
    def _extract_important_info(self, user_msg: str, ai_msg: str) -> Optional[Dict]:
        """使用 LLM 提取重要信息"""
        prompt = f"""
        分析以下对话，提取需要长期记住的重要信息。
        只返回具体的事实、偏好或决策，如果没有重要信息则返回 "NONE"。
        
        用户: {user_msg}
        助手: {ai_msg}
        
        重要信息:
        """
        result = self.llm_gateway.invoke([{"role": "user", "content": prompt}])
        
        if result.strip() == "NONE":
            return None
        
        return {
            "content": result.strip(),
            "timestamp": datetime.now().isoformat(),
            "source": "extracted",
            "type": "long_term"
        }
```

### 2.4 安全控制层

#### 优先级：P0

**安全检查器** (`core/safety/checker.py`)
```python
class SafetyChecker:
    """安全检查器 - 三级策略"""
    
    def __init__(self, config: SafetyConfig):
        self.blacklist = set(config.blacklist_commands)
        self.whitelist = set(config.whitelist_operations)
        self.audit_logger = AuditLogger()
    
    def check(self, skill: BaseSkill, params: Dict) -> bool:
        """检查技能执行是否安全"""
        skill_name = skill.metadata.name
        
        # 1. 黑名单检查 - 完全禁止
        if self._is_blacklisted(skill_name, params):
            self.audit_logger.log_blocked(skill_name, params, "blacklist")
            return False
        
        # 2. 白名单检查 - 自动允许
        if skill_name in self.whitelist:
            self.audit_logger.log_allowed(skill_name, params, "whitelist")
            return True
        
        # 3. 确认操作 - 需要用户确认
        if skill.metadata.requires_confirmation:
            # 这个检查由 SkillNode 处理
            return True
        
        # 默认允许
        return True
    
    def _is_blacklisted(self, skill_name: str, params: Dict) -> bool:
        """检查是否在黑名单"""
        # 检查技能名称
        if skill_name in self.blacklist:
            return True
        
        # 检查参数中是否包含危险命令
        for value in params.values():
            if isinstance(value, str):
                if any(cmd in value for cmd in self.blacklist):
                    return True
        
        return False

**审计日志** (`core/safety/audit.py`)
```python
class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
    
    def log_blocked(self, skill_name: str, params: Dict, reason: str):
        """记录被阻止的操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "BLOCKED",
            "skill": skill_name,
            "params": params,
            "reason": reason
        }
        self._write_log(log_entry)
    
    def log_allowed(self, skill_name: str, params: Dict, reason: str):
        """记录允许的操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "ALLOWED",
            "skill": skill_name,
            "params": params,
            "reason": reason
        }
        self._write_log(log_entry)
    
    def _write_log(self, entry: Dict):
        """写入日志文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{today}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

### 2.5 UI 完善

#### 优先级：P1

**侧边栏组件** (`components/sidebar.py`)
```python
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🦞 SafeClaw TRASA")
        
        # 会话管理
        st.subheader("会话管理")
        sessions = load_sessions()
        selected_session = st.selectbox(
            "选择会话",
            options=[s["id"] for s in sessions],
            format_func=lambda x: next(
                s["name"] for s in sessions if s["id"] == x
            )
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("新建会话"):
                create_new_session()
        with col2:
            if st.button("删除会话"):
                delete_session(selected_session)
        
        st.divider()
        
        # 模型选择
        st.subheader("模型设置")
        provider = st.selectbox(
            "LLM 提供商",
            ["OpenAI", "Anthropic", "Ollama"]
        )
        
        models = get_models_for_provider(provider)
        model = st.selectbox("模型", models)
        
        temperature = st.slider(
            "温度", 
            min_value=0.0, 
            max_value=2.0, 
            value=0.7,
            step=0.1
        )
        
        st.divider()
        
        # 记忆统计
        st.subheader("记忆统计")
        memory_stats = get_memory_stats()
        st.metric("活跃记忆", memory_stats["active"])
        st.metric("沉睡记忆", memory_stats["dormant"])
        st.metric("深层记忆", memory_stats["deep"])
```

**记忆浏览页** (`pages/01_📚_Memory.py`)
```python
import streamlit as st
from core.memory.manager import MemoryManager

st.title("📚 记忆浏览器")

# 搜索框
query = st.text_input("搜索记忆", placeholder="输入关键词...")

# 记忆类型过滤
memory_type = st.selectbox(
    "记忆类型",
    ["全部", "活跃", "沉睡", "深层"]
)

# 搜索按钮
if st.button("搜索") or query:
    memory_manager = MemoryManager(get_workspace_path())
    
    if memory_type == "全部":
        results = memory_manager.search_all(query)
    elif memory_type == "活跃":
        results = memory_manager.active.search(query)
    elif memory_type == "沉睡":
        results = memory_manager.dormant.search(query)
    else:
        results = memory_manager.deep.search(query)
    
    st.write(f"找到 {len(results)} 条记忆")
    
    for memory in results:
        with st.expander(f"{memory['timestamp']} - {memory['type']}"):
            st.markdown(memory["content"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("激活", key=f"activate_{memory['id']}"):
                    memory_manager.activate_memory(memory["id"])
            with col2:
                if st.button("编辑", key=f"edit_{memory['id']}"):
                    # 打开编辑对话框
                    pass
            with col3:
                if st.button("删除", key=f"delete_{memory['id']}"):
                    if st.confirm("确定删除此记忆？"):
                        memory_manager.delete_memory(memory["id"])

# 可视化记忆网络
st.subheader("记忆关联网络")
# 使用 graphviz 或 networkx 可视化记忆之间的关联
```

---

## 🎨 第三阶段：高级功能与优化 (2-3周)

### 目标
实现**向量检索 + RAG + 代码解释器 + 性能优化 + UI 美化**

### 3.1 向量检索集成（可选）

#### 优先级：P2

**ChromaDB 集成** (`core/memory/vector_store.py`)
```python
import chromadb
from chromadb.config import Settings

class VectorMemoryStore:
    """向量记忆存储 - ChromaDB"""
    
    def __init__(self, persist_directory: Path):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(persist_directory)
        ))
        self.collection = self.client.get_or_create_collection("memories")
    
    def add_memory(self, memory: Dict):
        """添加记忆到向量库"""
        self.collection.add(
            documents=[memory["content"]],
            metadatas=[{
                "timestamp": memory["timestamp"],
                "type": memory["type"]
            }],
            ids=[memory["id"]]
        )
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """语义搜索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        memories = []
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "id": results["ids"][0][i],
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return memories
```

### 3.2 RAG 知识库

#### 优先级：P2

**文档上传与索引** (`core/rag/indexer.py`)
```python
class DocumentIndexer:
    """文档索引器"""
    
    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store
    
    def index_document(self, file_path: Path):
        """索引单个文档"""
        # 1. 加载文档
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # 2. 分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # 3. 添加到向量库
        for chunk in chunks:
            self.vector_store.add_memory({
                "id": str(uuid.uuid4()),
                "content": chunk.page_content,
                "timestamp": datetime.now().isoformat(),
                "type": "document",
                "source": str(file_path)
            })
    
    def _get_loader(self, file_path: Path):
        """根据文件类型选择加载器"""
        if file_path.suffix == ".pdf":
            return PyPDFLoader(str(file_path))
        elif file_path.suffix == ".md":
            return UnstructuredMarkdownLoader(str(file_path))
        elif file_path.suffix in [".py", ".js", ".java"]:
            return TextLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
```

### 3.3 代码解释器（可选）

#### 优先级：P3

**安全 Python 执行器** (`core/skills/built_in/code_interpreter.py`)
```python
class CodeInterpreterSkill(BaseSkill):
    """代码解释器技能 - 安全执行 Python"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="execute_python",
            description="安全执行 Python 代码",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "超时时间（秒）"
                    }
                },
                "required": ["code"]
            },
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "error": {"type": "string"},
                    "figures": {"type": "array"}
                }
            },
            requires_confirmation=True  # 执行代码需要确认
        )
    
    def execute(self, code: str, timeout: int = 30) -> Dict:
        """在受限环境中执行代码"""
        try:
            # 创建受限的全局命名空间
            restricted_globals = {
                "__builtins__": safe_builtins(),
                "print": captured_print,
                "plt": matplotlib.pyplot,
                "np": numpy,
                "pd": pandas
            }
            
            # 捕获输出
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                # 使用 RestrictedPython 或 timeout-decorator
                exec(code, restricted_globals)
            
            return {
                "success": True,
                "output": output_buffer.getvalue(),
                "figures": self._capture_figures()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _capture_figures(self) -> List[str]:
        """捕获 matplotlib 图表为 base64"""
        # 实现图表捕获
        pass

def safe_builtins():
    """返回安全的内置函数"""
    safe_list = [
        "abs", "all", "any", "bin", "bool", "chr", "dict", 
        "enumerate", "filter", "float", "int", "len", "list", 
        "map", "max", "min", "range", "round", "set", "str", 
        "sum", "tuple", "zip"
    ]
    return {name: __builtins__[name] for name in safe_list}
```

### 3.4 性能优化

#### 优先级：P1

**缓存策略**
```python
import streamlit as st

@st.cache_data(ttl=3600)
def load_memory_index():
    """缓存记忆索引"""
    return memory_manager.build_index()

@st.cache_resource
def get_llm_gateway():
    """缓存 LLM 连接"""
    return GatewayFactory.create(config)
```

**异步记忆处理**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncMemoryManager:
    """异步记忆管理器"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def add_memory_async(self, memory: Dict):
        """异步添加记忆"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.memory_store.add,
            memory
        )
```

### 3.5 UI 美化与体验优化

#### 优先级：P1

**自定义 CSS** (`styles/custom.css`)
```css
/* 主题色 */
:root {
    --primary-color: #FF6B6B;
    --secondary-color: #4ECDC4;
    --background-color: #1A1A2E;
    --text-color: #EAEAEA;
}

/* 聊天消息样式 */
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}

.chat-message.user {
    background-color: var(--primary-color);
    align-items: flex-end;
}

.chat-message.assistant {
    background-color: var(--secondary-color);
    align-items: flex-start;
}

/* 侧边栏样式 */
.sidebar .sidebar-content {
    background-color: var(--background-color);
}

/* 按钮样式 */
.stButton>button {
    border-radius: 20px;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

**加载自定义 CSS** (`app.py`)
```python
def load_custom_css():
    """加载自定义 CSS"""
    css_file = Path(__file__).parent / "styles" / "custom.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 在主应用中调用
load_custom_css()
```

**打字机效果流式响应**
```python
def stream_response(response_text: str, placeholder):
    """流式显示响应（打字机效果）"""
    displayed_text = ""
    for chunk in response_text.split():
        displayed_text += chunk + " "
        placeholder.markdown(displayed_text + "▌")
        time.sleep(0.05)
    
    placeholder.markdown(displayed_text)
```

---

## 📊 开发时间线与里程碑

### 总览
| 阶段 | 时间 | 核心交付物 | 验收标准 |
|------|------|-----------|---------|
| 阶段一 | 2-3周 | MVP可运行 | 能进行简单对话，有基础记忆 |
| 阶段二 | 3-4周 | 核心功能完整 | 多Agent协作，技能系统，完整记忆 |
| 阶段三 | 2-3周 | 高级功能 | 向量检索，性能优化，UI美化 |
| **总计** | **7-10周** | **生产级产品** | **可对外发布** |

### 详细里程碑

#### 🎯 Milestone 1: MVP (Week 1-3)
**目标**: 最小可用产品

**Week 1: 基础架构**
- [ ] Day 1-2: 项目结构搭建 + 环境配置
- [ ] Day 3-4: 核心模型定义 (State, Config, Session)
- [ ] Day 5: LLM Gateway 实现

**Week 2: Graph + UI**
- [ ] Day 1-2: 简单 LangGraph 实现
- [ ] Day 3-4: 基础 Streamlit UI
- [ ] Day 5: 流式响应集成

**Week 3: 记忆 + 测试**
- [ ] Day 1-2: 基础记忆系统 (Active Memory)
- [ ] Day 3-4: 集成测试 + Bug 修复
- [ ] Day 5: MVP 演示准备

**验收标准**:
- ✅ 能与 LLM 进行多轮对话
- ✅ 对话历史保存到文件
- ✅ UI 基本可用
- ✅ 无阻塞性 Bug

#### 🚀 Milestone 2: 核心功能 (Week 4-7)
**目标**: 功能完整的产品

**Week 4: 多 Agent Graph**
- [ ] Day 1-2: Router Agent 实现
- [ ] Day 3-4: Planner/Executor/Reviewer Agents
- [ ] Day 5: 多 Agent 协作测试

**Week 5: 技能系统**
- [ ] Day 1-2: BaseSkill + SkillRegistry
- [ ] Day 3-4: 内置技能实现 (文件、代码、搜索)
- [ ] Day 5: 技能到工具转换

**Week 6: 完整记忆系统**
- [ ] Day 1-2: 四层记忆实现
- [ ] Day 3-4: 记忆唤醒机制
- [ ] Day 5: 记忆精华化

**Week 7: 安全 + UI 完善**
- [ ] Day 1-2: 安全控制层 + 审计日志
- [ ] Day 3-4: 侧边栏 + 记忆浏览页
- [ ] Day 5: 集成测试

**验收标准**:
- ✅ 多 Agent 能协作处理复杂任务
- ✅ 技能系统可扩展
- ✅ 记忆系统完整工作
- ✅ 安全控制有效

#### 🎨 Milestone 3: 高级功能 (Week 8-10)
**目标**: 生产级产品

**Week 8: 向量检索 + RAG**
- [ ] Day 1-2: ChromaDB 集成
- [ ] Day 3-4: 文档上传 + 索引
- [ ] Day 5: RAG 查询测试

**Week 9: 性能优化**
- [ ] Day 1-2: 缓存策略
- [ ] Day 3-4: 异步处理
- [ ] Day 5: 性能测试

**Week 10: UI 美化 + 发布准备**
- [ ] Day 1-2: 自定义 CSS + 动画
- [ ] Day 3-4: 文档完善
- [ ] Day 5: 发布准备

**验收标准**:
- ✅ 支持文档知识库
- ✅ 响应速度 < 2s (首 token)
- ✅ UI 美观专业
- ✅ 文档完整

---

## 🛠️ 技术实施细节

### 开发环境配置

**1. Conda 环境**
```bash
# 创建环境
conda env create -f environment.yml

# 或手动创建
conda create -n safe_claw python=3.10
conda activate safe_claw

# 安装依赖
pip install -r requirements.txt
```

**2. 必需依赖**
```txt
# requirements.txt
streamlit>=1.30.0
langgraph>=0.0.50
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# 可选
chromadb>=0.4.0
keyring>=24.0.0
```

**3. 环境变量**
```bash
# .env
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
WORKSPACE_PATH=~/.safe_claw
LOG_LEVEL=INFO
```

### 项目初始化脚本

**init_project.py**
```python
#!/usr/bin/env python3
"""初始化 SafeClaw 项目"""

from pathlib import Path
import json

def init_workspace(workspace_path: Path):
    """初始化工作区"""
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # 创建目录结构
    dirs = [
        "memory/active",
        "memory/dormant",
        "memory/deep",
        "memory/forgotten",
        "sessions",
        "skills",
        "logs"
    ]
    
    for dir_name in dirs:
        (workspace_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # 创建默认配置
    default_config = {
        "llm": {
            "provider": "openai",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "memory": {
            "enable_vector_search": False,
            "active_memory_max": 20,
            "dormant_wakeup_threshold": 0.6
        },
        "safety": {
            "enable_confirmation": True,
            "blacklist_commands": ["rm -rf /", "format"],
            "whitelist_operations": ["read_file", "chat"]
        }
    }
    
    config_file = workspace_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    # 创建默认 AGENTS.md
    agents_md = workspace_path / "AGENTS.md"
    agents_md.write_text("""# SafeClaw Agent 配置

## 系统提示词

你是 SafeClaw，一个安全优先的本地 AI 助手。

### 核心原则
1. **安全第一**: 敏感操作必须确认
2. **透明可控**: 所有操作可审计
3. **本地优先**: 数据不出境
4. **持续学习**: 从对话中学习用户偏好

### 能力范围
- 对话交流
- 代码分析
- 文件操作
- 记忆管理
- 技能调用
""")
    
    print(f"✅ 工作区初始化完成: {workspace_path}")

if __name__ == "__main__":
    workspace = Path.home() / ".safe_claw"
    init_workspace(workspace)
```

---

## 🧪 测试策略

### 单元测试
```python
# tests/unit/test_memory_manager.py
import pytest
from core.memory.manager import MemoryManager

def test_add_active_memory(tmp_path):
    manager = MemoryManager(tmp_path)
    manager.active.add({
        "content": "测试记忆",
        "timestamp": "2026-03-22T10:00:00"
    })
    
    memories = manager.active.get_recent(limit=10)
    assert len(memories) == 1
    assert memories[0]["content"] == "测试记忆"

def test_keyword_wakeup(tmp_path):
    manager = MemoryManager(tmp_path)
    
    # 添加沉睡记忆
    manager.dormant.add({
        "content": "Python 编程技巧",
        "timestamp": "2026-03-01T10:00:00"
    })
    
    # 关键词唤醒
    awakened = manager.dormant.wakeup_by_keyword("Python")
    assert len(awakened) > 0
```

### 集成测试
```python
# tests/integration/test_graph_execution.py
def test_simple_chat_graph():
    graph = build_simple_chat_graph()
    
    state = {
        "user_input": "你好",
        "session_id": "test",
        "messages": [],
        # ...
    }
    
    result = graph.invoke(state)
    
    assert "response" in result
    assert len(result["response"]) > 0
    assert "execution_path" in result
```

### E2E 测试
```python
# tests/e2e/test_ui_flow.py
from streamlit.testing.v1 import AppTest

def test_chat_flow():
    at = AppTest.from_file("app.py")
    at.run()
    
    # 模拟用户输入
    at.chat_input[0].set_value("你好").run()
    
    # 验证响应
    assert len(at.chat_message) > 0
```

---

## 📝 文档规范

### 代码注释
```python
def retrieve_for_query(self, query: str, limit: int = 10) -> List[Dict]:
    """为查询检索相关记忆
    
    Args:
        query: 查询字符串
        limit: 最大返回数量
    
    Returns:
        相关记忆列表，按相关性排序
    
    Example:
        >>> manager.retrieve_for_query("Python编程", limit=5)
        [{'content': 'Python最佳实践', ...}, ...]
    """
```

### API 文档
使用 Sphinx 自动生成

```bash
# 安装
pip install sphinx sphinx-rtd-theme

# 初始化
cd docs
sphinx-quickstart

# 生成文档
make html
```

---

## 🚨 风险管理

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| LangGraph 版本不兼容 | 高 | 中 | 锁定版本，编写适配层 |
| Streamlit 性能瓶颈 | 中 | 高 | 实现缓存，异步处理 |
| 记忆检索性能差 | 中 | 中 | 向量索引，分层存储 |
| LLM API 限流 | 低 | 中 | 实现重试，本地备份 |

### 进度风险

| 风险 | 缓解措施 |
|------|---------|
| 需求变更 | 每周回顾，快速迭代 |
| 技术难点 | 提前 Spike，寻求社区帮助 |
| 测试不充分 | TDD 开发，自动化测试 |

---

## 🎯 成功标准

### MVP 阶段
- ✅ 能与 3+ 种 LLM 对话
- ✅ 会话历史持久化
- ✅ 基础记忆功能工作
- ✅ UI 无明显 Bug

### 核心功能阶段
- ✅ 多 Agent 协作成功率 > 90%
- ✅ 技能系统可扩展 (支持自定义)
- ✅ 记忆唤醒准确率 > 80%
- ✅ 安全控制 100% 生效

### 高级功能阶段
- ✅ 向量检索召回率 > 85%
- ✅ 首 token 延迟 < 2s
- ✅ UI 满意度 > 4/5
- ✅ 文档完整度 100%

---

## 📚 参考资源

### 官方文档
- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
- [Streamlit 文档](https://docs.streamlit.io)
- [LangChain 文档](https://python.langchain.com)

### 设计参考
- OpenClaw 架构设计
- Claude Desktop 用户体验
- ChatGPT UI 交互模式

### 技术博客
- [Building Agent Workflows with LangGraph](https://blog.langchain.dev)
- [Streamlit Best Practices](https://docs.streamlit.io/library/advanced-features)

---

## 🤝 开发协作

### Git 工作流
```bash
# 主分支
main          # 生产代码
develop       # 开发主线

# 功能分支
feature/mvp-graph
feature/memory-system
feature/skill-registry

# 修复分支
hotfix/critical-bug
```

### Commit 规范
```
feat: 添加新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

### Code Review 清单
- [ ] 代码符合项目规范
- [ ] 有充足的注释
- [ ] 有对应的测试
- [ ] 无明显性能问题
- [ ] 安全检查通过

---

## 📞 联系与支持

### 问题反馈
- GitHub Issues
- 开发者邮件列表
- 技术社区讨论

### 开发者社区
- Discord 频道
- 定期技术分享
- 代码贡献指南

---

**最后更新**: 2026-03-22  
**文档版本**: v1.0  
**维护者**: SafeClaw Development Team