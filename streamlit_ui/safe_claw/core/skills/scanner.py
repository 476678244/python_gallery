"""Skill Scanner - Level 1 Discovery with Full Frontmatter Support

Stage 1: Directory-level shallow scan
- Only reads SKILL.md frontmatter or skill.yaml
- No Level 2/3 content loading (progressive disclosure)
- ~100 tokens per skill

Follows Claude Code skills specification with 3-level progressive disclosure:
- Level 1: name + description + frontmatter (always loaded)
- Level 2: SKILL.md body (loaded on trigger)
- Level 3: supporting files (loaded on demand)
"""

import os
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict

from streamlit_ui.safe_claw.core.skills.manifest import SkillLevel1, SkillManifest
from streamlit_ui.safe_claw.core.skills.loader import SkillLoader

logger = logging.getLogger(__name__)


@dataclass
class SkillIndexEntry:
    """Lightweight index entry for fast skill lookup"""
    name: str
    description: str
    path: str
    category: str
    disable_model_invocation: bool = False
    user_invocable: bool = True
    tags: List[str] = None
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.aliases is None:
            self.aliases = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "category": self.category,
            "disable_model_invocation": self.disable_model_invocation,
            "user_invocable": self.user_invocable,
            "tags": self.tags,
            "aliases": self.aliases,
        }
    
    @classmethod
    def from_level1(cls, level1: SkillLevel1) -> "SkillIndexEntry":
        """Create index entry from Level 1 data"""
        return cls(
            name=level1.name,
            description=level1.description,
            path=str(level1.path),
            category=level1.category,
            disable_model_invocation=level1.disable_model_invocation,
            user_invocable=level1.user_invocable,
            tags=level1.tags,
            aliases=level1.aliases,
        )


class SkillScanner:
    """Filesystem-native skill scanner - Lazy + Directory-semantic aware + Progressive Disclosure"""

    def __init__(self, skills_base_path: Path = None):
        # Support both project structure and skills/ folder
        self.skills_base_path = skills_base_path or Path(__file__).parent.parent.parent.parent / "skills"
        
        # Level 1 index: name -> index entry (lightweight, always loaded)
        self.index: Dict[str, SkillIndexEntry] = {}
        
        # Path-based index for directory-semantic scanning
        self.path_index: Dict[str, List[str]] = {}  # directory path -> skill names
        
        # Full manifest cache (loaded on demand)
        self._manifest_cache: Dict[str, SkillManifest] = {}
        
        # Loader for progressive disclosure
        self._loader = SkillLoader(self.skills_base_path)
        
        self.loaded = False

        # Category keywords for path-guided scanning
        self.category_keywords = {
            "data": ["csv", "json", "sql", "query", "database", "db", "table", "excel"],
            "web": ["http", "url", "crawl", "scrape", "fetch", "api", "web", "browser"],
            "file": ["read", "write", "file", "directory", "path", "folder"],
            "code": ["code", "analyze", "format", "lint", "syntax", "ast"],
            "finance": ["stock", "portfolio", "13f", "market", "price", "finance"],
            "image": ["image", "img", "png", "jpeg", "photo", "visual", "graph"],
            "text": ["text", "nlp", "parse", "extract", "summarize"],
        }

        logger.info(f"SkillScanner initialized with base path: {self.skills_base_path}")

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[SkillIndexEntry]:
        """Scan a directory for skills (Stage 1: Level 1 only)
        
        Only extracts minimal metadata (~100 tokens per skill).
        No SKILL.md body content is loaded at this stage.
        """
        skills = []
        scan_path = directory if directory.is_absolute() else self.skills_base_path / directory

        if not scan_path.exists():
            logger.warning(f"Directory not found: {scan_path}")
            return skills

        # Look for skill directories (each dir with SKILL.md is a skill)
        if recursive:
            # Find all SKILL.md files recursively
            for skill_md in scan_path.rglob("SKILL.md"):
                skill_path = skill_md.parent
                manifest = self._loader.load_level1(skill_path)
                if manifest:
                    entry = SkillIndexEntry.from_level1(manifest)
                    skills.append(entry)
                    self.index[entry.name] = entry
                    
                    # Index by path
                    path_key = str(skill_path)
                    if path_key not in self.path_index:
                        self.path_index[path_key] = []
                    if entry.name not in self.path_index[path_key]:
                        self.path_index[path_key].append(entry.name)
            
            # Also look for skill.yaml files (alternative format)
            for yaml_file in scan_path.rglob("skill.yaml"):
                skill_path = yaml_file.parent
                # Skip if already indexed via SKILL.md
                if any(str(skill_path) == str(e.path) for e in skills):
                    continue
                    
                manifest = self._loader.load_level1(skill_path)
                if manifest:
                    entry = SkillIndexEntry.from_level1(manifest)
                    skills.append(entry)
                    self.index[entry.name] = entry
        else:
            # Non-recursive: only immediate subdirectories
            for subdir in scan_path.iterdir():
                if subdir.is_dir():
                    manifest = self._loader.load_level1(subdir)
                    if manifest:
                        entry = SkillIndexEntry.from_level1(manifest)
                        skills.append(entry)
                        self.index[entry.name] = entry
                        
                        path_key = str(subdir)
                        if path_key not in self.path_index:
                            self.path_index[path_key] = []
                        self.path_index[path_key].append(entry.name)

        logger.info(f"Scanned {scan_path}: found {len(skills)} skills (Level 1 only)")
        return skills

    def scan_all_skills(self) -> List[SkillIndexEntry]:
        """Full scan of all skills directories - Level 1 only"""
        all_skills = []

        # Scan built-in skills
        builtin_path = Path(__file__).parent.parent / "skills" / "built_in"
        if builtin_path.exists():
            all_skills.extend(self.scan_directory(builtin_path, recursive=False))

        # Scan public skills
        public_path = self.skills_base_path / "public_skills"
        if public_path.exists():
            for subdir in public_path.iterdir():
                if subdir.is_dir():
                    # Each public_skill package has its own structure
                    skills_subdir = subdir / "skills" if (subdir / "skills").exists() else subdir
                    all_skills.extend(self.scan_directory(skills_subdir, recursive=True))

        # Scan private skills
        private_path = self.skills_base_path / "private_skills"
        if private_path.exists():
            all_skills.extend(self.scan_directory(private_path, recursive=True))

        self.loaded = True
        logger.info(f"Total skills indexed (L1): {len(all_skills)}")
        return all_skills

    def scan_paths(self, paths: List[Path], recursive: bool = True) -> List[SkillIndexEntry]:
        """Scan multiple skill paths at startup (pre-loading Level 1)
        
        Args:
            paths: List of directory paths to scan
            recursive: Whether to scan recursively
            
        Returns:
            List of all discovered skill index entries (Level 1 only)
        """
        all_skills = []
        
        for path in paths:
            if path.exists():
                logger.info(f"Pre-scanning skill path: {path}")
                skills = self.scan_directory(path, recursive=recursive)
                all_skills.extend(skills)
            else:
                logger.warning(f"Skill path not found: {path}")
        
        self.loaded = True
        logger.info(f"Pre-loaded {len(all_skills)} skills from {len(paths)} paths (Level 1)")
        return all_skills

    def get_manifest(self, skill_name: str, 
                    load_l2: bool = False,
                    scan_l3: bool = False) -> Optional[SkillManifest]:
        """Get full skill manifest with progressive loading
        
        Args:
            skill_name: Name of the skill
            load_l2: Load Level 2 (SKILL.md body content)
            scan_l3: Scan Level 3 (supporting file list)
        """
        # Check cache
        if skill_name in self._manifest_cache:
            manifest = self._manifest_cache[skill_name]
            # Load additional levels if requested
            if load_l2 and not manifest.level2_loaded:
                self._load_level2(manifest)
            if scan_l3 and not manifest.level3_scanned:
                self._scan_level3(manifest)
            return manifest
        
        # Find in index
        entry = self.index.get(skill_name)
        if not entry:
            logger.warning(f"Skill not found in index: {skill_name}")
            return None
        
        # Build manifest progressively
        skill_path = Path(entry.path)
        manifest = self._loader.load_full_manifest(
            skill_path,
            load_l1=True,
            load_l2=load_l2,
            scan_l3=scan_l3
        )
        
        if manifest:
            self._manifest_cache[skill_name] = manifest
        
        return manifest
    
    def _load_level2(self, manifest: SkillManifest) -> bool:
        """Load Level 2 content for a manifest"""
        level2 = self._loader.load_level2(manifest.path)
        if level2:
            manifest.level2 = level2
            manifest.level2_loaded = True
            return True
        return False
    
    def _scan_level3(self, manifest: SkillManifest) -> bool:
        """Scan Level 3 files for a manifest"""
        level3 = self._loader.scan_level3(manifest.path)
        manifest.level3 = level3
        manifest.level3_scanned = True
        return True

    def search_by_path(self, path_hint: str) -> List[SkillIndexEntry]:
        """Find skills by path hint (e.g., 'data/', 'web/')"""
        results = []
        for entry in self.index.values():
            if path_hint.lower() in entry.path.lower():
                results.append(entry)
        return results
    
    def search_by_category(self, category: str) -> List[SkillIndexEntry]:
        """Find skills by category"""
        return [e for e in self.index.values() if e.category == category]
    
    def get_auto_invocable_skills(self) -> List[SkillIndexEntry]:
        """Get skills that can be auto-invoked by Claude
        
        Excludes skills with disable_model_invocation: true
        """
        return [e for e in self.index.values() if not e.disable_model_invocation]
    
    def get_user_invocable_skills(self) -> List[SkillIndexEntry]:
        """Get skills that can be invoked by user via /
        
        Excludes skills with user_invocable: false
        """
        return [e for e in self.index.values() if e.user_invocable]

    def save_index(self, index_path: Path = None):
        """Save Level 1 index to JSON for fast loading"""
        index_path = index_path or self.skills_base_path / "skill_index.json"
        data = {
            "skills": {name: entry.to_dict() for name, entry in self.index.items()},
            "path_index": self.path_index,
            "metadata": {
                "total_skills": len(self.index),
                "auto_invocable": len(self.get_auto_invocable_skills()),
                "user_invocable": len(self.get_user_invocable_skills()),
            }
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved skill index to {index_path}")

    def load_index(self, index_path: Path = None) -> bool:
        """Load Level 1 index from JSON"""
        index_path = index_path or self.skills_base_path / "skill_index.json"
        if not index_path.exists():
            return False

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for name, entry_dict in data.get("skills", {}).items():
                entry = SkillIndexEntry(
                    name=entry_dict["name"],
                    description=entry_dict["description"],
                    path=entry_dict["path"],
                    category=entry_dict.get("category", "general"),
                    disable_model_invocation=entry_dict.get("disable_model_invocation", False),
                    user_invocable=entry_dict.get("user_invocable", True),
                    tags=entry_dict.get("tags", []),
                    aliases=entry_dict.get("aliases", []),
                )
                self.index[name] = entry

            self.path_index = data.get("path_index", {})
            self.loaded = True
            
            logger.info(f"Loaded skill index from {index_path}: {len(self.index)} skills (L1)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get summary of the Level 1 index"""
        total_tokens = sum(
            len(e.description) // 4 + len(e.name) // 4
            for e in self.index.values()
        )
        
        return {
            "total_skills": len(self.index),
            "auto_invocable": len(self.get_auto_invocable_skills()),
            "user_invocable": len(self.get_user_invocable_skills()),
            "categories": len(set(e.category for e in self.index.values())),
            "estimated_tokens": total_tokens,
            "loaded": self.loaded,
        }


# Singleton instance
_scanner_instance: Optional[SkillScanner] = None


def get_skill_scanner() -> SkillScanner:
    """Get singleton skill scanner instance"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SkillScanner()
    return _scanner_instance
