"""Base agent class for SafeClaw"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime

from core.graph.state import SafeClawState
from services.llm_gateway import LLMService

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all SafeClaw agents"""
    
    def __init__(self, name: str, llm_service: LLMService, config: Dict[str, Any] = None):
        self.name = name
        self.llm_service = llm_service
        self.config = config or {}
        self.created_at = datetime.now()
        self.execution_count = 0
        
        logger.info(f"Initialized agent: {self.name}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return self.system_prompt if hasattr(self, 'system_prompt') else f"You are a {self.__class__.__name__}."
    
    @abstractmethod
    def process(self, state: SafeClawState) -> SafeClawState:
        """Process the state and return updated state"""
        pass
    
    def validate_input(self, user_input: str) -> tuple[bool, str]:
        """
        Validate user input for this agent
        
        Args:
            user_input: User input to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not user_input or not user_input.strip():
                return False, "Input cannot be empty"
            
            if len(user_input) > 10000:
                return False, "Input too long (max 10000 characters)"
            
            # Agent-specific validation
            return self._validate_agent_input(user_input)
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _validate_agent_input(self, user_input: str) -> tuple[bool, str]:
        """
        Agent-specific input validation (override in subclasses)
        
        Args:
            user_input: User input to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default implementation - always valid
        return True, ""
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities
        
        Returns:
            List of capability descriptions
        """
        if hasattr(self, 'capabilities'):
            return self.capabilities
        return [f"{self.__class__.__name__} processing"]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information
        
        Returns:
            Dictionary with status information
        """
        return {
            "agent_type": self.__class__.__name__,
            "is_active": getattr(self, 'is_active', True),
            "execution_count": getattr(self, 'execution_count', 0),
            "last_execution": getattr(self, 'last_execution', None),
            "capabilities": self.get_capabilities()
        }
    
    def reset_stats(self):
        """Reset agent statistics"""
        self.execution_count = 0
        self.last_execution = None
        self.error_count = 0
        self.success_count = 0
    
    def increment_execution(self):
        """Increment execution counter"""
        if not hasattr(self, 'execution_count'):
            self.execution_count = 0
        self.execution_count += 1
        self.last_execution = datetime.now()
    
    def increment_success(self):
        """Increment success counter"""
        if not hasattr(self, 'success_count'):
            self.success_count = 0
        self.success_count += 1
    
    def increment_error(self):
        """Increment error counter"""
        if not hasattr(self, 'error_count'):
            self.error_count = 0
        self.error_count += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = getattr(self, 'success_count', 0) + getattr(self, 'error_count', 0)
        return self.success_count / total if total > 0 else 0.0
    
    def stream_response(self, state: SafeClawState) -> Iterator[str]:
        """Stream response from the agent"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Add conversation history
        for msg in state.get("messages", []):
            if hasattr(msg, 'type'):
                role = "user" if msg.type == "human" else "assistant"
                messages.append({"role": role, "content": msg.content})
        
        # Add current user input
        if state.get("user_input"):
            messages.append({"role": "user", "content": state["user_input"]})
        
        try:
            for chunk in self.llm_service.stream(messages):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming response from {self.name}: {e}")
            yield f"Error: {str(e)}"
    
    def invoke_response(self, state: SafeClawState) -> str:
        """Get synchronous response from the agent"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Add conversation history
        for msg in state.get("messages", []):
            if hasattr(msg, 'type'):
                role = "user" if msg.type == "human" else "assistant"
                messages.append({"role": role, "content": msg.content})
        
        # Add current user input
        if state.get("user_input"):
            messages.append({"role": "user", "content": state["user_input"]})
        
        try:
            return self.llm_service.invoke(messages)
        except Exception as e:
            logger.error(f"Error invoking response from {self.name}: {e}")
            return f"Error: {str(e)}"
    
    def update_state(self, state: SafeClawState, response: str) -> SafeClawState:
        """Update state with agent response"""
        state["current_agent"] = self.name
        state["response"] = response
        state["execution_path"] = state.get("execution_path", [])
        state["execution_path"].append(self.name)
        self.execution_count += 1
        
        return state
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count,
            "config": self.config
        }
    
    def validate_state(self, state: SafeClawState) -> bool:
        """Validate that state has required fields"""
        required_fields = ["user_input", "session_id"]
        return all(field in state for field in required_fields)
