"""Unit tests: memory lifecycle, write policy, vector hybrid search."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from safe_claw.core.memory.manager import MemoryManager, assess_conversation_importance
from safe_claw.core.memory.embeddings import embed_text, cosine_similarity
from safe_claw.models.config import MemoryConfig
from safe_claw.models.memory import MemoryLayer


@pytest.fixture()
def mm(tmp_path: Path) -> MemoryManager:
    return MemoryManager(
        config=MemoryConfig(
            max_active_memories=3,
            auto_write_min_importance=0.6,
            dormant_to_deep_days=7,
            enable_vector_search=True,
        ),
        workspace_path=str(tmp_path),
    )


def test_active_overflow_moves_to_dormant(mm: MemoryManager):
    for i in range(4):
        mm.add_memory(content=f"fact-{i} unique content", importance_score=0.1 * (i + 1))
    stats = mm.get_memory_stats()
    assert stats["active_count"] <= 3
    assert stats["dormant_count"] >= 1


def test_maybe_store_skips_low_importance(mm: MemoryManager):
    assert assess_conversation_importance("hi", "hello") < 0.6
    mid = mm.maybe_store_conversation("hi there friend", "hello back to you")
    assert mid is None
    assert mm.get_memory_stats()["total_count"] == 0


def test_maybe_store_writes_high_importance(mm: MemoryManager):
    mid = mm.maybe_store_conversation(
        "Please remember my preference for dark mode",
        "Got it, I'll remember your preference.",
    )
    assert mid is not None
    assert mm.get_memory_stats()["active_count"] == 1


def test_promote_dormant_to_deep(mm: MemoryManager):
    mid = mm.add_memory(content="old dormant fact xyz", importance_score=0.2)
    assert mm._move_memory_between_layers(mid, MemoryLayer.ACTIVE, MemoryLayer.DORMANT)
    mem = mm.dormant_layer.get_memory(mid)
    assert mem is not None
    mem.accessed_at = datetime.now() - timedelta(days=30)
    mem.importance_score = 0.1
    mm.storage.save_memory(mem)

    promoted = mm.promote_dormant_to_deep()
    assert promoted >= 1
    assert mm.get_memory_stats()["deep_count"] >= 1


def test_consolidate_near_duplicates(mm: MemoryManager):
    mm.add_memory(content="User likes green tea every morning", importance_score=0.7)
    mm.add_memory(content="User likes green tea every morning", importance_score=0.8)
    merged = mm.consolidate_memories()
    assert merged >= 1
    assert mm.get_memory_stats()["active_count"] == 1


def test_vector_search_hits_related_tokens(mm: MemoryManager):
    mm.add_memory(
        content="The capital of France is Paris and the river is Seine",
        importance_score=0.9,
        keywords=["france", "paris"],
    )
    # Keyword-light query still shares embedding tokens with stored text
    hits = mm.search_memories("Seine river France", max_results=5)
    assert len(hits) >= 1
    assert any(h.match_type in ("semantic", "hybrid", "keyword") for h in hits)


def test_embed_cosine_sanity():
    a = embed_text("red sports car")
    b = embed_text("red sports car")
    c = embed_text("completely unrelated quantum topic")
    assert cosine_similarity(a, b) > 0.99
    assert cosine_similarity(a, c) < cosine_similarity(a, b)


def test_config_accepts_active_memory_max_alias():
    cfg = MemoryConfig(active_memory_max=15)  # type: ignore[call-arg]
    assert cfg.max_active_memories == 15
    assert cfg.active_memory_max == 15


def test_chinese_question_finds_jargon_token(tmp_path: Path):
    mm = MemoryManager(
        config=MemoryConfig(enable_vector_search=False),
        workspace_path=str(tmp_path),
    )
    mm.add_memory(
        content="[Investment Jargon Wiki] 101（散户 / 边际接盘流动性）\n散户提供的边际接盘",
        importance_score=0.92,
        keywords=["101", "散户", "jargon", "黑话"],
        metadata={"collection": "jargon"},
    )
    hits = mm.search_memories("什么是101", max_results=5)
    assert len(hits) >= 1
    assert "101" in hits[0].memory.content or "散户" in hits[0].memory.content


def test_format_memory_context_has_guardrails():
    from safe_claw.core.memory.manager import format_memory_context
    from safe_claw.models.memory import Memory, MemoryLayer, MemorySearchResult

    mem = Memory(
        content="101 指散户边际接盘",
        layer=MemoryLayer.ACTIVE,
        importance_score=0.9,
    )
    text = format_memory_context(
        [MemorySearchResult(memory=mem, score=1.0, match_type="keyword")]
    )
    assert "AUTHORITATIVE" in text or "mandatory" in text.lower()
    assert "101" in text
    assert "textbook" in text.lower() or "encyclopedia" in text.lower() or "导论" in text or "generic" in text.lower()


def test_rebuild_vector_index(tmp_path: Path):
    mm = MemoryManager(
        config=MemoryConfig(enable_vector_search=True),
        workspace_path=str(tmp_path),
    )
    mm.add_memory(content="vector rebuild sample alpha", importance_score=0.8)
    n = mm.rebuild_vector_index()
    assert n >= 1


def test_inventory_query_lists_jargon(tmp_path: Path):
    mm = MemoryManager(
        config=MemoryConfig(enable_vector_search=False),
        workspace_path=str(tmp_path),
    )
    mm.add_memory(
        content="[Investment Jargon Wiki] 黑话词典 index.md",
        importance_score=0.95,
        keywords=["黑话", "jargon"],
        metadata={"collection": "jargon"},
    )
    assert mm.retriever.is_inventory_query("你知道哪些黑话")
    hits = mm.search_memories("你知道哪些黑话", max_results=5)
    assert len(hits) >= 1
    assert hits[0].match_type == "inventory"
