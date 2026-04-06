"""Skill Loader - 3-Level Progressive Disclosure with Dynamic Context

Handles:
- Level 1: Load minimal metadata (always)
- Level 2: Load SKILL.md with dynamic injection and variable substitution
- Level 3: Load supporting files on demand

Variable substitution:
- $ARGUMENTS - All arguments
- $ARGUMENTS[N] / $N - Nth argument (0-indexed)
- ${CLAUDE_SESSION_ID} - Session ID
- ${CLAUDE_SKILL_DIR} - Skill directory path

Dynamic context injection:
- !`command` - Execute shell command and insert output
"""

import os
import re
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from streamlit_ui.safe_claw.core.skills.manifest import (
    SkillManifest, SkillLevel1, SkillLevel2, SkillLevel3,
    parse_skill_md, DYNAMIC_INJECTION_PATTERN
)

logger = logging.getLogger(__name__)


@dataclass
class LoadContext:
    """Context for loading a skill"""
    session_id: Optional[str] = None
    arguments: List[str] = field(default_factory=list)
    working_dir: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)


class SkillLoader:
    """3-Level progressive skill loader"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent.parent / "skills"
        self._manifest_cache: Dict[str, SkillManifest] = {}
        self._level2_cache: Dict[str, SkillLevel2] = {}
        
    def load_level1(self, skill_path: Path) -> Optional[SkillLevel1]:
        """Load Level 1: Minimal metadata from SKILL.md or skill.yaml
        
        Fast operation - only reads frontmatter/name/description.
        ~100 tokens per skill.
        """
        try:
            # Try SKILL.md first
            skill_md_path = skill_path / "SKILL.md"
            if skill_md_path.exists():
                return self._load_l1_from_skill_md(skill_md_path)
            
            # Fallback to skill.yaml
            yaml_path = skill_path / "skill.yaml"
            if yaml_path.exists():
                return self._load_l1_from_yaml(yaml_path)
            
            # Last resort: use directory name
            return SkillLevel1(
                name=skill_path.name,
                description="",
                path=skill_path,
                category=self._infer_category(skill_path)
            )
            
        except Exception as e:
            logger.warning(f"Failed to load L1 for {skill_path}: {e}")
            return None
    
    def _load_l1_from_skill_md(self, path: Path) -> Optional[SkillLevel1]:
        """Extract Level 1 from SKILL.md frontmatter"""
        content = path.read_text(encoding="utf-8")
        
        # Extract frontmatter
        name = path.parent.name
        description = ""
        category = "general"
        tags = []
        aliases = []
        disable_model_invocation = False
        user_invocable = True
        auto_trigger = False
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                    name = fm.get("name", name)
                    description = fm.get("description", "")
                    tags = fm.get("tags", [])
                    aliases = fm.get("aliases", [])
                    disable_model_invocation = fm.get("disable_model_invocation", False)
                    user_invocable = fm.get("user_invocable", True)
                    auto_trigger = fm.get("auto_trigger", False)
                    category = fm.get("category") or self._infer_category(path.parent, fm)
                except yaml.YAMLError:
                    pass
        
        # If no description in frontmatter, use first paragraph
        if not description:
            body = content.split("---", 2)[-1] if content.startswith("---") else content
            lines = body.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    description = line[:200]
                    break
        
        return SkillLevel1(
            name=name,
            description=description,
            path=path.parent,
            category=category,
            tags=tags,
            aliases=aliases,
            disable_model_invocation=disable_model_invocation,
            user_invocable=user_invocable,
            auto_trigger=auto_trigger,
        )
    
    def _load_l1_from_yaml(self, path: Path) -> Optional[SkillLevel1]:
        """Extract Level 1 from skill.yaml"""
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return SkillLevel1(
                name=data.get("name", path.parent.name),
                description=data.get("description", ""),
                path=path.parent,
                version=data.get("version", "1.0.0"),
                category=data.get("category") or self._infer_category(path.parent, data),
                tags=data.get("tags", []),
                aliases=data.get("aliases", []),
                disable_model_invocation=data.get("disable_model_invocation", False),
                user_invocable=data.get("user_invocable", True),
                auto_trigger=data.get("auto_trigger", False),
            )
        except Exception as e:
            logger.warning(f"Failed to parse {path}: {e}")
            return None
    
    def load_level2(self, skill_path: Path, context: Optional[LoadContext] = None) -> Optional[SkillLevel2]:
        """Load Level 2: SKILL.md content with dynamic injection and variable substitution
        
        This loads the full skill instructions including:
        - Frontmatter configuration
        - Body content with variable substitution
        - Dynamic context injection (!`command` execution)
        
        ~5k tokens typical.
        """
        skill_md_path = skill_path / "SKILL.md"
        if not skill_md_path.exists():
            logger.warning(f"SKILL.md not found: {skill_md_path}")
            return None
        
        try:
            content = skill_md_path.read_text(encoding="utf-8")
            
            # Parse base structure
            level2 = parse_skill_md(content, skill_path)
            
            # Apply variable substitution
            if context:
                level2.body_content = self._substitute_variables(
                    level2.body_content, 
                    context,
                    skill_path
                )
                
                # Apply dynamic context injection
                if level2.has_dynamic_injection:
                    level2.body_content = self._inject_dynamic_context(
                        level2.body_content,
                        context,
                        skill_path
                    )
            
            return level2
            
        except Exception as e:
            logger.error(f"Failed to load L2 for {skill_path}: {e}")
            return None
    
    def _substitute_variables(self, content: str, context: LoadContext, skill_path: Path) -> str:
        """Substitute variables in skill content
        
        Supported variables:
        - $ARGUMENTS - All arguments joined
        - $ARGUMENTS[N] - Nth argument (0-indexed)
        - $N - Shorthand for $ARGUMENTS[N]
        - ${CLAUDE_SESSION_ID} - Session ID
        - ${CLAUDE_SKILL_DIR} - Skill directory
        """
        result = content
        
        # ${CLAUDE_SESSION_ID}
        if context.session_id:
            result = result.replace("${CLAUDE_SESSION_ID}", context.session_id)
        
        # ${CLAUDE_SKILL_DIR}
        result = result.replace("${CLAUDE_SKILL_DIR}", str(skill_path))
        
        # $ARGUMENTS[N] pattern
        def replace_arg_n(match):
            try:
                n = int(match.group(1))
                if 0 <= n < len(context.arguments):
                    return context.arguments[n]
                return ""
            except (ValueError, IndexError):
                return match.group(0)
        
        result = re.sub(r'\$ARGUMENTS\[(\d+)\]', replace_arg_n, result)
        
        # $N shorthand (but not $ followed by non-digit, like ${VAR})
        def replace_dollar_n(match):
            try:
                n = int(match.group(1))
                if 0 <= n < len(context.arguments):
                    return context.arguments[n]
                return ""
            except (ValueError, IndexError):
                return match.group(0)
        
        result = re.sub(r'\$(\d+)(?!\w)', replace_dollar_n, result)
        
        # $ARGUMENTS - all arguments
        if "$ARGUMENTS" in result:
            args_str = " ".join(context.arguments)
            result = result.replace("$ARGUMENTS", args_str)
        
        return result
    
    def _inject_dynamic_context(self, content: str, context: LoadContext, skill_path: Path) -> str:
        """Execute commands and inject output into content
        
        Syntax: !`command` - executes command and replaces with stdout
        """
        def execute_command(match):
            cmd = match.group(1).strip()
            
            try:
                # Run command in skill directory or working directory
                cwd = str(skill_path) if skill_path.exists() else str(context.working_dir or ".")
                
                # Set environment variables
                env = os.environ.copy()
                env.update(context.env_vars)
                if context.session_id:
                    env["CLAUDE_SESSION_ID"] = context.session_id
                env["CLAUDE_SKILL_DIR"] = str(skill_path)
                
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=env,
                    timeout=30  # 30 second timeout
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    logger.debug(f"Dynamic injection succeeded: {cmd[:50]}...")
                    return output
                else:
                    logger.warning(f"Dynamic injection failed: {cmd[:50]}... - {result.stderr}")
                    return f"[Command failed: {result.stderr[:100]}]"
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Dynamic injection timeout: {cmd[:50]}...")
                return "[Command timed out]"
            except Exception as e:
                logger.warning(f"Dynamic injection error: {cmd[:50]}... - {e}")
                return f"[Error: {e}]"
        
        return DYNAMIC_INJECTION_PATTERN.sub(execute_command, content)
    
    def scan_level3(self, skill_path: Path) -> SkillLevel3:
        """Scan Level 3: Find supporting files without loading content
        
        Scans for:
        - scripts/*.py, *.sh, etc.
        - templates/*.md
        - examples/*.md
        - reference/*.md
        
        Returns file paths only - content loaded on demand.
        """
        level3 = SkillLevel3()
        
        # Scan scripts directory
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for ext in ["*.py", "*.sh", "*.js", "*.ts"]:
                for file in scripts_dir.glob(ext):
                    level3.scripts[file.stem] = file
        
        # Scan templates directory
        templates_dir = skill_path / "templates"
        if templates_dir.exists():
            for file in templates_dir.glob("*.md"):
                level3.templates[file.stem] = file
        
        # Scan examples directory
        examples_dir = skill_path / "examples"
        if examples_dir.exists():
            for file in examples_dir.glob("*.md"):
                level3.examples[file.stem] = file
        
        # Scan reference directory
        ref_dir = skill_path / "reference"
        if ref_dir.exists():
            for file in ref_dir.glob("*.md"):
                level3.references[file.stem] = file
        
        # Also check for loose .md files in skill root (reference files)
        for file in skill_path.glob("*.md"):
            if file.name != "SKILL.md":
                level3.references[file.stem] = file
        
        return level3
    
    def load_full_manifest(self, skill_path: Path, 
                         load_l1: bool = True,
                         load_l2: bool = False,
                         scan_l3: bool = False,
                         context: Optional[LoadContext] = None) -> Optional[SkillManifest]:
        """Load complete skill manifest with specified levels
        
        Args:
            skill_path: Path to skill directory
            load_l1: Load Level 1 (metadata)
            load_l2: Load Level 2 (SKILL.md content)
            scan_l3: Scan Level 3 (supporting files)
            context: Loading context for variable substitution
        """
        manifest = SkillManifest(
            name=skill_path.name,
            path=skill_path
        )
        
        # Level 1
        if load_l1:
            level1 = self.load_level1(skill_path)
            if level1:
                manifest.level1 = level1
                manifest.name = level1.name  # Use proper name from frontmatter
                manifest.level1_loaded = True
        
        # Level 2
        if load_l2:
            level2 = self.load_level2(skill_path, context)
            if level2:
                manifest.level2 = level2
                manifest.level2_loaded = True
                # Update L1 with frontmatter data if available
                if level2.frontmatter.name and not load_l1:
                    manifest.name = level2.frontmatter.name
        
        # Level 3
        if scan_l3:
            manifest.level3 = self.scan_level3(skill_path)
            manifest.level3_scanned = True
        
        manifest.last_loaded = __import__('datetime').datetime.now()
        manifest.load_count += 1
        
        # Cache
        self._manifest_cache[manifest.name] = manifest
        if manifest.level2:
            self._level2_cache[manifest.name] = manifest.level2
        
        return manifest
    
    def _infer_category(self, skill_path: Path, yaml_data: Optional[Dict] = None) -> str:
        """Infer skill category from path and data"""
        category_keywords = {
            "data": ["csv", "json", "sql", "query", "database", "db", "table", "excel"],
            "web": ["http", "url", "crawl", "scrape", "fetch", "api", "web", "browser"],
            "file": ["read", "write", "file", "directory", "path", "folder"],
            "code": ["code", "analyze", "format", "lint", "syntax", "ast"],
            "finance": ["stock", "portfolio", "13f", "market", "price", "finance"],
            "image": ["image", "img", "png", "jpeg", "photo", "visual", "graph"],
            "text": ["text", "nlp", "parse", "extract", "summarize"],
        }
        
        # From yaml tags
        if yaml_data:
            tags = yaml_data.get("tags", [])
            if tags:
                for cat, keywords in category_keywords.items():
                    if any(kw in tags[0].lower() for kw in keywords):
                        return cat
        
        # From path
        path_str = str(skill_path).lower()
        for cat, keywords in category_keywords.items():
            if cat in path_str:
                return cat
            for kw in keywords:
                if kw in path_str:
                    return cat
        
        return "general"
    
    def get_cached_manifest(self, skill_name: str) -> Optional[SkillManifest]:
        """Get cached manifest by name"""
        return self._manifest_cache.get(skill_name)
    
    def clear_cache(self, skill_name: Optional[str] = None):
        """Clear cache for a skill or all skills"""
        if skill_name:
            self._manifest_cache.pop(skill_name, None)
            self._level2_cache.pop(skill_name, None)
        else:
            self._manifest_cache.clear()
            self._level2_cache.clear()


# Singleton instance
_loader_instance: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    """Get singleton skill loader"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = SkillLoader()
    return _loader_instance
