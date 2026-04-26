"""Progressive Skill Discovery - 3-Level Progressive Disclosure

Main entry point for skill discovery with Claude Code spec compliance:
1. Level 1: Hot cache (name + description only, always loaded)
2. Level 2: Progressive scan with semantic matching (load SKILL.md on trigger)
3. Level 3: Supporting files (loaded on demand)
4. Failure-driven expansion

Reference: https://code.claude.com/docs/llms.txt
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from streamlit_ui.safe_claw.core.skills.scanner import SkillScanner, SkillIndexEntry, get_skill_scanner
from streamlit_ui.safe_claw.core.skills.matcher import SemanticMatcher, MatchResult, get_semantic_matcher
from streamlit_ui.safe_claw.core.skills.manifest import SkillManifest
from streamlit_ui.safe_claw.core.skills.loader import SkillLoader, LoadContext
from streamlit_ui.safe_claw.core.skills.executor import SkillExecutor, ExecutionContext

logger = logging.getLogger(__name__)


class DiscoveryLevel(Enum):
    """Discovery expansion levels following progressive disclosure"""
    HOT_CACHE = 0       # Already loaded (L1 + L2 loaded previously)
    L1_INDEX = 1        # L1 metadata only (need to load L2)
    L2_LOADED = 2       # L2 loaded (full skill content available)
    L3_EXPANDED = 3     # L3 files available (supporting content)
    MISSING_SKILL = 4   # Cannot find suitable skill


@dataclass
class DiscoveryResult:
    """Result of skill discovery with progressive disclosure state"""
    skill_name: Optional[str] = None
    manifest: Optional[SkillManifest] = None
    level: DiscoveryLevel = DiscoveryLevel.MISSING_SKILL
    candidates: List[MatchResult] = None
    missing_skill_hint: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.candidates is None:
            self.candidates = []
    
    @property
    def success(self) -> bool:
        return self.level != DiscoveryLevel.MISSING_SKILL and self.manifest is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "level": self.level.name,
            "success": self.success,
            "candidates": [
                {"name": c.skill.name, "score": c.score, "terms": c.matched_terms}
                for c in self.candidates[:5]
            ] if self.candidates else [],
            "manifest_summary": self.manifest.to_dict(
                include_level1=True,
                include_level2=self.level.value >= DiscoveryLevel.L2_LOADED.value
            ) if self.manifest else None,
            "missing_skill_hint": self.missing_skill_hint,
            "error": self.error,
        }


class SkillDiscovery:
    """Progressive skill discovery with 3-level disclosure"""

    def __init__(self, scanner: SkillScanner = None, external_skills_paths: List[Path] = None):
        self.scanner = scanner or get_skill_scanner(external_skills_paths=external_skills_paths)
        self.matcher = get_semantic_matcher()
        self.loader = SkillLoader()
        self.executor = SkillExecutor(self.loader)
        self.scanned_paths: set = set()

        self.path_hints = {
            "data": ["data", "sql", "csv", "json", "db"],
            "web": ["web", "http", "url", "crawl", "api", "browser"],
            "file": ["file", "read", "write", "directory", "path"],
            "code": ["code", "analyze", "format", "syntax", "lint"],
            "image": ["image", "img", "png", "visual", "graph", "chart"],
            "text": ["text", "nlp", "parse", "extract", "summarize"],
            "finance": ["stock", "portfolio", "13f", "market", "finance"],
        }

    def _infer_directories(self, query: str) -> List[Path]:
        """Infer which directories to scan based on query"""
        query_lower = query.lower()
        directories = []
        for category, keywords in self.path_hints.items():
            if any(kw in query_lower for kw in keywords):
                cat_path = self.scanner.skills_base_path / category
                if cat_path.exists():
                    directories.append(cat_path)
        return directories

    def _check_hot_cache(self, skill_name: str) -> Optional[SkillManifest]:
        """Level 0: Check if skill is already fully loaded in cache"""
        manifest = self.scanner.get_manifest(skill_name, load_l2=False, scan_l3=False)
        if manifest and manifest.level2_loaded:
            return manifest
        return None

    def _check_l1_index(self, query: str, min_confidence: float = 0.3) -> Optional[DiscoveryResult]:
        """Level 1: Search L1 index and match on metadata only"""
        if not self.scanner.loaded:
            self.scanner.scan_all_skills()
        
        entries = list(self.scanner.index.values())
        if not entries:
            return None
        
        matches = self.matcher.simple_match_l1(query, entries, top_k=5)
        
        if matches and matches[0].score >= min_confidence:
            best_match = matches[0]
            return DiscoveryResult(
                skill_name=best_match.skill.name,
                manifest=None,
                level=DiscoveryLevel.L1_INDEX,
                candidates=matches
            )
        return None
    
    def _load_and_trigger(self, skill_name: str, query: str, arguments: List[str] = None,
                         session_id: Optional[str] = None,
                         output_callback: Optional[Callable[[str], None]] = None) -> Optional[DiscoveryResult]:
        """Load L2 and trigger skill execution"""
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: 记录动态加载开始
        logger.info(f"🔍 DEBUG: _load_and_trigger 开始加载skill: {skill_name}")
        logger.info(f"🔍 DEBUG: 准备加载L2 manifest和扫描L3文件...")
        
        manifest = self.scanner.get_manifest(skill_name, load_l2=True, scan_l3=True)
        if not manifest:
            logger.error(f"🔍 DEBUG: 加载manifest失败: {skill_name}")
            return None
        
        # DEBUG: 记录manifest信息
        if hasattr(manifest, 'description') and manifest.description:
            desc_length = len(manifest.description)
            logger.info(f"🔍 DEBUG: Skill描述长度: {desc_length} 字符")
            logger.info(f"🔍 DEBUG: 估算描述tokens: {desc_length // 4}")
        
        logger.info(f"🔍 DEBUG: 准备执行skill: {skill_name}")
        context = ExecutionContext(
            session_id=session_id,
            arguments=arguments or [],
            working_dir=Path.cwd(),
            output_callback=output_callback
        )
        
        logger.info(f"🔍 DEBUG: 调用executor.execute...")
        execution_result = self.executor.execute(
            manifest=manifest,
            arguments=arguments or [],
            session_id=session_id,
            working_dir=Path.cwd(),
            output_callback=output_callback
        )
        logger.info(f"🔍 DEBUG: executor.execute 完成")
        
        return DiscoveryResult(
            skill_name=skill_name,
            manifest=manifest,
            level=DiscoveryLevel.L2_LOADED,
            execution_result=execution_result
        )

    def _path_guided_scan(self, query: str) -> List[SkillIndexEntry]:
        """Scan inferred directories based on query keywords"""
        directories = self._infer_directories(query)
        all_skills = []
        for directory in directories:
            if str(directory) not in self.scanned_paths:
                skills = self.scanner.scan_directory(directory, recursive=True)
                all_skills.extend(skills)
                self.scanned_paths.add(str(directory))
        return all_skills

    def _full_scan_and_match(self, query: str, top_k: int = 5) -> List[MatchResult]:
        """Full scan + semantic matching on all skills"""
        if not self.scanner.loaded:
            self.scanner.scan_all_skills()
            entries = list(self.scanner.index.values())
            self.matcher.fit_l1(entries)
        return self.matcher.find_skills_l1(query, top_k=top_k)

    def _detect_missing_skill(self, query: str) -> Dict[str, str]:
        """Detect what skill is missing based on query analysis"""
        words = query.lower().split()
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

    def find_skill(self, query: str, min_confidence: float = 0.3,
                   arguments: List[str] = None, session_id: Optional[str] = None,
                   auto_trigger: bool = False,
                   output_callback: Optional[Callable[[str], None]] = None) -> DiscoveryResult:
        """Main discovery method - progressive disclosure"""
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: 记录skill发现开始
        logger.info(f"🔍 DEBUG: SkillDiscovery.find_skill 开始")
        logger.info(f"🔍 DEBUG: 查询: '{query}'")
        logger.info(f"🔍 DEBUG: 自动触发: {auto_trigger}")
        
        # Exact match by name
        if query.startswith("/"):
            skill_name = query[1:].split()[0]
            if skill_name in self.scanner.index:
                logger.info(f"🔍 DEBUG: 精确匹配skill: {skill_name}")
                if auto_trigger:
                    logger.info(f"🔍 DEBUG: 准备加载并触发skill: {skill_name}")
                    return self._load_and_trigger(skill_name, query, arguments, session_id, output_callback)
                else:
                    return DiscoveryResult(
                        skill_name=skill_name,
                        manifest=None,
                        level=DiscoveryLevel.L1_INDEX
                    )

        # Hot cache check
        check_name = query.split()[0] if not query.startswith("/") else query[1:].split()[0]
        cached = self._check_hot_cache(check_name)
        if cached:
            if auto_trigger:
                # Create context with callback for cached skills
                context = ExecutionContext(
                    session_id=session_id,
                    arguments=arguments or [],
                    working_dir=Path.cwd(),
                    output_callback=output_callback
                )
                execution_result = self.executor.execute(
                    manifest=cached, arguments=arguments or [], session_id=session_id, working_dir=Path.cwd(), output_callback=output_callback
                )
                return DiscoveryResult(
                    skill_name=cached.name, manifest=cached,
                    level=DiscoveryLevel.HOT_CACHE, execution_result=execution_result
                )
            else:
                return DiscoveryResult(
                    skill_name=cached.name, manifest=cached, level=DiscoveryLevel.HOT_CACHE
                )

        # L1 index search
        l1_result = self._check_l1_index(query, min_confidence)
        if l1_result and not auto_trigger:
            return l1_result
        if l1_result and auto_trigger:
            return self._load_and_trigger(l1_result.skill_name, query, arguments, session_id, output_callback)

        # Path-guided scan
        new_skills = self._path_guided_scan(query)
        if new_skills:
            matches = self.matcher.simple_match_l1(query, new_skills, top_k=3)
            if matches and matches[0].score >= min_confidence:
                skill_name = matches[0].skill.name
                if auto_trigger:
                    return self._load_and_trigger(skill_name, query, arguments, session_id, output_callback)
                else:
                    return DiscoveryResult(
                        skill_name=skill_name, manifest=None,
                        level=DiscoveryLevel.L1_INDEX, candidates=matches
                    )

        # Full scan
        matches = self._full_scan_and_match(query, top_k=5)
        if matches:
            for match in matches:
                if match.score >= min_confidence:
                    skill_name = match.skill.name
                    if auto_trigger:
                        return self._load_and_trigger(skill_name, query, arguments, session_id, output_callback)
                    else:
                        return DiscoveryResult(
                            skill_name=skill_name, manifest=None,
                            level=DiscoveryLevel.L1_INDEX, candidates=matches
                        )

        # Missing skill
        result = DiscoveryResult()
        result.level = DiscoveryLevel.MISSING_SKILL
        result.missing_skill_hint = self._detect_missing_skill(query)
        result.error = f"No suitable skill found for: {query[:50]}..."
        result.candidates = matches if 'matches' in locals() else []
        return result

    def trigger_skill(self, skill_name: str, arguments: List[str] = None,
                     session_id: Optional[str] = None,
                     output_callback: Optional[Callable[[str], None]] = None) -> DiscoveryResult:
        """Explicitly trigger a skill by name (load L2 and execute)"""
        return self._load_and_trigger(skill_name, skill_name, arguments, session_id, output_callback)

    def get_skill_prompt(self, skill_name: str, arguments: List[str] = None,
                        session_id: Optional[str] = None) -> Optional[str]:
        """Get the prompt content for a skill (for inline execution)"""
        manifest = self.scanner.get_manifest(skill_name, load_l2=True)
        if not manifest:
            return None
        context = ExecutionContext(
            session_id=session_id, arguments=arguments or [], working_dir=Path.cwd()
        )
        return self.executor.get_skill_prompt(manifest, context)

    def find_skills_for_expansion(self, query: str, failed_skill: str = None) -> List[MatchResult]:
        """Find additional skills when execution fails"""
        for category in self.path_hints.keys():
            cat_path = self.scanner.skills_base_path / category
            if cat_path.exists() and str(cat_path) not in self.scanned_paths:
                self.scanner.scan_directory(cat_path, recursive=True)
                self.scanned_paths.add(str(cat_path))
        
        entries = list(self.scanner.index.values())
        if entries:
            self.matcher.fit_l1(entries)
            matches = self.matcher.find_skills_l1(query, top_k=10, min_score=0.05)
            if failed_skill:
                matches = [m for m in matches if m.skill.name != failed_skill]
            return matches
        return []


def discover_skill(query: str, scanner: SkillScanner = None,
                  auto_trigger: bool = False) -> DiscoveryResult:
    """Convenience function for skill discovery"""
    discovery = SkillDiscovery(scanner)
    return discovery.find_skill(query, auto_trigger=auto_trigger)
