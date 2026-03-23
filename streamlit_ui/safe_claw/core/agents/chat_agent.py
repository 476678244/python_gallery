"""Chat agent for SafeClaw"""

import logging
from typing import Dict, Any, Iterator

from core.agents.base_agent import BaseAgent
from core.graph.state import SafeClawState
from services.llm_gateway import LLMService

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """Main chat agent for conversational interactions"""
    
    def __init__(self, llm_service: LLMService, config: Dict[str, Any] = None):
        super().__init__("chat_agent", llm_service, config)
        self.personality = config.get("personality", "helpful_assistant")
        self.max_response_length = config.get("max_response_length", 2000)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for chat agent"""
        base_prompt = """You are SafeClaw, a helpful and safe AI assistant. Your purpose is to assist users with their tasks while maintaining safety and privacy.

Key principles:
- Be helpful, accurate, and concise
- Prioritize user safety and data privacy
- Ask for clarification when needed
- Admit when you don't know something
- Provide thoughtful, well-reasoned responses

You have access to memory systems and can recall previous conversations when relevant."""
        
        personality_prompts = {
            "helpful_assistant": "You are friendly, professional, and eager to help.",
            "technical_expert": "You are technically precise and detailed in your responses.",
            "creative_partner": "You are creative and encourage innovative thinking.",
            "minimalist": "You provide concise, to-the-point responses."
        }
        
        personality = personality_prompts.get(self.personality, personality_prompts["helpful_assistant"])
        
        return f"{base_prompt}\n\n{personality}"
    
    def process(self, state: SafeClawState) -> SafeClawState:
        """Process chat interaction"""
        if not self.validate_state(state):
            state["response"] = "Error: Invalid state provided to chat agent"
            return state
        
        try:
            # Get response from LLM
            response = self.invoke_response(state)
            
            # Truncate if too long
            if len(response) > self.max_response_length:
                response = response[:self.max_response_length-3] + "..."
            
            # Update state
            state = self.update_state(state, response)
            
            logger.info(f"Chat agent processed message for session {state['session_id']}")
            
        except Exception as e:
            logger.error(f"Error in chat agent processing: {e}")
            state["response"] = f"Sorry, I encountered an error: {str(e)}"
        
        return state
    
    def stream_process(self, state: SafeClawState) -> Iterator[Dict[str, Any]]:
        """Stream chat processing"""
        if not self.validate_state(state):
            yield {"type": "error", "content": "Error: Invalid state provided to chat agent"}
            return
        
        try:
            # Update state to show current agent
            state["current_agent"] = self.name
            state["execution_path"] = state.get("execution_path", [])
            state["execution_path"].append(self.name)
            
            # Stream response
            full_response = ""
            for chunk in self.stream_response(state):
                full_response += chunk
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "agent": self.name
                }
            
            # Final state update
            state["response"] = full_response
            self.execution_count += 1
            
            yield {
                "type": "complete",
                "content": full_response,
                "agent": self.name,
                "state": state
            }
            
            logger.info(f"Chat agent streamed response for session {state['session_id']}")
            
        except Exception as e:
            logger.error(f"Error in chat agent streaming: {e}")
            yield {"type": "error", "content": f"Sorry, I encountered an error: {str(e)}"}
    
    def handle_memory_context(self, state: SafeClawState) -> str:
        """Add memory context to the conversation"""
        memory_context = ""
        
        # Add relevant memories if available
        if state.get("active_memories"):
            memory_context += "\nRelevant memories:\n"
            for memory in state["active_memories"][:3]:  # Limit to top 3
                memory_context += f"- {memory.get('content', '')[:100]}...\n"
        
        return memory_context
    
    def should_use_tools(self, state: SafeClawState) -> bool:
        """Determine if tools should be used for this request"""
        user_input = state.get("user_input", "").lower()
        
        tool_indicators = [
            "read file", "write file", "search", "analyze", "calculate",
            "list files", "create", "delete", "move", "copy"
        ]
        
        return any(indicator in user_input for indicator in tool_indicators)
