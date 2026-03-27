"""Skill Scanner - Lazy filesystem-based skill discovery

Stage 1: Directory-level shallow scan
- Only reads skill.yaml files
- No code import until needed
"""

import os
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Lightweight skill metadata from yaml (no code)"""
    name: str
    description: str
    path: Path
    tags: List[str]
    inputs: List[str]
    outputs: List[str]
    aliases: List[str]
    user_invocable: bool = True
    version: str = "1.0.0"
    category: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
            "tags": self.tags,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "aliases": self.aliases,
            "user_invocable": self.user_invocable,
            "version": self.version,
            "category": self.category,
        }


class SkillScanner:
    """Filesystem-native skill scanner - Lazy + Directory-semantic aware"""

    def __init__(self, skills_base_path: Path = None):
        # Support both project structure and skills/ folder
        self.skills_base_path = skills_base_path or Path(__file__).parent.parent.parent.parent / "skills"
        self.index: Dict[str, SkillMetadata] = {}  # name -> metadata
        self.path_index: Dict[str, List[str]] = {}  # directory path -> skill names
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

    def _infer_category(self, path: Path, yaml_data: Dict) -> str:
        """Infer skill category from path and yaml data"""
        # From yaml tags
        tags = yaml_data.get("tags", [])
        if tags:
            for cat, keywords in self.category_keywords.items():
                if any(kw in tags[0].lower() for kw in keywords):
                    return cat

        # From path
        path_str = str(path).lower()
        for cat, keywords in self.category_keywords.items():
            if cat in path_str:
                return cat
            for kw in keywords:
                if kw in path_str:
                    return cat

        return "general"

    def _parse_skill_yaml(self, yaml_path: Path) -> Optional[SkillMetadata]:
        """Parse skill.yaml or SKILL.md with frontmatter"""
        try:
            content = yaml_path.read_text(encoding="utf-8")

            # Try YAML frontmatter in SKILL.md
            if "---" in content:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    data = yaml.safe_load(yaml_content)
                else:
                    data = yaml.safe_load(content)
            else:
                data = yaml.safe_load(content)

            if not data or "name" not in data:
                return None

            description = data.get("description", "")
            # Truncate long descriptions
            if len(description) > 500:
                description = description[:497] + "..."

            category = data.get("category") or self._infer_category(yaml_path.parent, data)

            return SkillMetadata(
                name=data["name"],
                description=description,
                path=yaml_path.parent,
                tags=data.get("tags", []),
                inputs=[p.get("name", str(p)) for p in data.get("inputs", [])],
                outputs=data.get("outputs", []),
                aliases=data.get("aliases", []),
                user_invocable=data.get("user_invocable", True),
                version=data.get("version", "1.0.0"),
                category=category,
            )
        except Exception as e:
            logger.warning(f"Failed to parse {yaml_path}: {e}")
            return None

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[SkillMetadata]:
        """Scan a directory for skills (Stage 1: shallow scan)"""
        skills = []
        scan_path = directory if directory.is_absolute() else self.skills_base_path / directory

        if not scan_path.exists():
            logger.warning(f"Directory not found: {scan_path}")
            return skills

        # Look for skill.yaml or SKILL.md
        pattern = "**/*.yaml" if recursive else "*.yaml"
        for yaml_file in scan_path.glob(pattern):
            if yaml_file.name in ["skill.yaml", "package.yaml", "config.yaml"]:
                skill = self._parse_skill_yaml(yaml_file)
                if skill:
                    skills.append(skill)
                    self.index[skill.name] = skill

        # Also look for SKILL.md files (common in ljg-skills)
        md_pattern = "**/SKILL.md" if recursive else "SKILL.md"
        for md_file in scan_path.glob(md_pattern):
            skill = self._parse_skill_yaml(md_file)
            if skill:
                skills.append(skill)
                self.index[skill.name] = skill

        # Index by path
        for skill in skills:
            path_key = str(skill.path)  # skill.path is already the skill folder
            if path_key not in self.path_index:
                self.path_index[path_key] = []
            if skill.name not in self.path_index[path_key]:
                self.path_index[path_key].append(skill.name)

        logger.info(f"Scanned {scan_path}: found {len(skills)} skills")
        return skills

    def scan_all_skills(self) -> List[SkillMetadata]:
        """Full scan of all skills directories (expensive, use sparingly)"""
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
        logger.info(f"Total skills indexed: {len(all_skills)}")
        return all_skills

    def scan_paths(self, paths: List[Path], recursive: bool = True) -> List[SkillMetadata]:
        """Scan multiple skill paths at startup (pre-loading)
        
        Args:
            paths: List of directory paths to scan
            recursive: Whether to scan recursively
            
        Returns:
            List of all discovered skill metadata
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
        logger.info(f"Pre-loaded {len(all_skills)} skills from {len(paths)} paths")
        return all_skills

    def search_by_path(self, path_hint: str) -> List[SkillMetadata]:
        """Find skills by path hint (e.g., 'data/', 'web/')"""
        results = []
        for skill in self.index.values():
            if path_hint.lower() in str(skill.path).lower():
                results.append(skill)
        return results

    def save_index(self, index_path: Path = None):
        """Save index to JSON for fast loading"""
        index_path = index_path or self.skills_base_path / "skill_index.json"
        data = {
            "skills": {name: metadata.to_dict() for name, metadata in self.index.items()},
            "path_index": self.path_index,
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved skill index to {index_path}")

    def load_index(self, index_path: Path = None) -> bool:
        """Load index from JSON"""
        index_path = index_path or self.skills_base_path / "skill_index.json"
        if not index_path.exists():
            return False

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for name, metadata_dict in data.get("skills", {}).items():
                metadata_dict["path"] = Path(metadata_dict["path"])
                self.index[name] = SkillMetadata(**metadata_dict)

            self.path_index = data.get("path_index", {})
            self.loaded = True
            logger.info(f"Loaded skill index from {index_path}: {len(self.index)} skills")
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False


# Singleton instance
_scanner_instance: Optional[SkillScanner] = None


def get_skill_scanner() -> SkillScanner:
    """Get singleton skill scanner instance"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SkillScanner()
    return _scanner_instance
