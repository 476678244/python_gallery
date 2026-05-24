"""Memory manager for SafeClaw"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult
from safe_claw.models.config import MemoryConfig
from safe_claw.core.memory.storage import FileStorage
from safe_claw.core.memory.retriever import MemoryRetriever
from safe_claw.core.memory.layers.active import ActiveMemoryLayer
from safe_claw.core.memory.layers.dormant import DormantMemoryLayer
from safe_claw.core.memory.layers.deep import DeepMemoryLayer
from safe_claw.core.memory.layers.forgotten import ForgottenMemoryLayer


class MemoryManager:
    """Main memory manager for SafeClaw"""
    
    def __init__(self, config: MemoryConfig, workspace_path: str):
        """Initialize memory manager
        
        Args:
            config: Memory configuration
            workspace_path: Path to workspace directory
        """
        self.config = config
        self.workspace_path = Path(workspace_path)
        self.storage_path = self.workspace_path / "memory"
        
        # Initialize storage
        self.storage = FileStorage(self.storage_path)
        
        # Initialize retriever
        self.retriever = MemoryRetriever(config)
        
        # Initialize memory layers
        self.active_layer = ActiveMemoryLayer(config, self.storage)
        self.dormant_layer = DormantMemoryLayer(config, self.storage)
        self.deep_layer = DeepMemoryLayer(config, self.storage)
        self.forgotten_layer = ForgottenMemoryLayer(config, self.storage)
        
        self.logger = logging.getLogger(__name__)
    
    def add_memory(self, content: str, importance_score: float = 0.5, 
                   keywords: Optional[List[str]] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new memory
        
        Args:
            content: Memory content
            importance_score: Importance score (0.0 to 1.0)
            keywords: Optional keywords for search
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        memory = Memory(
            content=content,
            layer=MemoryLayer.ACTIVE,
            importance_score=importance_score,
            keywords=keywords or [],
            metadata=metadata or {}
        )
        
        memory_id = self.active_layer.add_memory(memory)
        
        # Check if active layer is full and move least important memory
        if self.active_layer.count() > self.config.max_active_memories:
            least_important = self.active_layer.get_least_important()
            if least_important:
                self._move_memory_between_layers(
                    least_important.id, 
                    MemoryLayer.ACTIVE, 
                    MemoryLayer.DORMANT
                )
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object or None if not found
        """
        # Check each layer
        for layer in [self.active_layer, self.dormant_layer, 
                     self.deep_layer, self.forgotten_layer]:
            memory = layer.get_memory(memory_id)
            if memory:
                # Update access info
                memory.accessed_at = datetime.now()
                memory.access_count += 1
                self.storage.save_memory(memory)
                return memory
        
        return None
    
    def search_memories(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories across all layers
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        all_memories = []
        
        # Collect memories from all layers
        for layer in [self.active_layer, self.dormant_layer, 
                     self.deep_layer, self.forgotten_layer]:
            layer_memories = layer.get_all_memories()
            all_memories.extend(layer_memories)
        
        # Use retriever to search
        return self.retriever.hybrid_search(all_memories, query, max_results)
    
    def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        """Update memory importance score
        
        Args:
            memory_id: Memory ID
            new_importance: New importance score (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        memory.importance_score = new_importance
        self.storage.save_memory(memory)
        return True
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "active_count": self.active_layer.count(),
            "dormant_count": self.dormant_layer.count(),
            "deep_count": self.deep_layer.count(),
            "forgotten_count": self.forgotten_layer.count(),
            "total_count": (self.active_layer.count() + 
                          self.dormant_layer.count() + 
                          self.deep_layer.count() + 
                          self.forgotten_layer.count())
        }
    
    def cleanup_old_memories(self):
        """Clean up old memories based on configuration"""
        cutoff_time = datetime.now() - timedelta(days=self.config.memory_retention_days)
        
        # Check each layer for old memories
        for layer in [self.active_layer, self.dormant_layer, self.deep_layer]:
            memories = layer.get_all_memories()
            
            for memory in memories:
                if memory.created_at < cutoff_time:
                    # Move to forgotten layer
                    self._move_memory_between_layers(
                        memory.id,
                        memory.layer,
                        MemoryLayer.FORGOTTEN
                    )
    
    def get_recent_memories(self, hours: int = 24) -> List[Memory]:
        """Get recent memories
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent memories
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_memories = []
        
        for layer in [self.active_layer, self.dormant_layer, self.deep_layer]:
            memories = layer.get_all_memories()
            recent_memories.extend([
                memory for memory in memories 
                if memory.accessed_at >= cutoff_time
            ])
        
        # Sort by accessed time
        recent_memories.sort(key=lambda m: m.accessed_at, reverse=True)
        return recent_memories
    
    def _move_memory_between_layers(self, memory_id: str, 
                                   from_layer: MemoryLayer, 
                                   to_layer: MemoryLayer) -> bool:
        """Move memory between layers
        
        Args:
            memory_id: Memory ID
            from_layer: Source layer
            to_layer: Target layer
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get memory from source layer
            source_layer = self._get_layer_instance(from_layer)
            target_layer = self._get_layer_instance(to_layer)
            
            memory = source_layer.get_memory(memory_id)
            if not memory:
                return False
            
            # Remove from source
            source_layer.remove_memory(memory_id)
            
            # Update layer and save to target
            memory.layer = to_layer
            target_layer.add_memory(memory)
            
            return True
        except Exception as e:
            self.logger.error(f"Error moving memory {memory_id}: {e}")
            return False
    
    def _get_layer_instance(self, layer: MemoryLayer):
        """Get layer instance by enum value
        
        Args:
            layer: Memory layer enum
            
        Returns:
            Layer instance
        """
        layer_map = {
            MemoryLayer.ACTIVE: self.active_layer,
            MemoryLayer.DORMANT: self.dormant_layer,
            MemoryLayer.DEEP: self.deep_layer,
            MemoryLayer.FORGOTTEN: self.forgotten_layer
        }
        return layer_map.get(layer)
