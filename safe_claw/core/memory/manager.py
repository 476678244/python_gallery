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
from safe_claw.core.memory.embeddings import VectorIndex


VALID_LAYERS = {layer.value for layer in MemoryLayer}


def serialize_memory(memory: Memory) -> Dict[str, Any]:
    """API/UI DTO for a Memory."""
    layer = memory.layer.value if isinstance(memory.layer, MemoryLayer) else str(memory.layer)
    created = memory.created_at
    return {
        "id": memory.id,
        "content": memory.content,
        "layer": layer,
        "importance": memory.importance_score,
        "created_at": created.isoformat() if isinstance(created, datetime) else str(created),
        "access_count": memory.access_count,
        "tags": list(memory.keywords or []),
    }


def format_memory_context(
    search_results: List[MemorySearchResult], top_k: int = 5, max_chars: int = 700
) -> str:
    """Build prompt context from search hits (must be merged into agent system prompt)."""
    if not search_results:
        return ""
    lines = [
        "### AUTHORITATIVE USER MEMORY (mandatory)",
        "The blocks below are the user's stored long-term memories (including investment jargon).",
        "Rules when answering:",
        "1. If the user asks what a term/jargon means and it appears below, answer from THAT text first.",
        "2. Do NOT substitute a generic encyclopedia / textbook / university-course meaning "
        "(e.g. 'Economics 101', 'Route 101') when a domain definition is present.",
        "3. You may briefly note other meanings only AFTER the memory definition.",
        "4. When listing jargon/memories, enumerate items found below.",
        "",
        "Relevant memories:",
    ]
    for result in search_results[:top_k]:
        content = (result.memory.content or "").strip().replace("\n", " ")
        if len(content) > max_chars:
            content = content[: max_chars - 3] + "..."
        lines.append(f"- {content}")
    return "\n".join(lines)


def assess_conversation_importance(user_input: str, response: str) -> float:
    """Heuristic importance for a chat turn."""
    text = (user_input + " " + response).lower()
    if any(word in text for word in ["important", "critical", "remember", "preference", "my name"]):
        return 0.8
    if any(word in text for word in ["question", "how to", "what is", "help with"]):
        return 0.6
    return 0.4


class MemoryManager:
    """Main memory manager for SafeClaw"""

    def __init__(self, config: MemoryConfig, workspace_path: str):
        self.config = config
        self.workspace_path = Path(workspace_path)
        self.storage_path = self.workspace_path / "memory"

        self.storage = FileStorage(self.storage_path)
        self.retriever = MemoryRetriever(config)
        self.vector_index = VectorIndex(self.storage_path)

        self.active_layer = ActiveMemoryLayer(config, self.storage)
        self.dormant_layer = DormantMemoryLayer(config, self.storage)
        self.deep_layer = DeepMemoryLayer(config, self.storage)
        self.forgotten_layer = ForgottenMemoryLayer(config, self.storage)

        self.logger = logging.getLogger(__name__)

    def add_memory(
        self,
        content: str,
        importance_score: float = 0.5,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        memory = Memory(
            content=content,
            layer=MemoryLayer.ACTIVE,
            importance_score=importance_score,
            keywords=keywords or [],
            metadata=metadata or {},
        )

        memory_id = self.active_layer.add_memory(memory)
        if self.config.enable_vector_search:
            self.vector_index.upsert(memory_id, content)

        if self.active_layer.count() > self.config.max_active_memories:
            least_important = self.active_layer.get_least_important()
            if least_important:
                self._move_memory_between_layers(
                    least_important.id,
                    MemoryLayer.ACTIVE,
                    MemoryLayer.DORMANT,
                )

        return memory_id

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        for layer in [
            self.active_layer,
            self.dormant_layer,
            self.deep_layer,
            self.forgotten_layer,
        ]:
            memory = layer.get_memory(memory_id)
            if memory:
                memory.accessed_at = datetime.now()
                memory.access_count += 1
                self.storage.save_memory(memory)
                return memory
        return None

    def get_memories_by_layer(self, layer: str, limit: int = 20) -> List[Memory]:
        """List memories in a layer (newest access first)."""
        if layer not in VALID_LAYERS:
            raise ValueError(
                f"[MemoryManager] Invalid memory layer\n"
                f"  layer: {layer!r}\n"
                f"  Expected: {sorted(VALID_LAYERS)}"
            )
        layer_enum = MemoryLayer(layer)
        instance = self._get_layer_instance(layer_enum)
        if instance is None:
            raise ValueError(
                f"[MemoryManager] Layer instance missing\n"
                f"  layer: {layer!r}"
            )
        memories = instance.get_all_memories()
        memories.sort(key=lambda m: m.accessed_at, reverse=True)
        return memories[: max(0, limit)]

    def rebuild_vector_index(self) -> int:
        """Re-embed all memories into vectors.sqlite. Returns count indexed."""
        count = 0
        for layer in [
            self.active_layer,
            self.dormant_layer,
            self.deep_layer,
            self.forgotten_layer,
        ]:
            for memory in layer.get_all_memories():
                self.vector_index.upsert(memory.id, memory.content or "")
                count += 1
        self.logger.info("[MemoryManager] Rebuilt vector index: %s entries", count)
        return count

    def search_memories(self, query: str, max_results: int = 10) -> List[MemorySearchResult]:
        all_memories = []
        for layer in [
            self.active_layer,
            self.dormant_layer,
            self.deep_layer,
            self.forgotten_layer,
        ]:
            all_memories.extend(layer.get_all_memories())

        # Meta questions ("你有哪些记忆/黑话") → surface high-value glossary notes
        if self.retriever.is_inventory_query(query):
            jargon = [
                m
                for m in all_memories
                if (m.metadata or {}).get("collection") == "jargon"
                or "jargon" in (m.content or "").lower()
                or "黑话" in (m.content or "")
            ]
            jargon.sort(key=lambda m: m.importance_score, reverse=True)
            # Prefer index + diverse entries
            index_first = [m for m in jargon if "index.md" in (m.content or "")]
            rest = [m for m in jargon if m not in index_first]
            picked = (index_first + rest)[:max_results]
            if picked:
                return [
                    MemorySearchResult(memory=m, score=1.0 + m.importance_score, match_type="inventory")
                    for m in picked
                ]

        results = self.retriever.hybrid_search(
            all_memories, query, max_results, vector_index=self.vector_index
        )

        # Wake high-scoring dormant memories into active
        threshold = self.config.dormant_wakeup_threshold
        for result in results:
            mem = result.memory
            layer_val = mem.layer.value if isinstance(mem.layer, MemoryLayer) else mem.layer
            if layer_val == MemoryLayer.DORMANT.value and result.score >= threshold:
                self._move_memory_between_layers(
                    mem.id, MemoryLayer.DORMANT, MemoryLayer.ACTIVE
                )
                mem.layer = MemoryLayer.ACTIVE

        return results

    def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        memory.importance_score = new_importance
        self.storage.save_memory(memory)
        return True

    def get_memory_stats(self) -> Dict[str, Any]:
        return {
            "active_count": self.active_layer.count(),
            "dormant_count": self.dormant_layer.count(),
            "deep_count": self.deep_layer.count(),
            "forgotten_count": self.forgotten_layer.count(),
            "total_count": (
                self.active_layer.count()
                + self.dormant_layer.count()
                + self.deep_layer.count()
                + self.forgotten_layer.count()
            ),
        }

    def cleanup_old_memories(self) -> Dict[str, int]:
        """Age-based forgotten move + dormant→deep promotion."""
        cutoff_time = datetime.now() - timedelta(days=self.config.memory_retention_days)
        forgotten = 0
        for layer in [self.active_layer, self.dormant_layer, self.deep_layer]:
            for memory in list(layer.get_all_memories()):
                if memory.created_at < cutoff_time:
                    if self._move_memory_between_layers(
                        memory.id, memory.layer, MemoryLayer.FORGOTTEN
                    ):
                        forgotten += 1

        promoted = self.promote_dormant_to_deep()
        consolidated = self.consolidate_memories()
        return {
            "forgotten": forgotten,
            "promoted_to_deep": promoted,
            "consolidated": consolidated,
        }

    def promote_dormant_to_deep(self) -> int:
        """Move stale/low-importance dormant memories to deep."""
        cutoff = datetime.now() - timedelta(days=self.config.dormant_to_deep_days)
        promoted = 0
        for memory in list(self.dormant_layer.get_all_memories()):
            stale = memory.accessed_at < cutoff
            low = memory.importance_score < self.config.dormant_wakeup_threshold
            if stale and low:
                if self._move_memory_between_layers(
                    memory.id, MemoryLayer.DORMANT, MemoryLayer.DEEP
                ):
                    promoted += 1
        return promoted

    def consolidate_memories(self) -> int:
        """Merge near-duplicate active memories (minimal usable consolidation)."""
        memories = self.active_layer.get_all_memories()
        if len(memories) < 2:
            return 0

        merged = 0
        removed_ids = set()
        memories_sorted = sorted(memories, key=lambda m: m.importance_score, reverse=True)

        for i, keep in enumerate(memories_sorted):
            if keep.id in removed_ids:
                continue
            for other in memories_sorted[i + 1 :]:
                if other.id in removed_ids:
                    continue
                sim = self.retriever._calculate_similarity(
                    keep.content.lower(), other.content.lower()
                )
                if sim >= 0.85:
                    # Merge keywords into keeper
                    keep.keywords = sorted(
                        set(keep.keywords or []) | set(other.keywords or [])
                    )
                    keep.importance_score = max(
                        keep.importance_score, other.importance_score
                    )
                    keep.access_count += other.access_count
                    self.storage.save_memory(keep)
                    if self.config.enable_vector_search:
                        self.vector_index.upsert(keep.id, keep.content)
                    self.active_layer.remove_memory(other.id)
                    if self.config.enable_vector_search:
                        self.vector_index.delete(other.id)
                    removed_ids.add(other.id)
                    merged += 1
        return merged

    def maybe_store_conversation(
        self,
        user_input: str,
        response: str,
        session_id: Optional[str] = None,
        force: bool = False,
    ) -> Optional[str]:
        """Store a chat turn when importance passes threshold (or force)."""
        if not user_input or not response:
            return None
        if len(user_input) <= 10 and not force:
            return None
        importance = assess_conversation_importance(user_input, response)
        if not force and importance < self.config.auto_write_min_importance:
            self.logger.info(
                "[MemoryManager] Skip auto-write (importance %.2f < %.2f)",
                importance,
                self.config.auto_write_min_importance,
            )
            return None
        conversation = f"User: {user_input}\nAssistant: {response}"
        return self.add_memory(
            content=conversation[:2000],
            importance_score=importance,
            metadata={"type": "conversation", "session_id": session_id},
        )

    def get_recent_memories(self, hours: int = 24) -> List[Memory]:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_memories = []
        for layer in [self.active_layer, self.dormant_layer, self.deep_layer]:
            memories = layer.get_all_memories()
            recent_memories.extend(
                [memory for memory in memories if memory.accessed_at >= cutoff_time]
            )
        recent_memories.sort(key=lambda m: m.accessed_at, reverse=True)
        return recent_memories

    def _normalize_layer(self, layer: MemoryLayer | str) -> MemoryLayer:
        if isinstance(layer, MemoryLayer):
            return layer
        try:
            return MemoryLayer(layer)
        except ValueError as e:
            raise ValueError(
                f"[MemoryManager] Invalid layer value\n"
                f"  layer: {layer!r}\n"
                f"  Expected: {sorted(VALID_LAYERS)}"
            ) from e

    def _move_memory_between_layers(
        self,
        memory_id: str,
        from_layer: MemoryLayer | str,
        to_layer: MemoryLayer | str,
    ) -> bool:
        try:
            from_layer = self._normalize_layer(from_layer)
            to_layer = self._normalize_layer(to_layer)
            source_layer = self._get_layer_instance(from_layer)
            target_layer = self._get_layer_instance(to_layer)
            if source_layer is None or target_layer is None:
                raise ValueError(
                    f"[MemoryManager] Invalid layer move\n"
                    f"  from: {from_layer}\n"
                    f"  to: {to_layer}"
                )

            memory = source_layer.get_memory(memory_id)
            if not memory:
                return False

            source_layer.remove_memory(memory_id)
            memory.layer = to_layer
            target_layer.add_memory(memory)
            return True
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error moving memory {memory_id}: {e}")
            return False

    def _get_layer_instance(self, layer: MemoryLayer):
        layer_map = {
            MemoryLayer.ACTIVE: self.active_layer,
            MemoryLayer.DORMANT: self.dormant_layer,
            MemoryLayer.DEEP: self.deep_layer,
            MemoryLayer.FORGOTTEN: self.forgotten_layer,
        }
        return layer_map.get(layer)
