"""Memory retrieval system for SafeClaw"""

import re
from typing import List, Dict, Any, Optional  # noqa: F401 — Dict used in hybrid_search
from datetime import datetime, timedelta
import logging

from safe_claw.models.memory import Memory, MemorySearchResult
from safe_claw.models.config import MemoryConfig


# Question prefixes stripped before token matching (CJK + EN)
_QUESTION_PREFIXES = (
    "什么是",
    "什么叫",
    "谁是",
    "介绍一下",
    "请介绍",
    "告诉我",
    "解释一下",
    "解释下",
    "啥是",
    "啥叫",
    "what is",
    "what's",
    "who is",
    "define",
    "explain",
)

_INVENTORY_PATTERNS = (
    re.compile(r"(你)?(还)?知道哪些黑话"),
    re.compile(r"(有)?哪些黑话"),
    re.compile(r"黑话(词典|列表|清单)?"),
    re.compile(r"(你)?(有)?哪些记忆"),
    re.compile(r"(列出|列举|说说).*(记忆|黑话|jargon)"),
    re.compile(r"\bjargon\b", re.I),
    re.compile(r"what (memories|jargon).*(do you|have)", re.I),
)


class MemoryRetriever:
    """Memory retrieval and search system"""

    def __init__(self, config: MemoryConfig):
        """Initialize retriever

        Args:
            config: Memory configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def is_inventory_query(self, query: str) -> bool:
        """True for meta questions that should list jargon/memories."""
        q = (query or "").strip()
        if not q:
            return False
        return any(p.search(q) for p in _INVENTORY_PATTERNS)

    def normalize_query(self, query: str) -> str:
        """Lowercase + strip common question prefixes."""
        q = (query or "").strip().lower()
        changed = True
        while changed and q:
            changed = False
            for prefix in _QUESTION_PREFIXES:
                if q.startswith(prefix):
                    q = q[len(prefix) :].lstrip(" ：:？?、,，")
                    changed = True
        return q.strip()

    def tokenize_query(self, query: str) -> List[str]:
        """Extract searchable tokens: latin/digits runs + CJK runs + whitespace words."""
        normalized = self.normalize_query(query)
        if not normalized:
            return []
        tokens: List[str] = []
        # latin / numbers (incl. 101, FAANG, taco)
        tokens.extend(re.findall(r"[a-z0-9][a-z0-9._-]{0,31}", normalized, flags=re.I))
        # CJK contiguous runs (2+ chars) and single meaningful chars later filtered
        for run in re.findall(r"[\u4e00-\u9fff]+", normalized):
            if len(run) >= 2:
                tokens.append(run)
                # also emit bigrams for longer runs
                if len(run) >= 4:
                    for i in range(len(run) - 1):
                        tokens.append(run[i : i + 2])
            elif len(run) == 1:
                tokens.append(run)
        # whitespace-split leftovers
        for part in normalized.split():
            if part and part not in tokens:
                tokens.append(part)
        # de-dupe preserve order; drop ultra-short noise except digits
        seen = set()
        out: List[str] = []
        for t in tokens:
            t = t.strip()
            if not t or t in seen:
                continue
            if len(t) == 1 and not t.isdigit() and t not in "新旧钱":
                continue
            seen.add(t)
            out.append(t)
        return out

    def keyword_search(self, memories: List[Memory], query: str,
                      max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories by keywords (CJK/latin/digit aware)."""
        results = []
        query_lower = (query or "").strip().lower()
        normalized = self.normalize_query(query)
        tokens = self.tokenize_query(query)

        for memory in memories:
            score = 0.0

            content_lower = memory.content.lower()
            if query_lower and query_lower in content_lower:
                score += 1.0
            if normalized and normalized != query_lower and normalized in content_lower:
                score += 1.0

            for keyword in memory.keywords:
                kw = keyword.lower()
                if query_lower and query_lower in kw:
                    score += 0.5
                for token in tokens:
                    if token in kw:
                        score += 0.35

            for token in tokens:
                if token and token in content_lower:
                    # Prefer longer token hits
                    score += 0.3 + min(0.4, len(token) * 0.05)

            if score > 0:
                score *= (1 + memory.importance_score)
                score *= (1 + memory.access_count * 0.1)

                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    match_type="keyword"
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
    
    def semantic_search(
        self,
        memories: List[Memory],
        query: str,
        max_results: int = 10,
        vector_index=None,
    ) -> List[MemorySearchResult]:
        """Search memories by semantic similarity (requires vector index)."""
        if not self.config.enable_vector_search:
            return []

        if vector_index is None:
            raise ValueError(
                "[MemoryRetriever] enable_vector_search=True but vector_index is None\n"
                "  Expected: VectorIndex instance from MemoryManager"
            )

        id_to_memory = {m.id: m for m in memories}
        hits = vector_index.search(query, memory_ids=list(id_to_memory.keys()), top_k=max_results)
        results: List[MemorySearchResult] = []
        for memory_id, score in hits:
            memory = id_to_memory.get(memory_id)
            if not memory:
                continue
            results.append(
                MemorySearchResult(
                    memory=memory,
                    score=score * (1 + memory.importance_score),
                    match_type="semantic",
                )
            )
        return results
    
    def context_search(self, memories: List[Memory], context: Dict[str, Any],
                      max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories based on context
        
        Args:
            memories: List of memories to search
            context: Search context (time range, importance, etc.)
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        results = []
        
        for memory in memories:
            score = 0.0
            
            # Time-based filtering
            if "time_range" in context:
                time_range = context["time_range"]
                now = datetime.now()
                
                if "hours" in time_range:
                    cutoff = now - timedelta(hours=time_range["hours"])
                    if memory.accessed_at >= cutoff:
                        score += 1.0
                
                if "days" in time_range:
                    cutoff = now - timedelta(days=time_range["days"])
                    if memory.accessed_at >= cutoff:
                        score += 0.8
            
            # Importance filtering
            if "min_importance" in context:
                if memory.importance_score >= context["min_importance"]:
                    score += memory.importance_score
            
            # Keyword filtering
            if "keywords" in context:
                for keyword in context["keywords"]:
                    if keyword.lower() in [k.lower() for k in memory.keywords]:
                        score += 0.5
            
            # Layer filtering
            if "layers" in context:
                if memory.layer.value in context["layers"]:
                    score += 0.3
            
            if score > 0:
                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    match_type="context"
                ))
        
        # Sort by score and limit results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
    
    def hybrid_search(
        self,
        memories: List[Memory],
        query: str,
        max_results: int = 10,
        vector_index=None,
    ) -> List[MemorySearchResult]:
        """Hybrid search: keyword always; semantic when vector search enabled."""
        keyword_results = self.keyword_search(memories, query, max_results * 2)
        semantic_results: List[MemorySearchResult] = []
        if self.config.enable_vector_search:
            semantic_results = self.semantic_search(
                memories, query, max_results * 2, vector_index=vector_index
            )

        if not semantic_results:
            return keyword_results[:max_results]

        combined_results: Dict[str, MemorySearchResult] = {}

        for result in keyword_results:
            memory_id = result.memory.id
            combined_results[memory_id] = result

        for result in semantic_results:
            memory_id = result.memory.id
            if memory_id not in combined_results:
                combined_results[memory_id] = result
            else:
                combined_results[memory_id].score += result.score * 0.4
                combined_results[memory_id].match_type = "hybrid"

        for result in combined_results.values():
            if result.match_type == "keyword" and semantic_results:
                # keep keyword label unless fused
                pass
            elif result.match_type == "semantic":
                pass
            else:
                result.match_type = "hybrid"

        results = list(combined_results.values())
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
    
    def fuzzy_search(self, memories: List[Memory], query: str,
                    max_results: int = 10, fuzzy_threshold: float = 0.6) -> List[MemorySearchResult]:
        """Fuzzy search for approximate matches
        
        Args:
            memories: List of memories to search
            query: Search query
            max_results: Maximum number of results
            fuzzy_threshold: Minimum similarity threshold
            
        Returns:
            List of memory search results
        """
        results = []
        query_lower = query.lower()
        
        for memory in memories:
            content_lower = memory.content.lower()
            
            # Simple fuzzy matching using character n-grams
            similarity = self._calculate_similarity(query_lower, content_lower)
            
            if similarity >= fuzzy_threshold:
                score = similarity * (1 + memory.importance_score)
                
                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    match_type="fuzzy"
                ))
        
        # Sort by score and limit results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple character matching
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        common_chars = set(str1) & set(str2)
        total_chars = set(str1) | set(str2)
        
        if not total_chars:
            return 0.0
        
        return len(common_chars) / len(total_chars)
    
    def get_related_memories(self, memories: List[Memory], target_memory: Memory,
                           max_results: int = 5) -> List[MemorySearchResult]:
        """Find memories related to a target memory
        
        Args:
            memories: List of memories to search
            target_memory: Target memory to find relations for
            max_results: Maximum number of results
            
        Returns:
            List of related memory search results
        """
        results = []
        
        for memory in memories:
            if memory.id == target_memory.id:
                continue
            
            score = 0.0
            
            # Keyword overlap
            target_keywords = set(k.lower() for k in target_memory.keywords)
            memory_keywords = set(k.lower() for k in memory.keywords)
            keyword_overlap = len(target_keywords & memory_keywords)
            
            if keyword_overlap > 0:
                score += keyword_overlap * 0.5
            
            # Content similarity
            content_similarity = self._calculate_similarity(
                target_memory.content.lower(), 
                memory.content.lower()
            )
            score += content_similarity * 0.3
            
            # Same layer bonus
            if memory.layer == target_memory.layer:
                score += 0.2
            
            if score > 0:
                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    match_type="related"
                ))
        
        # Sort by score and limit results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
