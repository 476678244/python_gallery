"""LangGraph workflow builder for SafeClaw"""

import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from streamlit_ui.safe_claw.core.graph.state import SafeClawState
from streamlit_ui.safe_claw.core.agents.router_agent import RouterAgent
from streamlit_ui.safe_claw.core.agents.chat_agent import ChatAgent
from streamlit_ui.safe_claw.core.agents.memory_agent import MemoryAgent
from streamlit_ui.safe_claw.core.deepagents.official_integration import SafeClawDeepAgent, DeepAgentFactory
from streamlit_ui.safe_claw.services.llm_gateway import LLMService

logger = logging.getLogger(__name__)


class SafeClawGraphBuilder:
    """Builder for SafeClaw LangGraph workflows"""
    
    def __init__(self, llm_service: LLMService, memory_manager, config: Dict[str, Any] = None):
        self.llm_service = llm_service
        self.memory_manager = memory_manager
        self.config = config or {}
        
        # Initialize official DeepAgent
        self.deep_agent = DeepAgentFactory.create_with_memory(
            llm_service=llm_service,
            memory_manager=memory_manager,
            config=config
        )
        
        # Initialize legacy agents (for backward compatibility)
        self.router_agent = RouterAgent(llm_service, config)
        self.chat_agent = ChatAgent(llm_service, config)
        self.memory_agent = MemoryAgent(llm_service, memory_manager, config)
        
        # Agent registry for router
        self.agent_registry = {
            "deep_agent": self.deep_agent,
            "chat_agent": self.chat_agent,
            "memory_agent": self.memory_agent
        }
        self.router_agent.update_agent_registry(self.agent_registry)
        
        logger.info("SafeClaw graph builder initialized with official DeepAgent")
    
    def build_simple_chat_graph(self) -> StateGraph:
        """Build a simple chat-only workflow"""
        workflow = StateGraph(SafeClawState)
        
        # Add nodes
        workflow.add_node("chat", self._chat_node)
        
        # Add edges
        workflow.set_entry_point("chat")
        workflow.add_edge("chat", END)
        
        # Add memory
        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)
    
    def build_deep_agent_graph(self) -> StateGraph:
        """Build a DeepAgent-only workflow"""
        workflow = StateGraph(SafeClawState)
        
        # Add nodes
        workflow.add_node("deep_agent", self._deep_agent_node)
        
        # Add edges
        workflow.set_entry_point("deep_agent")
        workflow.add_edge("deep_agent", END)
        
        # Add memory
        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)
    
    def build_multi_agent_graph(self) -> StateGraph:
        """Build a multi-agent workflow with routing"""
        workflow = StateGraph(SafeClawState)
        
        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("chat", self._chat_node)
        workflow.add_node("memory", self._memory_node)
        workflow.add_node("safety_check", self._safety_check_node)
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "chat_agent": "chat",
                "memory_agent": "memory",
                "safety_agent": "safety_check",
                "end": END
            }
        )
        
        # Add edges from agents back to router or end
        workflow.add_edge("chat", END)
        workflow.add_edge("memory", END)
        workflow.add_edge("safety_check", END)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add memory
        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)
    
    def build_advanced_graph(self) -> StateGraph:
        """Build an advanced workflow with memory integration and safety"""
        workflow = StateGraph(SafeClawState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("memory_retrieval", self._memory_retrieval_node)
        workflow.add_node("router", self._router_node)
        workflow.add_node("chat", self._chat_node)
        workflow.add_node("memory", self._memory_node)
        workflow.add_node("safety_check", self._safety_check_node)
        workflow.add_node("finalizer", self._finalizer_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add sequential edges
        workflow.add_edge("initialize", "memory_retrieval")
        workflow.add_edge("memory_retrieval", "router")
        
        # Add conditional routing from router
        workflow.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "chat_agent": "chat",
                "memory_agent": "memory",
                "safety_agent": "safety_check",
                "end": END
            }
        )
        
        # All agents go to finalizer
        workflow.add_edge("chat", "finalizer")
        workflow.add_edge("memory", "finalizer")
        workflow.add_edge("safety_check", "finalizer")
        
        # Finalizer goes to end
        workflow.add_edge("finalizer", END)
        
        # Add memory
        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)
    
    def _initialize_node(self, state: SafeClawState) -> SafeClawState:
        """Initialize the workflow state"""
        state["start_time"] = datetime.now()
        state["execution_path"] = []
        state["agent_outputs"] = {}
        state["needs_confirmation"] = False
        state["confirmed"] = True
        
        logger.info(f"Initializing workflow for session {state.get('session_id')}")
        return state
    
    def _memory_retrieval_node(self, state: SafeClawState) -> SafeClawState:
        """Retrieve relevant memories before processing"""
        user_input = state.get("user_input", "")
        
        if user_input:
            # Search for relevant memories
            search_results = self.memory_manager.search_memories(user_input, max_results=5)
            state["active_memories"] = [result.memory.dict() for result in search_results]
        else:
            state["active_memories"] = []
        
        state["execution_path"].append("memory_retrieval")
        return state
    
    def _router_node(self, state: SafeClawState) -> SafeClawState:
        """Route to appropriate agent"""
        return self.router_agent.process(state)
    
    def _chat_node(self, state: SafeClawState) -> SafeClawState:
        """Process with chat agent"""
        return self.chat_agent.process(state)
    
    def _deep_agent_node(self, state: SafeClawState) -> SafeClawState:
        """Process with official DeepAgent"""
        try:
            # Prepare messages for DeepAgent
            user_input = state.get("user_input", "")
            messages = [
                {"role": "user", "content": user_input}
            ]
            
            # Add conversation history if available
            if state.get("messages"):
                for msg in state["messages"][-5:]:  # Last 5 messages
                    if hasattr(msg, 'type'):
                        role = "user" if msg.type == "human" else "assistant"
                        messages.append({"role": role, "content": msg.content})
            
            # Execute DeepAgent
            result = self.deep_agent.invoke(messages)
            
            # Update state with result
            state["response"] = result.get("content", "")
            state["current_agent"] = "deep_agent"
            state["execution_path"].append("deep_agent")
            
            # Add metadata
            state["deep_agent_metadata"] = {
                "success": result.get("success", False),
                "tool_calls": result.get("tool_calls", []),
                "metadata": result.get("metadata", {})
            }
            
            if not result.get("success", False):
                error_msg = result.get("metadata", {}).get("error", "DeepAgent execution failed")
                state["response"] = f"Error: {error_msg}"
            
        except Exception as e:
            logger.error(f"DeepAgent execution error: {e}")
            state["response"] = f"DeepAgent error: {str(e)}"
            state["current_agent"] = "deep_agent"
        
        return state
    
    def _memory_node(self, state: SafeClawState) -> SafeClawState:
        """Process with memory agent"""
        return self.memory_agent.process(state)
    
    def _safety_check_node(self, state: SafeClawState) -> SafeClawState:
        """Process safety checks"""
        # Placeholder for safety agent
        state["response"] = "Safety checks would be performed here."
        state["current_agent"] = "safety_agent"
        return state
    
    def _finalizer_node(self, state: SafeClawState) -> SafeClawState:
        """Finalize the workflow"""
        # Store conversation in memory if appropriate
        user_input = state.get("user_input", "")
        response = state.get("response", "")
        
        if user_input and response and len(user_input) > 10:
            # Store the conversation exchange
            conversation = f"User: {user_input}\nAssistant: {response}"
            importance = self._assess_conversation_importance(user_input, response)
            
            self.memory_manager.add_memory(
                content=conversation,
                importance_score=importance,
                metadata={"type": "conversation", "session_id": state.get("session_id")}
            )
        
        state["execution_path"].append("finalizer")
        return state
    
    def _route_to_agent(self, state: SafeClawState) -> str:
        """Determine which agent to route to"""
        current_agent = state.get("current_agent", "chat_agent")
        
        # Validate agent exists
        if current_agent in self.agent_registry:
            return current_agent
        
        # Fallback to chat agent
        return "chat_agent"
    
    def _assess_conversation_importance(self, user_input: str, response: str) -> float:
        """Assess importance of conversation exchange"""
        text = (user_input + " " + response).lower()
        
        # High importance indicators
        if any(word in text for word in ["important", "critical", "remember", "preference"]):
            return 0.8
        
        # Medium importance indicators
        if any(word in text for word in ["question", "how to", "what is", "help with"]):
            return 0.6
        
        # Default importance
        return 0.4
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about available graphs"""
        return {
            "simple_chat": "Basic chat-only workflow",
            "deep_agent": "Official DeepAgent workflow with planning and sub-agents",
            "multi_agent": "Multi-agent workflow with routing",
            "advanced": "Advanced workflow with memory and safety"
        }
    
    def create_graph(self, graph_type: str = "advanced") -> StateGraph:
        """Create a graph of the specified type"""
        if graph_type == "simple_chat":
            return self.build_simple_chat_graph()
        elif graph_type == "deep_agent":
            return self.build_deep_agent_graph()
        elif graph_type == "multi_agent":
            return self.build_multi_agent_graph()
        elif graph_type == "advanced":
            return self.build_advanced_graph()
        else:
            raise ValueError(f"Unknown graph type: {graph_type}")
    
    def get_deep_agent_stats(self) -> Dict[str, Any]:
        """Get DeepAgent statistics"""
        return self.deep_agent.get_agent_info()
