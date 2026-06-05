"""Deep memory layer for SafeClaw"""

from typing import List, Optional, Dict, Any
import logging

from safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult
from safe_claw.models.config import MemoryConfig
from safe_claw.core.memory.storage import FileStorage


class DeepMemoryLayer:
    """Deep memory layer - stores long-term, important memories"""
    
    def __init__(self, config: MemoryConfig, storage: FileStorage):
        """Initialize deep memory layer
        
        Args:
            config: Memory configuration
            storage: File storage instance
        """
        self.config = config
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    def add_memory(self, memory: Memory) -> str:
        """Add memory to deep layer
        
        Args:
            memory: Memory to add
            
        Returns:
            Memory ID
        """
        memory.layer = MemoryLayer.DEEP
        
        # Save to storage
        self.storage.save_memory(memory)
        
        self.logger.debug(f"Added memory {memory.id} to deep layer")
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from deep layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object or None if not found
        """
        return self.storage.load_memory(memory_id, MemoryLayer.DEEP.value)
    
    def remove_memory(self, memory_id: str) -> bool:
        """Remove memory from deep layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        success = self.storage.delete_memory(memory_id, MemoryLayer.DEEP.value)
        
        if success:
            self.logger.debug(f"Removed memory {memory_id} from deep layer")
        
        return success
    
    def search(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories in deep layer
        
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
        """Get all memories in deep layer
        
        Returns:
            List of all memories
        """
        memory_ids = self.storage.list_memories(MemoryLayer.DEEP.value)
        memories = []
        
        for memory_id in memory_ids:
            memory = self.storage.load_memory(memory_id, MemoryLayer.DEEP.value)
            if memory:
                memories.append(memory)
        
        return memories
    
    def count(self) -> int:
        """Get number of memories in deep layer
        
        Returns:
            Number of memories
        """
        return len(self.storage.list_memories(MemoryLayer.DEEP.value))
    
    def get_high_importance_memories(self, min_importance: float = 0.7) -> List[Memory]:
        """Get high importance memories
        
        Args:
            min_importance: Minimum importance threshold
            
        Returns:
            List of high importance memories
        """
        high_importance_memories = []
        
        for memory in self.get_all_memories():
            if memory.importance_score >= min_importance:
                high_importance_memories.append(memory)
        
        return high_importance_memories
    
    def promote_to_active(self, memory_id: str) -> Optional[Memory]:
        """Promote memory to active layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object if successful, None otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        # Remove from deep layer
        self.remove_memory(memory_id)
        
        # Update layer and boost importance
        memory.layer = MemoryLayer.ACTIVE
        memory.importance_score = min(1.0, memory.importance_score + 0.3)
        memory.access_count += 1
        
        return memory
    
    def archive_memory(self, memory_id: str) -> bool:
        """Archive memory to forgotten layer
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.storage.move_memory(
            memory_id,
            MemoryLayer.DEEP.value,
            MemoryLayer.FORGOTTEN.value
        )
    
    def get_forgotten_candidates(self, days_inactive: int = 90) -> List[Memory]:
        """Get candidates for forgotten layer
        
        Args:
            days_inactive: Days of inactivity threshold
            
        Returns:
            List of memories to consider for forgetting
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_inactive)
        candidates = []
        
        for memory in self.get_all_memories():
            if (memory.accessed_at < cutoff_time and 
                memory.importance_score < 0.5):
                candidates.append(memory)
        
        return candidates
    
    def cleanup_archived(self) -> int:
        """Clean up and archive old memories
        
        Returns:
            Number of memories archived
        """
        candidates = self.get_forgotten_candidates()
        archived_count = 0
        
        for memory in candidates:
            if self.archive_memory(memory.id):
                archived_count += 1
        
        return archived_count
    
    def consolidate_memories(self) -> int:
        """Consolidate similar memories
        
        Returns:
            Number of memories consolidated
        """
        # TODO: Implement memory consolidation logic
        # This would identify similar memories and merge them
        return 0
