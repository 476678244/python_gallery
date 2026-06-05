"""Memory retrieval system for SafeClaw"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from safe_claw.models.memory import Memory, MemorySearchResult
from safe_claw.models.config import MemoryConfig


class MemoryRetriever:
    """Memory retrieval and search system"""
    
    def __init__(self, config: MemoryConfig):
        """Initialize retriever
        
        Args:
            config: Memory configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def keyword_search(self, memories: List[Memory], query: str, 
                      max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories by keywords
        
        Args:
            memories: List of memories to search
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        results = []
        query_lower = query.lower()
        
        for memory in memories:
            score = 0.0
            
            # Check content match
            content_lower = memory.content.lower()
            if query_lower in content_lower:
                score += 1.0
            
            # Check keyword matches
            for keyword in memory.keywords:
                if query_lower in keyword.lower():
                    score += 0.5
            
            # Check partial word matches
            words = query_lower.split()
            for word in words:
                if word in content_lower:
                    score += 0.3
            
            if score > 0:
                # Boost by importance score
                score *= (1 + memory.importance_score)
                
                # Boost by access frequency
                score *= (1 + memory.access_count * 0.1)
                
                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    match_type="keyword"
                ))
        
        # Sort by score and limit results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
    
    def semantic_search(self, memories: List[Memory], query: str,
                       max_results: int = 10) -> List[MemorySearchResult]:
        """Search memories by semantic similarity
        
        Args:
            memories: List of memories to search
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        # Fallback to keyword search if vector search is not enabled
        if not self.config.enable_vector_search:
            return self.keyword_search(memories, query, max_results)
        
        # TODO: Implement actual semantic search with embeddings
        # For now, fallback to keyword search
        results = self.keyword_search(memories, query, max_results)
        
        # Update match type to semantic for consistency
        for result in results:
            result.match_type = "semantic"
        
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
    
    def hybrid_search(self, memories: List[Memory], query: str,
                     max_results: int = 10) -> List[MemorySearchResult]:
        """Hybrid search combining multiple methods
        
        Args:
            memories: List of memories to search
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of memory search results
        """
        # Get results from different search methods
        keyword_results = self.keyword_search(memories, query, max_results * 2)
        semantic_results = self.semantic_search(memories, query, max_results * 2)
        
        # Combine and deduplicate results
        combined_results = {}
        
        # Add keyword results
        for result in keyword_results:
            memory_id = result.memory.id
            if memory_id not in combined_results:
                combined_results[memory_id] = result
            else:
                # Combine scores
                combined_results[memory_id].score += result.score * 0.6
        
        # Add semantic results
        for result in semantic_results:
            memory_id = result.memory.id
            if memory_id not in combined_results:
                combined_results[memory_id] = result
            else:
                # Combine scores
                combined_results[memory_id].score += result.score * 0.4
        
        # Update match type to hybrid
        for result in combined_results.values():
            result.match_type = "hybrid"
        
        # Sort by score and limit results
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
