"""Router agent for SafeClaw"""

import logging
import json
from typing import Dict, Any, List

from safe_claw.core.agents.base_agent import BaseAgent
from safe_claw.core.graph.state import SafeClawState
from safe_claw.services.llm_gateway import LLMService

logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """Router agent that determines which agent should handle requests"""
    
    def __init__(self, llm_service: LLMService, config: Dict[str, Any] = None):
        super().__init__("router_agent", llm_service, config)
        self.agent_registry = config.get("agent_registry", {})
        self.default_agent = config.get("default_agent", "chat_agent")
    
    def get_system_prompt(self) -> str:
        """Get system prompt for router agent"""
        available_agents = list(self.agent_registry.keys())
        
        return f"""You are a router agent for SafeClaw. Your job is to determine which agent should handle the user's request.

Available agents:
{chr(10).join(f"- {agent}" for agent in available_agents)}

Analyze the user's request and determine the most appropriate agent. Consider:
- Is this a simple chat conversation? -> chat_agent
- Does this require memory operations? -> memory_agent
- Does this require safety checks? -> safety_agent
- Does this require file operations? -> file_agent (if available)

Respond with a JSON object containing:
{{
  "selected_agent": "agent_name",
  "confidence": 0.8,
  "reasoning": "Brief explanation"
}}

If unsure, default to "{self.default_agent}"."""
    
    def process(self, state: SafeClawState) -> SafeClawState:
        """Process routing decision"""
        if not self.validate_state(state):
            state["current_agent"] = self.default_agent
            return state
        
        try:
            # Get routing decision
            routing_response = self.invoke_response(state)
            
            # Parse routing decision
            routing_decision = self._parse_routing_response(routing_response)
            
            # Update state with routing decision
            state["current_agent"] = routing_decision["selected_agent"]
            state["agent_outputs"] = state.get("agent_outputs", {})
            state["agent_outputs"]["router_decision"] = routing_decision
            
            logger.info(f"Router selected {routing_decision['selected_agent']} for session {state['session_id']}")
            
        except Exception as e:
            logger.error(f"Error in router agent: {e}")
            state["current_agent"] = self.default_agent
            state["agent_outputs"] = state.get("agent_outputs", {})
            state["agent_outputs"]["router_error"] = str(e)
        
        return state
    
    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """Parse the routing response from LLM"""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                routing = json.loads(json_str)
                
                # Validate routing decision
                if "selected_agent" not in routing:
                    routing["selected_agent"] = self.default_agent
                
                if routing["selected_agent"] not in self.agent_registry:
                    logger.warning(f"Unknown agent {routing['selected_agent']}, using default")
                    routing["selected_agent"] = self.default_agent
                
                routing["confidence"] = routing.get("confidence", 0.5)
                routing["reasoning"] = routing.get("reasoning", "No reasoning provided")
                
                return routing
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse routing response as JSON: {response}")
        except Exception as e:
            logger.error(f"Error parsing routing response: {e}")
        
        # Fallback to default
        return {
            "selected_agent": self.default_agent,
            "confidence": 0.0,
            "reasoning": "Failed to parse routing response"
        }
    
    def route_by_keywords(self, user_input: str) -> str:
        """Simple keyword-based routing fallback"""
        user_input_lower = user_input.lower()
        
        # Memory-related keywords
        memory_keywords = ["remember", "recall", "memory", "forget", "previous", "earlier"]
        if any(keyword in user_input_lower for keyword in memory_keywords):
            return "memory_agent"
        
        # Safety-related keywords
        safety_keywords = ["dangerous", "unsafe", "harmful", "security", "confirm", "permission"]
        if any(keyword in user_input_lower for keyword in safety_keywords):
            return "safety_agent"
        
        # File-related keywords
        file_keywords = ["file", "read", "write", "save", "open", "create", "delete"]
        if any(keyword in user_input_lower for keyword in file_keywords):
            return "file_agent" if "file_agent" in self.agent_registry else self.default_agent
        
        return self.default_agent
    
    def update_agent_registry(self, agent_registry: Dict[str, Any]):
        """Update the available agent registry"""
        self.agent_registry = agent_registry
        logger.info(f"Updated agent registry with {len(agent_registry)} agents")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_routings": self.execution_count,
            "available_agents": list(self.agent_registry.keys()),
            "default_agent": self.default_agent
        }
