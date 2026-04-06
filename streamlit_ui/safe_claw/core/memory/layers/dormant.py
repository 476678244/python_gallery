"""Dormant memory layer for SafeClaw"""

from typing import List, Optional, Dict, Any
import logging

from streamlit_ui.safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult
from streamlit_ui.safe_claw.models.config import MemoryConfig
from streamlit_ui.safe_claw.core.memory.storage import FileStorage


class DormantMemoryLayer:
    """Dormant memory layer - stores infrequently accessed memories"""
    
    def __init__(self, config: MemoryConfig, storage: FileStorage):
        """Initialize dormant memory layer
        
        Args:
            config: Memory configuration
            storage: File storage instance
        """
        self.config = config
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    def add_memory(self, memory: Memory) -> str:
        """Add memory to dormant layer
        
        Args:
            memory: Memory to add
            
        Returns:
            Memory ID
        """
        memory.layer = MemoryLayer.DORMANT
        
        # Save to storage
        self.storage.save_memory(memory)
        
        self.logger.debug(f"Added memory {memory.id} to dormant layer")
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from dormant layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object or None if not found
        """
        return self.storage.load_memory(memory_id, MemoryLayer.DORMANT.value)
    
    def remove_memory(self, memory_id: str) -> bool:
        """Remove memory from dormant layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        success = self.storage.delete_memory(memory_id, MemoryLayer.DORMANT.value)
        
        if success:
            self.logger.debug(f"Removed memory {memory_id} from dormant layer")
        
        return success
    
    def search(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories in dormant layer
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        from streamlit_ui.safe_claw.core.memory.retriever import MemoryRetriever
        
        retriever = MemoryRetriever(self.config)
        memories = self.get_all_memories()
        
        return retriever.keyword_search(memories, query, max_results)
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories in dormant layer
        
        Returns:
            List of all memories
        """
        memory_ids = self.storage.list_memories(MemoryLayer.DORMANT.value)
        memories = []
        
        for memory_id in memory_ids:
            memory = self.storage.load_memory(memory_id, MemoryLayer.DORMANT.value)
            if memory:
                memories.append(memory)
        
        return memories
    
    def count(self) -> int:
        """Get number of memories in dormant layer
        
        Returns:
            Number of memories
        """
        return len(self.storage.list_memories(MemoryLayer.DORMANT.value))
    
    def activate_memory(self, memory_id: str) -> Optional[Memory]:
        """Activate a memory (move to active layer)
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object if successful, None otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        # Remove from dormant layer
        self.remove_memory(memory_id)
        
        # Update layer and importance
        memory.layer = MemoryLayer.ACTIVE
        memory.importance_score = min(1.0, memory.importance_score + 0.2)
        memory.access_count += 1
        
        return memory
    
    def get_old_memories(self, days_threshold: int = 30) -> List[Memory]:
        """Get memories older than threshold
        
        Args:
            days_threshold: Age threshold in days
            
        Returns:
            List of old memories
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_threshold)
        old_memories = []
        
        for memory in self.get_all_memories():
            if memory.accessed_at < cutoff_time:
                old_memories.append(memory)
        
        return old_memories
    
    def move_to_deep(self, memory_id: str) -> bool:
        """Move memory to deep storage
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.storage.move_memory(
            memory_id, 
            MemoryLayer.DORMANT.value, 
            MemoryLayer.DEEP.value
        )
    
    def cleanup_low_importance(self, min_importance: float = 0.3) -> int:
        """Clean up low importance memories
        
        Args:
            min_importance: Minimum importance threshold
            
        Returns:
            Number of memories cleaned up
        """
        memories_to_remove = []
        
        for memory in self.get_all_memories():
            if memory.importance_score < min_importance:
                memories_to_remove.append(memory.id)
        
        cleaned_count = 0
        for memory_id in memories_to_remove:
            if self.move_to_deep(memory_id):
                cleaned_count += 1
        
        return cleaned_count
