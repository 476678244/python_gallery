"""File storage for SafeClaw memory system"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from streamlit_ui.safe_claw.models.memory import Memory, MemoryLayer


class FileStorage:
    """File-based storage for memories"""
    
    def __init__(self, storage_path: Path):
        """Initialize file storage
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)
        
        # Create storage directory and layer subdirectories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        for layer in MemoryLayer:
            layer_path = self.storage_path / layer.value
            layer_path.mkdir(exist_ok=True)
    
    def save_memory(self, memory: Memory) -> bool:
        """Save memory to file
        
        Args:
            memory: Memory object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            layer_path = self.storage_path / memory.layer.value
            file_path = layer_path / f"{memory.id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memory.dict(), f, indent=2, default=str)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving memory {memory.id}: {e}")
            return False
    
    def load_memory(self, memory_id: str, layer: str) -> Optional[Memory]:
        """Load memory from file
        
        Args:
            memory_id: Memory ID
            layer: Memory layer name
            
        Returns:
            Memory object or None if not found
        """
        try:
            layer_path = self.storage_path / layer
            file_path = layer_path / f"{memory_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Memory(**data)
        except Exception as e:
            self.logger.error(f"Error loading memory {memory_id}: {e}")
            return None
    
    def delete_memory(self, memory_id: str, layer: str) -> bool:
        """Delete memory file
        
        Args:
            memory_id: Memory ID
            layer: Memory layer name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            layer_path = self.storage_path / layer
            file_path = layer_path / f"{memory_id}.json"
            
            if file_path.exists():
                file_path.unlink()
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    def move_memory(self, memory_id: str, from_layer: str, to_layer: str) -> bool:
        """Move memory between layers
        
        Args:
            memory_id: Memory ID
            from_layer: Source layer name
            to_layer: Target layer name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load memory from source layer
            memory = self.load_memory(memory_id, from_layer)
            if not memory:
                return False
            
            # Delete from source layer
            self.delete_memory(memory_id, from_layer)
            
            # Update layer and save to target layer
            memory.layer = MemoryLayer(to_layer)
            self.save_memory(memory)
            
            return True
        except Exception as e:
            self.logger.error(f"Error moving memory {memory_id}: {e}")
            return False
    
    def list_memories(self, layer: str) -> List[str]:
        """List all memory IDs in a layer
        
        Args:
            layer: Memory layer name
            
        Returns:
            List of memory IDs
        """
        try:
            layer_path = self.storage_path / layer
            memory_ids = []
            
            for file_path in layer_path.glob("*.json"):
                memory_ids.append(file_path.stem)
            
            return memory_ids
        except Exception as e:
            self.logger.error(f"Error listing memories in layer {layer}: {e}")
            return []
    
    def get_layer_stats(self, layer: str) -> Dict[str, Any]:
        """Get statistics for a layer
        
        Args:
            layer: Memory layer name
            
        Returns:
            Dictionary with layer statistics
        """
        try:
            layer_path = self.storage_path / layer
            memory_files = list(layer_path.glob("*.json"))
            
            stats = {
                "count": len(memory_files),
                "total_size_bytes": sum(f.stat().st_size for f in memory_files),
                "oldest_memory": None,
                "newest_memory": None
            }
            
            if memory_files:
                # Get file modification times
                file_times = [(f, f.stat().st_mtime) for f in memory_files]
                oldest_file = min(file_times, key=lambda x: x[1])
                newest_file = max(file_times, key=lambda x: x[1])
                
                stats["oldest_memory"] = oldest_file[0].stem
                stats["newest_memory"] = newest_file[0].stem
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting stats for layer {layer}: {e}")
            return {"count": 0, "total_size_bytes": 0}
    
    def cleanup_empty_files(self) -> int:
        """Clean up empty or corrupted files
        
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        
        for layer in MemoryLayer:
            layer_path = self.storage_path / layer.value
            
            for file_path in layer_path.glob("*.json"):
                try:
                    # Try to load the file to check if it's valid
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if file is empty or invalid
                    if not data or not isinstance(data, dict):
                        file_path.unlink()
                        cleaned_count += 1
                        
                except (json.JSONDecodeError, Exception):
                    # File is corrupted, remove it
                    file_path.unlink()
                    cleaned_count += 1
        
        return cleaned_count
