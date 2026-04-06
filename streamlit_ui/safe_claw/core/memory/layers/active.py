"""Active memory layer for SafeClaw"""

from typing import List, Optional, Dict, Any
import logging

from streamlit_ui.safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult
from streamlit_ui.safe_claw.models.config import MemoryConfig
from streamlit_ui.safe_claw.core.memory.storage import FileStorage


class ActiveMemoryLayer:
    """Active memory layer - stores frequently accessed memories"""
    
    def __init__(self, config: MemoryConfig, storage: FileStorage):
        """Initialize active memory layer
        
        Args:
            config: Memory configuration
            storage: File storage instance
        """
        self.config = config
        self.storage = storage
        self._cache: Dict[str, Memory] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load existing memories
        self._load_memories()
    
    def _load_memories(self):
        """Load existing memories from storage"""
        memory_ids = self.storage.list_memories(MemoryLayer.ACTIVE.value)
        
        for memory_id in memory_ids:
            memory = self.storage.load_memory(memory_id, MemoryLayer.ACTIVE.value)
            if memory:
                self._cache[memory_id] = memory
    
    def add_memory(self, memory: Memory) -> str:
        """Add memory to active layer
        
        Args:
            memory: Memory to add
            
        Returns:
            Memory ID
        """
        memory.layer = MemoryLayer.ACTIVE
        
        # Save to storage
        self.storage.save_memory(memory)
        
        # Add to cache
        self._cache[memory.id] = memory
        
        self.logger.debug(f"Added memory {memory.id} to active layer")
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from active layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object or None if not found
        """
        return self._cache.get(memory_id)
    
    def remove_memory(self, memory_id: str) -> bool:
        """Remove memory from active layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        if memory_id not in self._cache:
            return False
        
        # Remove from storage
        success = self.storage.delete_memory(memory_id, MemoryLayer.ACTIVE.value)
        
        if success:
            # Remove from cache
            del self._cache[memory_id]
            self.logger.debug(f"Removed memory {memory_id} from active layer")
        
        return success
    
    def search(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories in active layer
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        from streamlit_ui.safe_claw.core.memory.retriever import MemoryRetriever
        
        retriever = MemoryRetriever(self.config)
        memories = list(self._cache.values())
        
        return retriever.keyword_search(memories, query, max_results)
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories in active layer
        
        Returns:
            List of all memories
        """
        return list(self._cache.values())
    
    def count(self) -> int:
        """Get number of memories in active layer
        
        Returns:
            Number of memories
        """
        return len(self._cache)
    
    def get_least_important(self) -> Optional[Memory]:
        """Get least important memory in active layer
        
        Returns:
            Least important memory or None if empty
        """
        if not self._cache:
            return None
        
        # Sort by importance score and access count
        memories = list(self._cache.values())
        memories.sort(key=lambda m: (m.importance_score, m.access_count))
        
        return memories[0]
    
    def get_most_important(self) -> Optional[Memory]:
        """Get most important memory in active layer
        
        Returns:
            Most important memory or None if empty
        """
        if not self._cache:
            return None
        
        # Sort by importance score and access count
        memories = list(self._cache.values())
        memories.sort(key=lambda m: (m.importance_score, m.access_count), reverse=True)
        
        return memories[0]
    
    def cleanup_old_memories(self, max_age_days: int = 7) -> int:
        """Clean up old memories from active layer
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of memories cleaned up
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0
        
        memories_to_remove = []
        for memory_id, memory in self._cache.items():
            if memory.accessed_at < cutoff_time and memory.importance_score < 0.5:
                memories_to_remove.append(memory_id)
        
        for memory_id in memories_to_remove:
            if self.remove_memory(memory_id):
                cleaned_count += 1
        
        return cleaned_count
    
    def promote_memory(self, memory_id: str) -> bool:
        """Promote a memory (increase importance)
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        if memory_id not in self._cache:
            return False
        
        memory = self._cache[memory_id]
        memory.importance_score = min(1.0, memory.importance_score + 0.1)
        memory.access_count += 1
        
        self.storage.save_memory(memory)
        return True
    
    def demote_memory(self, memory_id: str) -> bool:
        """Demote a memory (decrease importance)
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        if memory_id not in self._cache:
            return False
        
        memory = self._cache[memory_id]
        memory.importance_score = max(0.0, memory.importance_score - 0.1)
        
        self.storage.save_memory(memory)
        return True
