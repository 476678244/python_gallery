"""Semantic Matcher for Skills - BM25 + Keyword-based matching

Stage 2: Semantic matching on Level 1 metadata only
- TF-IDF / BM25 for text similarity
- Keyword expansion for recall
- Works with SkillIndexEntry (L1 data)
"""

import re
import math
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import Counter
from dataclasses import dataclass

from streamlit_ui.safe_claw.core.skills.scanner import SkillIndexEntry

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Skill match result with score"""
    skill: SkillIndexEntry
    score: float
    matched_terms: List[str]


class BM25:
    """BM25 ranking function implementation"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[str] = []
        self.idf: Dict[str, float] = {}
        self.avg_doc_len = 0

    def fit(self, documents: List[str]):
        """Fit BM25 on document corpus"""
        self.documents = documents

        # Calculate document lengths
        doc_lengths = [len(doc.split()) for doc in documents]
        self.avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1

        # Calculate IDF for each term
        doc_count = len(documents)
        term_doc_count: Dict[str, int] = Counter()

        for doc in documents:
            words = set(doc.lower().split())
            for word in words:
                term_doc_count[word] += 1

        for term, count in term_doc_count.items():
            # IDF formula
            self.idf[term] = math.log((doc_count - count + 0.5) / (count + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for a query against a document"""
        query_terms = query.lower().split()
        doc = self.documents[doc_idx]
        doc_terms = doc.lower().split()
        doc_len = len(doc_terms)

        score = 0.0
        for term in query_terms:
            if term not in self.idf:
                continue

            # Term frequency in document
            tf = doc_terms.count(term)

            # BM25 formula
            numerator = self.idf[term] * tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            score += numerator / denominator

        return score


class KeywordExpander:
    """Expand keywords with common synonyms and variations"""

    EXPANSIONS = {
        # Data operations
        "csv": ["csv", "spreadsheet", "excel", "table", "data file"],
        "json": ["json", "data", "structured data"],
        "sql": ["sql", "database", "query", "db", "select"],

        # Web operations
        "url": ["url", "link", "web", "http", "website"],
        "crawl": ["crawl", "scrape", "fetch", "download", "get"],
        "api": ["api", "endpoint", "rest", "http", "request"],

        # File operations
        "read": ["read", "open", "load", "get", "fetch"],
        "write": ["write", "save", "create", "store"],
        "file": ["file", "document", "path", "filesystem"],

        # Code operations
        "analyze": ["analyze", "parse", "check", "lint", "review"],
        "format": ["format", "beautify", "prettify", "clean"],

        # Content
        "parse": ["parse", "extract", "convert", "transform"],
        "summarize": ["summarize", "summary", "tldr", "brief"],
    }

    @classmethod
    def expand(cls, query: str) -> List[str]:
        """Expand query with related terms"""
        words = query.lower().split()
        expanded = set(words)

        for word in words:
            for key, variations in cls.EXPANSIONS.items():
                if word in variations or word == key:
                    expanded.update(variations)

        return list(expanded)


class SemanticMatcher:
    """Semantic skill matcher using BM25 + keyword expansion
    
    Works with Level 1 metadata (SkillIndexEntry) for efficient matching
    without loading full SKILL.md content.
    """

    def __init__(self):
        self.bm25: Optional[BM25] = None
        self.skills: List[SkillIndexEntry] = []
        self.documents: List[str] = []
        self.fitted = False

    def _create_document(self, skill: SkillIndexEntry) -> str:
        """Create searchable document from skill metadata (L1 only)"""
        parts = [
            skill.name,
            skill.description,
            " ".join(skill.tags),
            " ".join(skill.aliases),
            skill.category,
        ]
        return " ".join(parts).lower()

    def fit_l1(self, skills: List[SkillIndexEntry]):
        """Fit matcher on Level 1 skill corpus"""
        self.skills = skills
        self.documents = [self._create_document(s) for s in skills]

        self.bm25 = BM25()
        self.bm25.fit(self.documents)
        self.fitted = True

        logger.info(f"SemanticMatcher fitted on {len(skills)} skills (L1)")

    def find_skills_l1(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
        use_expansion: bool = True
    ) -> List[MatchResult]:
        """Find matching skills for a query using L1 metadata"""
        if not self.fitted or not self.skills:
            return []

        # Expand query
        if use_expansion:
            expanded = KeywordExpander.expand(query)
            search_query = " ".join(expanded)
        else:
            search_query = query

        # Score all documents
        scores: List[Tuple[int, float]] = []
        for i in range(len(self.documents)):
            score = self.bm25.score(search_query, i)
            if score >= min_score:
                scores.append((i, score))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Create results
        results = []
        for idx, score in scores[:top_k]:
            skill = self.skills[idx]

            # Find matched terms
            query_terms = set(search_query.lower().split())
            doc_terms = set(self.documents[idx].split())
            matched = list(query_terms & doc_terms)

            results.append(MatchResult(
                skill=skill,
                score=score,
                matched_terms=matched
            ))

        return results

    def simple_match_l1(
        self,
        query: str,
        skills: List[SkillIndexEntry],
        top_k: int = 5
    ) -> List[MatchResult]:
        """Simple keyword overlap matching on L1 metadata (no BM25 fitting required)"""
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w+\b', query_lower))

        results = []
        for skill in skills:
            # Create document
            doc = self._create_document(skill)
            doc_terms = set(re.findall(r'\b\w+\b', doc))

            # Calculate overlap
            overlap = query_terms & doc_terms
            if not overlap:
                continue

            # Score based on overlap ratio
            score = len(overlap) / len(query_terms) if query_terms else 0

            # Boost exact name match
            if skill.name.lower() in query_lower:
                score += 2.0

            # Boost alias match
            for alias in skill.aliases:
                if alias.lower() in query_lower:
                    score += 1.5

            results.append(MatchResult(
                skill=skill,
                score=score,
                matched_terms=list(overlap)
            ))

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    # Legacy compatibility methods
    def fit(self, skills: List[SkillIndexEntry]):
        """Legacy method - delegates to fit_l1"""
        return self.fit_l1(skills)

    def find_skills(self, query: str, top_k: int = 5, min_score: float = 0.1,
                   use_expansion: bool = True) -> List[MatchResult]:
        """Legacy method - delegates to find_skills_l1"""
        return self.find_skills_l1(query, top_k, min_score, use_expansion)

    def simple_match(self, query: str, skills: List[SkillIndexEntry], top_k: int = 5) -> List[MatchResult]:
        """Legacy method - delegates to simple_match_l1"""
        return self.simple_match_l1(query, skills, top_k)


# Singleton instance
_matcher_instance: Optional[SemanticMatcher] = None


def get_semantic_matcher() -> SemanticMatcher:
    """Get singleton semantic matcher instance"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = SemanticMatcher()
    return _matcher_instance
