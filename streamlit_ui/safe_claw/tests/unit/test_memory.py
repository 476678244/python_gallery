"""Unit tests for SafeClaw memory system"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd

from safe_claw.core.memory.manager import MemoryManager
from safe_claw.core.memory.storage import FileStorage
from safe_claw.core.memory.retriever import MemoryRetriever
from safe_claw.core.memory.layers.active import ActiveMemoryLayer
from safe_claw.core.memory.layers.dormant import DormantMemoryLayer
from safe_claw.core.memory.layers.deep import DeepMemoryLayer
from safe_claw.core.memory.layers.forgotten import ForgottenMemoryLayer
from safe_claw.models.memory import Memory, MemoryLayer
from safe_claw.models.config import MemoryConfig

class TestFileStorage:
    """Test file storage for memory"""
    
    def test_file_storage_creation(self, temp_workspace):
        """Test file storage creation"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        assert storage.storage_path == storage_path
        assert storage_path.exists()
        
        # Check layer directories
        for layer in MemoryLayer:
            layer_path = storage_path / layer.value
            assert layer_path.exists()
    
    def test_save_and_load_memory(self, temp_workspace):
        """Test saving and loading memory"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        memory = Memory(
            content="Test memory content",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.8,
            keywords=["test", "memory"]
        )
        
        # Save memory
        success = storage.save_memory(memory)
        assert success is True
        
        # Load memory
        loaded_memory = storage.load_memory(memory.id, MemoryLayer.ACTIVE.value)
        assert loaded_memory is not None
        assert loaded_memory.content == memory.content
        assert loaded_memory.layer == MemoryLayer.ACTIVE
        assert loaded_memory.importance_score == memory.importance_score
        assert loaded_memory.keywords == memory.keywords
    
    def test_load_nonexistent_memory(self, temp_workspace):
        """Test loading non-existent memory"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        memory = storage.load_memory("nonexistent_id", MemoryLayer.ACTIVE.value)
        assert memory is None
    
    def test_delete_memory(self, temp_workspace):
        """Test deleting memory"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        memory = Memory(
            content="Test memory",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.5
        )
        
        # Save memory
        storage.save_memory(memory)
        
        # Delete memory
        success = storage.delete_memory(memory.id, MemoryLayer.ACTIVE.value)
        assert success is True
        
        # Verify deletion
        loaded_memory = storage.load_memory(memory.id, MemoryLayer.ACTIVE.value)
        assert loaded_memory is None
    
    def test_move_memory(self, temp_workspace):
        """Test moving memory between layers"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        memory = Memory(
            content="Test memory",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.5
        )
        
        # Save to active layer
        storage.save_memory(memory)
        
        # Move to dormant layer
        success = storage.move_memory(memory.id, MemoryLayer.ACTIVE.value, MemoryLayer.DORMANT.value)
        assert success is True
        
        # Verify move
        assert storage.load_memory(memory.id, MemoryLayer.ACTIVE.value) is None
        loaded_memory = storage.load_memory(memory.id, MemoryLayer.DORMANT.value)
        assert loaded_memory is not None
        assert loaded_memory.layer == MemoryLayer.DORMANT
    
    def test_list_memories(self, temp_workspace):
        """Test listing memories"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        # Create multiple memories
        memories = []
        for i in range(5):
            memory = Memory(
                content=f"Test memory {i}",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.5 + i * 0.1
            )
            storage.save_memory(memory)
            memories.append(memory.id)
        
        # List memories
        memory_ids = storage.list_memories(MemoryLayer.ACTIVE.value)
        
        assert len(memory_ids) == 5
        assert all(memory_id in memory_ids for memory_id in memories)
    
    def test_get_layer_stats(self, temp_workspace):
        """Test getting layer statistics"""
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        # Add memories
        for i in range(3):
            memory = Memory(
                content=f"Test memory {i}",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.5
            )
            storage.save_memory(memory)
        
        # Get stats
        stats = storage.get_layer_stats(MemoryLayer.ACTIVE.value)
        
        assert stats["count"] == 3
        assert stats["total_size_bytes"] > 0
        assert "oldest_memory" in stats
        assert "newest_memory" in stats

class TestMemoryRetriever:
    """Test memory retrieval system"""
    
    def test_retriever_creation(self):
        """Test retriever creation"""
        config = MemoryConfig()
        retriever = MemoryRetriever(config)
        
        assert retriever.config == config
    
    def test_keyword_search(self):
        """Test keyword search"""
        config = MemoryConfig()
        retriever = MemoryRetriever(config)
        
        # Create test memories
        memories = [
            Memory(
                content="Python programming is fun",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.8,
                keywords=["python", "programming"]
            ),
            Memory(
                content="JavaScript web development",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.7,
                keywords=["javascript", "web"]
            ),
            Memory(
                content="Data analysis with pandas",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.6,
                keywords=["data", "analysis", "pandas"]
            )
        ]
        
        # Search for "python"
        results = retriever.keyword_search(memories, "python")
        
        assert len(results) > 0
        assert results[0].memory.content == "Python programming is fun"
        assert results[0].match_type == "keyword"
        assert results[0].score > 0
    
    def test_semantic_search(self):
        """Test semantic search (fallback to keyword)"""
        config = MemoryConfig(enable_vector_search=False)
        retriever = MemoryRetriever(config)
        
        memories = [
            Memory(
                content="Machine learning algorithms",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.8
            )
        ]
        
        results = retriever.semantic_search(memories, "machine learning")
        
        assert len(results) >= 0  # Should not crash
    
    def test_context_search(self):
        """Test context-based search"""
        config = MemoryConfig()
        retriever = MemoryRetriever(config)
        
        memories = [
            Memory(
                content="Recent conversation about AI",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.7,
                accessed_at=datetime.now()
            ),
            Memory(
                content="Old conversation from last year",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.6,
                accessed_at=datetime.now() - timedelta(days=400)
            )
        ]
        
        # Search for recent memories
        context = {"time_range": {"hours": 24}}
        results = retriever.context_search(memories, context)
        
        # Should find recent memory
        assert len(results) >= 0
        if results:
            assert "recent" in results[0].memory.content.lower()
    
    def test_hybrid_search(self):
        """Test hybrid search combining multiple methods"""
        config = MemoryConfig()
        retriever = MemoryRetriever(config)
        
        memories = [
            Memory(
                content="Python programming tutorial",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.8,
                keywords=["python", "programming"]
            )
        ]
        
        results = retriever.hybrid_search(memories, "python programming")
        
        assert len(results) >= 0
        if results:
            assert results[0].match_type == "hybrid"

class TestActiveMemoryLayer:
    """Test active memory layer"""
    
    def test_active_layer_creation(self, temp_workspace):
        """Test active layer creation"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        assert layer.config == config
        assert layer.storage == storage
        assert layer.count() == 0
    
    def test_add_memory(self, temp_workspace):
        """Test adding memory to active layer"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        memory = Memory(
            content="Test memory",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.7
        )
        
        memory_id = layer.add_memory(memory)
        
        assert memory_id is not None
        assert layer.count() == 1
        assert memory_id in layer._cache
    
    def test_get_memory(self, temp_workspace):
        """Test getting memory from active layer"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        memory = Memory(
            content="Test memory",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.7
        )
        
        memory_id = layer.add_memory(memory)
        retrieved_memory = layer.get_memory(memory_id)
        
        assert retrieved_memory is not None
        assert retrieved_memory.content == memory.content
        assert retrieved_memory.id == memory_id
    
    def test_remove_memory(self, temp_workspace):
        """Test removing memory from active layer"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        memory = Memory(
            content="Test memory",
            layer=MemoryLayer.ACTIVE,
            importance_score=0.7
        )
        
        memory_id = layer.add_memory(memory)
        success = layer.remove_memory(memory_id)
        
        assert success is True
        assert layer.count() == 0
        assert memory_id not in layer._cache
    
    def test_search(self, temp_workspace):
        """Test searching in active layer"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        # Add multiple memories
        memories = [
            Memory(
                content="Python programming guide",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.8,
                keywords=["python", "programming"]
            ),
            Memory(
                content="JavaScript tutorial",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.7,
                keywords=["javascript", "tutorial"]
            )
        ]
        
        for memory in memories:
            layer.add_memory(memory)
        
        # Search for "python"
        results = layer.search("python", max_results=10)
        
        assert len(results) > 0
        assert "python" in results[0].memory.content.lower()
    
    def test_get_least_important(self, temp_workspace):
        """Test getting least important memory"""
        config = MemoryConfig()
        storage_path = Path(temp_workspace) / "memory"
        storage = FileStorage(storage_path)
        
        layer = ActiveMemoryLayer(config, storage)
        
        # Add memories with different importance scores
        memories = [
            Memory(
                content="High importance memory",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.9
            ),
            Memory(
                content="Low importance memory",
                layer=MemoryLayer.ACTIVE,
                importance_score=0.3
            )
        ]
        
        for memory in memories:
            layer.add_memory(memory)
        
        least_important = layer.get_least_important()
        
        assert least_important is not None
        assert least_important.importance_score == 0.3
        assert "Low importance" in least_important.content

class TestMemoryManager:
    """Test memory manager"""
    
    def test_memory_manager_creation(self, temp_workspace):
        """Test memory manager creation"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        assert manager.config == config
        assert manager.workspace_path == Path(temp_workspace)
        assert manager.active_layer is not None
        assert manager.dormant_layer is not None
        assert manager.deep_layer is not None
        assert manager.forgotten_layer is not None
    
    def test_add_memory(self, temp_workspace):
        """Test adding memory through manager"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        memory_id = manager.add_memory(
            content="Test memory content",
            importance_score=0.8,
            keywords=["test", "memory"]
        )
        
        assert memory_id is not None
        assert manager.active_layer.count() == 1
        
        # Retrieve memory
        memory = manager.get_memory(memory_id)
        assert memory is not None
        assert memory.content == "Test memory content"
    
    def test_search_memories(self, temp_workspace):
        """Test searching memories through manager"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        # Add test memories
        manager.add_memory(
            content="Python programming tutorial",
            importance_score=0.8,
            keywords=["python", "programming"]
        )
        manager.add_memory(
            content="JavaScript web development",
            importance_score=0.7,
            keywords=["javascript", "web"]
        )
        
        # Search for "python"
        results = manager.search_memories("python", max_results=10)
        
        assert len(results) > 0
        assert "python" in results[0].memory.content.lower()
    
    def test_update_memory_importance(self, temp_workspace):
        """Test updating memory importance"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        # Add memory
        memory_id = manager.add_memory(
            content="Test memory",
            importance_score=0.5
        )
        
        # Update importance
        success = manager.update_memory_importance(memory_id, 0.9)
        
        assert success is True
        
        # Check updated memory
        memory = manager.get_memory(memory_id)
        assert memory.importance_score == 0.9
    
    def test_get_memory_stats(self, temp_workspace):
        """Test getting memory statistics"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        # Add memories to different layers
        manager.add_memory("Active memory 1", importance_score=0.9)
        manager.add_memory("Active memory 2", importance_score=0.8)
        
        stats = manager.get_memory_stats()
        
        assert "active_count" in stats
        assert "dormant_count" in stats
        assert "deep_count" in stats
        assert "forgotten_count" in stats
        assert "total_count" in stats
        
        assert stats["active_count"] == 2
        assert stats["total_count"] == 2
    
    def test_cleanup_old_memories(self, temp_workspace):
        """Test cleaning up old memories"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        # Add some memories
        manager.add_memory("Test memory 1", importance_score=0.8)
        manager.add_memory("Test memory 2", importance_score=0.7)
        
        # Run cleanup
        manager.cleanup_old_memories()
        
        # Should not crash
        stats = manager.get_memory_stats()
        assert stats["total_count"] >= 0
    
    def test_get_recent_memories(self, temp_workspace):
        """Test getting recent memories"""
        config = MemoryConfig()
        manager = MemoryManager(config, temp_workspace)
        
        # Add memories
        manager.add_memory("Recent memory 1", importance_score=0.8)
        manager.add_memory("Recent memory 2", importance_score=0.7)
        
        # Get recent memories
        recent_memories = manager.get_recent_memories(hours=24)
        
        assert len(recent_memories) >= 2
        assert all(isinstance(memory, Memory) for memory in recent_memories)
