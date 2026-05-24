"""Forgotten memory layer for SafeClaw"""

from typing import List, Optional, Dict, Any
import logging

from safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult
from safe_claw.models.config import MemoryConfig
from safe_claw.core.memory.storage import FileStorage


class ForgottenMemoryLayer:
    """Forgotten memory layer - stores archived memories"""
    
    def __init__(self, config: MemoryConfig, storage: FileStorage):
        """Initialize forgotten memory layer
        
        Args:
            config: Memory configuration
            storage: File storage instance
        """
        self.config = config
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    def add_memory(self, memory: Memory) -> str:
        """Add memory to forgotten layer
        
        Args:
            memory: Memory to add
            
        Returns:
            Memory ID
        """
        memory.layer = MemoryLayer.FORGOTTEN
        
        # Save to storage
        self.storage.save_memory(memory)
        
        self.logger.debug(f"Added memory {memory.id} to forgotten layer")
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from forgotten layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object or None if not found
        """
        return self.storage.load_memory(memory_id, MemoryLayer.FORGOTTEN.value)
    
    def remove_memory(self, memory_id: str) -> bool:
        """Remove memory from forgotten layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        success = self.storage.delete_memory(memory_id, MemoryLayer.FORGOTTEN.value)
        
        if success:
            self.logger.debug(f"Removed memory {memory_id} from forgotten layer")
        
        return success
    
    def search(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories in forgotten layer
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        from safe_claw.core.memory.retriever import MemoryRetriever
        
        retriever = MemoryRetriever(self.config)
        memories = self.get_all_memories()
        
        return retriever.keyword_search(memories, query, max_results)
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories in forgotten layer
        
        Returns:
            List of all memories
        """
        memory_ids = self.storage.list_memories(MemoryLayer.FORGOTTEN.value)
        memories = []
        
        for memory_id in memory_ids:
            memory = self.storage.load_memory(memory_id, MemoryLayer.FORGOTTEN.value)
            if memory:
                memories.append(memory)
        
        return memories
    
    def count(self) -> int:
        """Get number of memories in forgotten layer
        
        Returns:
            Number of memories
        """
        return len(self.storage.list_memories(MemoryLayer.FORGOTTEN.value))
    
    def restore_memory(self, memory_id: str, target_layer: MemoryLayer = MemoryLayer.DORMANT) -> Optional[Memory]:
        """Restore memory from forgotten layer
        
        Args:
            memory_id: Memory ID
            target_layer: Target layer to restore to
            
        Returns:
            Memory object if successful, None otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        # Remove from forgotten layer
        self.remove_memory(memory_id)
        
        # Update layer and restore some importance
        memory.layer = target_layer
        memory.importance_score = min(0.5, memory.importance_score + 0.1)
        
        return memory
    
    def purge_old_memories(self, days_threshold: int = 365) -> int:
        """Permanently delete very old memories
        
        Args:
            days_threshold: Age threshold in days
            
        Returns:
            Number of memories purged
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_threshold)
        memories_to_purge = []
        
        for memory in self.get_all_memories():
            if memory.created_at < cutoff_time:
                memories_to_purge.append(memory.id)
        
        purged_count = 0
        for memory_id in memories_to_purge:
            if self.remove_memory(memory_id):
                purged_count += 1
        
        return purged_count
    
    def get_memories_by_importance(self, min_importance: float = 0.0) -> List[Memory]:
        """Get memories filtered by importance
        
        Args:
            min_importance: Minimum importance threshold
            
        Returns:
            List of memories meeting criteria
        """
        filtered_memories = []
        
        for memory in self.get_all_memories():
            if memory.importance_score >= min_importance:
                filtered_memories.append(memory)
        
        return filtered_memories
    
    def get_cleanup_candidates(self) -> List[Memory]:
        """Get candidates for cleanup
        
        Returns:
            List of memories that could be cleaned up
        """
        candidates = []
        
        for memory in self.get_all_memories():
            # Low importance and old
            if (memory.importance_score < 0.2 and 
                memory.access_count < 2):
                candidates.append(memory)
        
        return candidates
    
    def emergency_restore(self, query: str, max_results: int = 5) -> List[Memory]:
        """Emergency restore for critical memories
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of restored memories
        """
        # Search in forgotten layer
        results = self.search(query, max_results)
        
        restored_memories = []
        for result in results:
            memory = self.restore_memory(result.memory.id, MemoryLayer.ACTIVE)
            if memory:
                restored_memories.append(memory)
        
        return restored_memories
