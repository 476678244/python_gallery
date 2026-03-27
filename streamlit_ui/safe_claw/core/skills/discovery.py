"""Progressive Skill Discovery - Lazy + Semantic + Failure-driven

Main entry point for skill discovery:
1. Hot cache (loaded skills)
2. Path-guided scan (lazy)
3. Semantic matching
4. Failure-driven expansion
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from safe_claw.core.skills.scanner import SkillScanner, SkillMetadata, get_skill_scanner
from safe_claw.core.skills.matcher import SemanticMatcher, MatchResult, get_semantic_matcher
from safe_claw.core.skills.base_skill import BaseSkill
from safe_claw.core.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


class DiscoveryLevel(Enum):
    """Discovery expansion levels"""
    HOT_CACHE = 0       # Already loaded
    PATH_GUIDED = 1     # Scan inferred directories
    FULL_SCAN = 2       # Scan all skills
    MISSING_SKILL = 3   # Cannot find suitable skill


@dataclass
class DiscoveryResult:
    """Result of skill discovery"""
    skill: Optional[BaseSkill] = None
    metadata: Optional[SkillMetadata] = None
    level: DiscoveryLevel = DiscoveryLevel.MISSING_SKILL
    candidates: List[MatchResult] = None
    missing_skill_hint: Optional[Dict[str, str]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.candidates is None:
            self.candidates = []


class SkillDiscovery:
    """Progressive skill discovery system

    Implements the 4-level discovery strategy:
    - Level 0: Hot cache (loaded skills)
    - Level 1: Path-guided scan (lazy)
    - Level 2: Full scan + semantic match
    - Level 3: Missing skill detection
    """

    def __init__(self, skill_registry: SkillRegistry = None):
        self.registry = skill_registry or SkillRegistry()
        self.scanner = get_skill_scanner()
        self.matcher = get_semantic_matcher()
        self.scanned_paths: set = set()

        # Directory semantics for path-guided scanning
        self.path_hints = {
            "data": ["data", "sql", "csv", "json", "db"],
            "web": ["web", "http", "url", "crawl", "api", "browser"],
            "file": ["file", "read", "write", "directory", "path"],
            "code": ["code", "analyze", "format", "syntax", "lint"],
            "image": ["image", "img", "png", "visual", "graph", "chart"],
            "text": ["text", "nlp", "parse", "extract", "summarize"],
            "finance": ["stock", "portfolio", "13f", "market", "finance"],
        }

    def _load_skill_code(self, metadata: SkillMetadata) -> Optional[BaseSkill]:
        """Lazy load skill code from metadata (Stage 3)"""
        try:
            # Try different skill file patterns
            skill_path = metadata.path

            # Pattern 1: main.py
            main_file = skill_path / "main.py"
            if main_file.exists():
                return self._load_from_python(main_file, metadata)

            # Pattern 2: tool.py
            tool_file = skill_path / "tool.py"
            if tool_file.exists():
                return self._load_from_python(tool_file, metadata)

            # Pattern 3: SKILL.md with embedded python
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                # For now, return a wrapper skill
                return self._create_wrapper_skill(metadata)

            logger.warning(f"No executable found for skill: {metadata.name}")
            return None

        except Exception as e:
            logger.error(f"Failed to load skill code {metadata.name}: {e}")
            return None

    def _load_from_python(self, py_file: Path, metadata: SkillMetadata) -> Optional[BaseSkill]:
        """Load skill from Python file"""
        import importlib.util

        try:
            spec = importlib.util.spec_from_file_location(metadata.name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for SKILL_DEFINITION or skill class
            if hasattr(module, "SKILL_DEFINITION"):
                # Return a wrapper using the definition
                return self._create_wrapper_skill(metadata, module)

            if hasattr(module, "run"):
                return self._create_wrapper_skill(metadata, module)

            return None
        except Exception as e:
            logger.error(f"Failed to import {py_file}: {e}")
            return None

    def _create_wrapper_skill(self, metadata: SkillMetadata, module=None) -> BaseSkill:
        """Create a wrapper skill from metadata"""
        # Create a dynamic skill class
        class DynamicSkill(BaseSkill):
            def __init__(self, meta: SkillMetadata, mod=None):
                self.meta = meta
                self.module = mod
                self._setup_from_metadata()

            def _setup_from_metadata(self):
                self.name = self.meta.name
                self.description = self.meta.description
                self.category = self.meta.category
                self.version = self.meta.version
                self.tags = self.meta.tags

                # Build parameters schema from inputs
                self.parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                for inp in self.meta.inputs:
                    if isinstance(inp, dict):
                        name = inp.get("name", "input")
                        self.parameters["properties"][name] = {
                            "type": inp.get("type", "string"),
                            "description": inp.get("description", "")
                        }
                    else:
                        self.parameters["properties"][str(inp)] = {"type": "string"}

            def can_handle(self, query: str) -> float:
                # Simple keyword matching
                query_lower = query.lower()
                score = 0.0

                # Name match
                if self.name.lower() in query_lower:
                    score += 2.0

                # Description match
                desc_words = self.description.lower().split()
                for word in desc_words[:20]:  # First 20 words
                    if word in query_lower:
                        score += 0.3

                # Tag match
                for tag in self.tags:
                    if tag.lower() in query_lower:
                        score += 0.5

                # Alias match
                for alias in self.meta.aliases:
                    if alias.lower() in query_lower:
                        score += 1.0

                return min(score, 1.0)

            def execute(self, **kwargs) -> Dict[str, Any]:
                if self.module and hasattr(self.module, "run"):
                    try:
                        result = self.module.run(**kwargs)
                        return {"success": True, "result": result}
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                return {"success": False, "error": "No execute method available"}

        return DynamicSkill(metadata, module)

    def _infer_directories(self, query: str) -> List[Path]:
        """Infer which directories to scan based on query"""
        query_lower = query.lower()
        directories = []

        for category, keywords in self.path_hints.items():
            if any(kw in query_lower for kw in keywords):
                # Add category directory
                cat_path = self.scanner.skills_base_path / category
                if cat_path.exists():
                    directories.append(cat_path)

        return directories

    def _check_loaded_skills(self, query: str) -> Optional[BaseSkill]:
        """Level 0: Check already loaded skills"""
        best_skill = self.registry.get_best_skill(query)
        return best_skill

    def _path_guided_scan(self, query: str) -> List[SkillMetadata]:
        """Level 1: Scan inferred directories"""
        directories = self._infer_directories(query)
        all_skills = []

        for directory in directories:
            if str(directory) not in self.scanned_paths:
                skills = self.scanner.scan_directory(directory, recursive=True)
                all_skills.extend(skills)
                self.scanned_paths.add(str(directory))

        return all_skills

    def _full_scan_and_match(self, query: str, top_k: int = 5) -> List[MatchResult]:
        """Level 2: Full scan + semantic matching"""
        # Ensure we have scanned everything
        if not self.scanner.loaded:
            self.scanner.scan_all_skills()
            # Fit matcher on all skills
            all_metadata = list(self.scanner.index.values())
            self.matcher.fit(all_metadata)

        # Find matches
        matches = self.matcher.find_skills(query, top_k=top_k)
        return matches

    def _detect_missing_skill(self, query: str) -> Dict[str, str]:
        """Level 3: Detect what skill is missing"""
        # Extract potential skill name from query
        # Simple heuristic: first verb + noun
        words = query.lower().split()

        # Common action words
        actions = ["parse", "extract", "convert", "analyze", "generate",
                   "read", "write", "crawl", "scrape", "fetch", "download",
                   "transform", "summarize", "translate", "format"]

        detected_action = None
        detected_object = None

        for word in words:
            if word in actions:
                detected_action = word
            elif len(word) > 3 and not detected_object:
                detected_object = word

        if detected_action and detected_object:
            suggested_name = f"{detected_action}_{detected_object}"
        else:
            suggested_name = "unknown_skill"

        return {
            "missing_skill": suggested_name,
            "desc": f"Skill to handle: {query[:100]}",
            "original_query": query,
        }

    def find_skill(self, query: str, min_confidence: float = 0.3) -> DiscoveryResult:
        """Main discovery method - 4-level progressive discovery"""
        result = DiscoveryResult()

        # Level 0: Hot cache
        loaded_skill = self._check_loaded_skills(query)
        if loaded_skill:
            result.skill = loaded_skill
            result.level = DiscoveryLevel.HOT_CACHE
            # Find metadata for loaded skill
            result.metadata = self.scanner.get_skill_metadata(loaded_skill.name)
            return result

        # Level 1: Path-guided scan
        new_skills = self._path_guided_scan(query)
        if new_skills:
            # Quick match on newly scanned skills
            matches = self.matcher.simple_match(query, new_skills, top_k=3)
            if matches and matches[0].score >= min_confidence:
                best_match = matches[0]
                skill = self._load_skill_code(best_match.skill)
                if skill:
                    self.registry.register_skill(skill)
                    result.skill = skill
                    result.metadata = best_match.skill
                    result.level = DiscoveryLevel.PATH_GUIDED
                    result.candidates = matches
                    return result

        # Level 2: Full scan + semantic match
        matches = self._full_scan_and_match(query, top_k=5)
        if matches:
            result.candidates = matches

            # Try to load top matches until one succeeds
            for match in matches:
                if match.score >= min_confidence:
                    skill = self._load_skill_code(match.skill)
                    if skill:
                        self.registry.register_skill(skill)
                        result.skill = skill
                        result.metadata = match.skill
                        result.level = DiscoveryLevel.FULL_SCAN
                        return result

        # Level 3: Missing skill
        result.level = DiscoveryLevel.MISSING_SKILL
        result.missing_skill_hint = self._detect_missing_skill(query)
        result.error = f"No suitable skill found for: {query[:50]}..."

        return result

    def find_skills_for_expansion(self, query: str, failed_skill: str = None) -> List[MatchResult]:
        """Find additional skills when execution fails (Failure-driven expansion)"""
        # Expand search scope
        # 1. Scan more directories
        for category in self.path_hints.keys():
            cat_path = self.scanner.skills_base_path / category
            if cat_path.exists() and str(cat_path) not in self.scanned_paths:
                self.scanner.scan_directory(cat_path, recursive=True)
                self.scanned_paths.add(str(cat_path))

        # 2. Re-run matching with lower threshold
        all_skills = list(self.scanner.index.values())
        if all_skills:
            self.matcher.fit(all_skills)
            matches = self.matcher.find_skills(query, top_k=10, min_score=0.05)

            # Exclude already tried skill
            if failed_skill:
                matches = [m for m in matches if m.skill.name != failed_skill]

            return matches

        return []


def discover_skill(query: str, registry: SkillRegistry = None) -> DiscoveryResult:
    """Convenience function for skill discovery"""
    discovery = SkillDiscovery(registry)
    return discovery.find_skill(query)
