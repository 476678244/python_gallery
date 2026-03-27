"""Memory agent for SafeClaw"""

import logging
from typing import Dict, Any, List

from safe_claw.core.agents.base_agent import BaseAgent
from safe_claw.core.graph.state import SafeClawState
from safe_claw.services.llm_gateway import LLMService

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """Memory agent for managing memory operations"""
    
    def __init__(self, llm_service: LLMService, memory_manager, config: Dict[str, Any] = None):
        super().__init__("memory_agent", llm_service, config)
        self.memory_manager = memory_manager
        self.max_search_results = config.get("max_search_results", 10)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for memory agent"""
        return """You are the Memory Agent for SafeClaw. Your purpose is to manage memory operations including:

1. Storing new memories based on conversations
2. Retrieving relevant memories for context
3. Searching through memory archives
4. Managing memory importance and organization

When users ask about previous conversations or want you to remember something, handle their request appropriately.

For memory storage, extract key information and assign appropriate importance scores (0.0-1.0):
- 0.8-1.0: Critical information, user preferences, important facts
- 0.6-0.8: Useful context, project details, recurring topics
- 0.4-0.6: General conversation, casual information
- 0.0-0.4: Temporary or minor details

Always be helpful and explain what memory operations you're performing."""
    
    def process(self, state: SafeClawState) -> SafeClawState:
        """Process memory operations"""
        if not self.validate_state(state):
            state["response"] = "Error: Invalid state provided to memory agent"
            return state
        
        try:
            user_input = state.get("user_input", "").lower()
            
            # Determine memory operation
            if "remember" in user_input or "store" in user_input or "save" in user_input:
                response = self._handle_memory_storage(state)
            elif "search" in user_input or "find" in user_input or "recall" in user_input:
                response = self._handle_memory_search(state)
            elif "forget" in user_input or "delete" in user_input:
                response = self._handle_memory_deletion(state)
            else:
                response = self._handle_conversation_memory(state)
            
            # Update state
            state = self.update_state(state, response)
            
            logger.info(f"Memory agent processed request for session {state['session_id']}")
            
        except Exception as e:
            logger.error(f"Error in memory agent: {e}")
            state["response"] = f"Sorry, I encountered a memory error: {str(e)}"
        
        return state
    
    def _handle_memory_storage(self, state: SafeClawState) -> str:
        """Handle explicit memory storage requests"""
        user_input = state.get("user_input", "")
        
        # Extract what to remember
        content = self._extract_memory_content(user_input)
        if not content:
            return "I'm not sure what you'd like me to remember. Could you be more specific?"
        
        # Determine importance
        importance = self._assess_importance(user_input)
        
        # Extract keywords
        keywords = self._extract_keywords(content)
        
        # Store memory
        memory_id = self.memory_manager.add_memory(
            content=content,
            importance_score=importance,
            keywords=keywords,
            metadata={"source": "user_request", "session_id": state["session_id"]}
        )
        
        return f"I've remembered: \"{content}\" (Importance: {importance:.1f})"
    
    def _handle_memory_search(self, state: SafeClawState) -> str:
        """Handle memory search requests"""
        user_input = state.get("user_input", "")
        
        # Extract search query
        query = self._extract_search_query(user_input)
        if not query:
            return "What would you like me to search for in my memory?"
        
        # Search memories
        results = self.memory_manager.search_memories(query, self.max_search_results)
        
        if not results:
            return f"I couldn't find any memories about \"{query}\"."
        
        # Format results
        response = f"Found {len(results)} memories about \"{query}\":\n\n"
        for i, result in enumerate(results[:5], 1):  # Show top 5
            memory = result.memory
            response += f"{i}. {memory.content[:150]}{'...' if len(memory.content) > 150 else ''}\n"
            response += f"   (Score: {result.score:.2f}, Importance: {memory.importance_score:.1f})\n\n"
        
        return response
    
    def _handle_memory_deletion(self, state: SafeClawState) -> str:
        """Handle memory deletion requests"""
        # For now, return a safety message
        return "For safety reasons, I don't delete memories on request. Memories are automatically managed based on importance and age."
    
    def _handle_conversation_memory(self, state: SafeClawState) -> str:
        """Handle automatic memory storage from conversation"""
        user_input = state.get("user_input", "")
        
        # Check if this is worth remembering
        if self._should_remember(user_input):
            content = user_input
            importance = self._assess_importance(user_input)
            keywords = self._extract_keywords(content)
            
            self.memory_manager.add_memory(
                content=content,
                importance_score=importance,
                keywords=keywords,
                metadata={"source": "conversation", "session_id": state["session_id"]}
            )
            
            return "I've noted that information for future reference."
        
        return "I'm ready to help with memory operations. You can ask me to remember, search, or recall information."
    
    def _extract_memory_content(self, user_input: str) -> str:
        """Extract what to remember from user input"""
        # Simple extraction - look for patterns
        indicators = ["remember that", "store this", "save this", "remember"]
        
        for indicator in indicators:
            if indicator in user_input.lower():
                # Extract content after indicator
                idx = user_input.lower().find(indicator)
                content = user_input[idx + len(indicator):].strip()
                # Remove quotes if present
                content = content.strip('"\'')
                return content
        
        return ""
    
    def _extract_search_query(self, user_input: str) -> str:
        """Extract search query from user input"""
        indicators = ["search for", "find", "recall", "remember about"]
        
        for indicator in indicators:
            if indicator in user_input.lower():
                idx = user_input.lower().find(indicator)
                query = user_input[idx + len(indicator):].strip()
                return query.strip('"\'')
        
        return user_input.strip()
    
    def _assess_importance(self, text: str) -> float:
        """Assess importance score for text"""
        text_lower = text.lower()
        
        # High importance indicators
        high_importance = ["important", "critical", "never forget", "always", "preference"]
        if any(indicator in text_lower for indicator in high_importance):
            return 0.9
        
        # Medium importance indicators
        medium_importance = ["remember", "note", "keep in mind", "project", "work"]
        if any(indicator in text_lower for indicator in medium_importance):
            return 0.7
        
        # Low importance indicators
        low_importance = ["maybe", "perhaps", "just", "casually"]
        if any(indicator in text_lower for indicator in low_importance):
            return 0.3
        
        # Default importance
        return 0.5
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return unique keywords, limited to 10
        return list(set(keywords))[:10]
    
    def _should_remember(self, text: str) -> bool:
        """Determine if text should be automatically remembered"""
        text_lower = text.lower()
        
        # Don't remember very short or common phrases
        if len(text) < 10:
            return False
        
        # Don't remember greetings
        greetings = ["hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye"]
        if any(greeting in text_lower for greeting in greetings):
            return False
        
        # Remember questions, statements about preferences, or work-related content
        question_indicators = ["?", "how to", "what is", "where", "when", "why"]
        preference_indicators = ["i like", "i prefer", "i want", "i need", "i think"]
        work_indicators = ["project", "work", "task", "deadline", "meeting"]
        
        return (any(indicator in text_lower for indicator in question_indicators) or
                any(indicator in text_lower for indicator in preference_indicators) or
                any(indicator in text_lower for indicator in work_indicators))
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return self.memory_manager.get_memory_stats()
