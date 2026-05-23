"""Skill Scanner - Level 1 Discovery with Full Frontmatter Support

Entry points for skill discovery:
1. linked_skills/ - each subdirectory is a skill collection (may be symlink)
2. streamlit_ui/skills/ - each subdirectory is a skill collection
3. built_in/ - core skills

A skill is any directory containing SKILL.md (with valid frontmatter).


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

# Patterns to ignore during skill scanning
IGNORE_PATTERNS = {
    "__pycache__", ".git", ".idea", ".DS_Store", ".pytest_cache", ".venv",
    "node_modules", ".vscode", ".env", ".gitignore", ".mypy_cache", ".tox",
    "dist", "build", "*.pyc", "*.pyo", "*.egg-info"
}


def _should_ignore_path(path: Path) -> bool:
    """Check if a path should be ignored during scanning"""
    name = path.name
    if name in IGNORE_PATTERNS:
        return True
    if name.startswith(".") or name.startswith("__"):
        return True
    if name.endswith(".pyc") or name.endswith(".pyo"):
        return True
    return False

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
    auto_trigger: bool = False
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
            "auto_trigger": self.auto_trigger,
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
            auto_trigger=level1.auto_trigger,
            tags=level1.tags,
            aliases=level1.aliases,
        )


class SkillScanner:
    """Filesystem-native skill scanner - Lazy + Directory-semantic aware + Progressive Disclosure"""

    def __init__(self, skills_base_path: Path = None, external_skills_paths: List[Path] = None):
        # Support both project structure and skills/ folder
        self.skills_base_path = skills_base_path or Path(__file__).parent.parent.parent.parent / "skills"
        
        # External skills paths (additional skill sources)
        self.external_skills_paths = external_skills_paths or []
        
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
            "text": ["text", "nlp", "parse", "extract", "summarize", "transcribe", "transcription", "audio", "speech", "voice"],
        }

        logger.info(f"SkillScanner initialized with base path: {self.skills_base_path}")

    def scan_directory(self, directory: Path, recursive: bool = True,
                        path_prefix: Path = None) -> List[SkillIndexEntry]:
        """Scan a directory for skills (Stage 1: Level 1 only)

        Only extracts minimal metadata (~100 tokens per skill).
        No SKILL.md body content is loaded at this stage.

        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively
            path_prefix: Optional path prefix to use instead of directory.
                        Used for symlinks to preserve the symlink path structure.
        """
        skills = []
        scan_path = directory if directory.is_absolute() else self.skills_base_path / directory

        if not scan_path.exists():
            logger.warning(f"Directory not found: {scan_path}")
            return skills

        # Use path_prefix for building display paths (for symlinks)
        display_base = path_prefix if path_prefix else scan_path

        # Look for skill directories (each dir with SKILL.md is a skill)
        if recursive:
            # Find all SKILL.md files recursively
            for skill_md in scan_path.rglob("SKILL.md"):
                real_skill_path = skill_md.parent
                
                # Skip if this is in an ignored directory
                if _should_ignore_path(real_skill_path):
                    logger.debug(f"Ignoring skill in excluded path: {real_skill_path}")
                    continue
                # Build display path: replace scan_path prefix with display_base
                try:
                    rel_path = real_skill_path.relative_to(scan_path)
                    display_path = display_base / rel_path
                except ValueError:
                    display_path = real_skill_path

                manifest = self._loader.load_level1(real_skill_path)
                if manifest:
                    # Override the path with display path
                    manifest.path = display_path
                    entry = SkillIndexEntry.from_level1(manifest)
                    skills.append(entry)
                    self.index[entry.name] = entry

                    # Index by display path
                    path_key = str(display_path)
                    if path_key not in self.path_index:
                        self.path_index[path_key] = []
                    if entry.name not in self.path_index[path_key]:
                        self.path_index[path_key].append(entry.name)

            # Also look for skill.yaml files (alternative format)
            for yaml_file in scan_path.rglob("skill.yaml"):
                real_skill_path = yaml_file.parent
                
                # Skip if this is in an ignored directory
                if _should_ignore_path(real_skill_path):
                    continue
                
                # Build display path
                try:
                    rel_path = real_skill_path.relative_to(scan_path)
                    display_path = display_base / rel_path
                except ValueError:
                    display_path = real_skill_path

                # Skip if already indexed
                if any(str(display_path) == str(e.path) for e in skills):
                    continue

                manifest = self._loader.load_level1(real_skill_path)
                if manifest:
                    manifest.path = display_path
                    entry = SkillIndexEntry.from_level1(manifest)
                    skills.append(entry)
                    self.index[entry.name] = entry
        else:
            # Non-recursive: only immediate subdirectories
            for subdir in scan_path.iterdir():
                if subdir.is_dir() and not _should_ignore_path(subdir):
                    manifest = self._loader.load_level1(subdir)
                    if manifest:
                        entry = SkillIndexEntry.from_level1(manifest)
                        skills.append(entry)
                        self.index[entry.name] = entry

                        path_key = str(subdir)
                        if path_key not in self.path_index:
                            self.path_index[path_key] = []
                        self.path_index[path_key].append(entry.name)

        logger.info(f"Scanned {scan_path} (display as {display_base}): found {len(skills)} skills (Level 1 only)")
        return skills

    def scan_all_skills(self) -> List[SkillIndexEntry]:
        """Full scan of all skills directories - Level 1 only

        Skills are discovered from three entry points:
        1. built_in/ - core built-in skills
        2. linked_skills/ - each subdirectory is a skill collection
        3. streamlit_ui/skills/ - each subdirectory is a skill collection
        4. External skills paths from configuration

        Each skill collection folder is scanned recursively for SKILL.md files.
        """
        all_skills = []

        # Scan built-in skills
        builtin_path = Path(__file__).parent.parent / "skills" / "built_in"
        if builtin_path.exists():
            all_skills.extend(self.scan_directory(builtin_path, recursive=False))

        # Entry point 1: linked_skills/ at project root - each subdir is a skill collection
        # Support both relative path from scanner and absolute path
        linked_skills_paths = [
            # Relative to scanner location (5 levels up: scanner.py -> skills -> core -> safe_claw -> streamlit_ui -> project_root)
            Path(__file__).parent.parent.parent.parent.parent / "linked_skills",
            # Also check if explicitly provided as external path
        ]
        
        # Add any external paths that look like linked_skills
        for ext_path in self.external_skills_paths:
            if "linked_skills" in str(ext_path) and ext_path not in linked_skills_paths:
                linked_skills_paths.append(ext_path)
        
        scanned_linked_skills = False
        for linked_skills_root in linked_skills_paths:
            if linked_skills_root.exists():
                logger.info(f"Scanning linked_skills entry point: {linked_skills_root}")
                scanned_linked_skills = True
                for collection_dir in linked_skills_root.iterdir():
                    if collection_dir.is_dir() or collection_dir.is_symlink():
                        # If it's a symlink, resolve it for scanning but preserve symlink path
                        if collection_dir.is_symlink():
                            real_dir = collection_dir.resolve()
                            logger.info(f"  Scanning skill collection: {collection_dir.name} -> {real_dir}")
                            # Pass symlink path as prefix to preserve path structure
                            all_skills.extend(self.scan_directory(real_dir, recursive=True, path_prefix=collection_dir))
                        else:
                            logger.info(f"  Scanning skill collection: {collection_dir.name}")
                            all_skills.extend(self.scan_directory(collection_dir, recursive=True))
        
        if not scanned_linked_skills:
            logger.warning(f"linked_skills entry point not found. Checked: {[str(p) for p in linked_skills_paths]}")

        # Entry point 2: streamlit_ui/skills/ - each subdir is a skill collection
        streamlit_skills_root = Path(__file__).parent.parent.parent.parent / "skills"
        if streamlit_skills_root.exists():
            logger.info(f"Scanning streamlit_ui/skills entry point: {streamlit_skills_root}")
            for collection_dir in streamlit_skills_root.iterdir():
                if collection_dir.is_dir() or collection_dir.is_symlink():
                    # Handle symlinks same as above
                    if collection_dir.is_symlink():
                        real_dir = collection_dir.resolve()
                        logger.info(f"  Scanning skill collection: {collection_dir.name} -> {real_dir}")
                        all_skills.extend(self.scan_directory(real_dir, recursive=True, path_prefix=collection_dir))
                    else:
                        logger.info(f"  Scanning skill collection: {collection_dir.name}")
                        all_skills.extend(self.scan_directory(collection_dir, recursive=True))
        else:
            logger.warning(f"streamlit_ui/skills entry point not found: {streamlit_skills_root}")

        # Scan external skills paths (legacy support)
        for external_path in self.external_skills_paths:
            if external_path.exists():
                logger.info(f"Scanning external skills path: {external_path}")
                all_skills.extend(self.scan_directory(external_path, recursive=True))
            else:
                logger.warning(f"External skills path not found: {external_path}")

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
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: 记录manifest获取开始
        logger.info(f"🔍 DEBUG: scanner.get_manifest 开始: {skill_name}")
        logger.info(f"🔍 DEBUG: load_l2={load_l2}, scan_l3={scan_l3}")
        
        # Check cache
        if skill_name in self._manifest_cache:
            manifest = self._manifest_cache[skill_name]
            logger.info(f"🔍 DEBUG: 从缓存获取manifest: {skill_name}")
            # Load additional levels if requested
            if load_l2 and not manifest.level2_loaded:
                logger.info(f"🔍 DEBUG: 开始加载L2内容...")
                self._load_level2(manifest)
            if scan_l3 and not manifest.level3_scanned:
                logger.info(f"🔍 DEBUG: 开始扫描L3文件...")
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 DEBUG: _load_level2 开始读取SKILL.md: {manifest.path}")
        level2 = self._loader.load_level2(manifest.path)
        if level2:
            manifest.level2 = level2
            manifest.level2_loaded = True
            
            # DEBUG: 记录实际加载的内容大小
            if hasattr(level2, 'description') and level2.description:
                desc_length = len(level2.description)
                logger.info(f"🔍 DEBUG: L2描述长度: {desc_length} 字符")
                logger.info(f"🔍 DEBUG: L2估算tokens: {desc_length // 4}")
            
            logger.info(f"🔍 DEBUG: _load_level2 完成: {manifest.path}")
            return True
        else:
            logger.error(f"🔍 DEBUG: _load_level2 失败: {manifest.path}")
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
                    auto_trigger=entry_dict.get("auto_trigger", False),
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


def get_skill_scanner(external_skills_paths: List[Path] = None) -> SkillScanner:
    """Get singleton skill scanner instance"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SkillScanner(external_skills_paths=external_skills_paths)
    return _scanner_instance
