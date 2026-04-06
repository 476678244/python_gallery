"""Skill Manifest - 3-Level Progressive Disclosure System

Implements the Claude Code skills standard with progressive disclosure:
- Level 1: name + description (~100 tokens, always loaded)
- Level 2: SKILL.md body content (~5k tokens, loaded on trigger)
- Level 3: scripts + reference files (unlimited, loaded on demand)

Reference: https://code.claude.com/docs/llms.txt
"""

import re
import yaml
import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class SkillContext(Enum):
    """Skill execution context"""
    INLINE = "inline"      # Run in current context
    FORK = "fork"          # Run in isolated subagent


class SkillEffort(Enum):
    """Skill effort level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


@dataclass
class SkillFrontmatter:
    """YAML frontmatter from SKILL.md
    
    All fields are optional per the Claude Code spec.
    """
    # Identity
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Invocation control
    disable_model_invocation: bool = False  # Prevent Claude from auto-loading
    user_invocable: bool = True             # Show in / menu
    
    # Arguments
    argument_hint: Optional[str] = None     # e.g., "[filename] [format]"
    
    # Tool permissions
    allowed_tools: List[str] = field(default_factory=list)
    
    # Model configuration
    model: Optional[str] = None
    effort: Optional[SkillEffort] = None
    
    # Execution context
    context: SkillContext = SkillContext.INLINE
    agent: Optional[str] = None  # Subagent type: Explore, Plan, general-purpose
    
    # Hooks (skill-lifecycle specific)
    hooks: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillFrontmatter":
        """Parse frontmatter dict into structured object"""
        if not data:
            return cls()
            
        # Parse effort enum
        effort = None
        effort_str = data.get("effort")
        if effort_str:
            try:
                effort = SkillEffort(effort_str.lower())
            except ValueError:
                logger.warning(f"Unknown effort level: {effort_str}")
        
        # Parse context enum
        context = SkillContext.INLINE
        context_str = data.get("context")
        if context_str:
            try:
                context = SkillContext(context_str.lower())
            except ValueError:
                logger.warning(f"Unknown context: {context_str}")
        
        # Parse allowed_tools - can be string or list
        allowed_tools = data.get("allowed_tools", [])
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split(",")]
        
        return cls(
            name=data.get("name"),
            description=data.get("description"),
            disable_model_invocation=data.get("disable_model_invocation", False),
            user_invocable=data.get("user_invocable", True),
            argument_hint=data.get("argument_hint"),
            allowed_tools=allowed_tools,
            model=data.get("model"),
            effort=effort,
            context=context,
            agent=data.get("agent"),
            hooks=data.get("hooks", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "disable_model_invocation": self.disable_model_invocation,
            "user_invocable": self.user_invocable,
            "argument_hint": self.argument_hint,
            "allowed_tools": self.allowed_tools,
            "model": self.model,
            "effort": self.effort.value if self.effort else None,
            "context": self.context.value,
            "agent": self.agent,
            "hooks": self.hooks,
        }


@dataclass
class SkillLevel1:
    """Level 1: Minimal metadata (~100 tokens)
    
    Always loaded at startup for all skills.
    Used for: skill listing, auto-invocation decisions
    """
    name: str
    description: str
    path: Path
    version: str = "1.0.0"
    category: str = "general"
    
    # Invocation control (from frontmatter)
    disable_model_invocation: bool = False
    user_invocable: bool = True
    auto_trigger: bool = False
    
    # Quick match data
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    
    def estimate_tokens(self) -> int:
        """Estimate token count for Level 1"""
        # Rough estimate: ~4 chars per token
        text = f"{self.name} {self.description} {' '.join(self.tags)}"
        return len(text) // 4


@dataclass
class SkillLevel2:
    """Level 2: SKILL.md body content (~5k tokens)
    
    Loaded when skill is triggered (manually or auto).
    Contains: full instructions, markdown content
    """
    # Raw content
    raw_content: str = ""                     # Full SKILL.md content
    frontmatter_text: str = ""                # YAML frontmatter as text
    body_content: str = ""                    # Markdown body (after frontmatter)
    
    # Parsed frontmatter
    frontmatter: SkillFrontmatter = field(default_factory=SkillFrontmatter)
    
    # Content analysis
    referenced_files: List[str] = field(default_factory=list)  # [file.md] references
    has_dynamic_injection: bool = False        # Contains !`command` syntax
    
    def estimate_tokens(self) -> int:
        """Estimate token count for Level 2"""
        return len(self.body_content) // 4
    
    def get_effective_description(self) -> str:
        """Get description from frontmatter or fallback to first paragraph"""
        if self.frontmatter.description:
            return self.frontmatter.description
        
        # Extract first paragraph from body
        lines = self.body_content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:200]
        return ""


@dataclass
class SkillLevel3:
    """Level 3: Supporting files (unlimited, on-demand)
    
    Loaded only when explicitly referenced.
    Contains: scripts, templates, examples, reference docs
    """
    # Available support files
    scripts: Dict[str, Path] = field(default_factory=dict)      # script_name -> path
    templates: Dict[str, Path] = field(default_factory=dict)    # template_name -> path
    examples: Dict[str, Path] = field(default_factory=dict)     # example_name -> path
    references: Dict[str, Path] = field(default_factory=dict)    # reference_name -> path
    
    # Cached content (loaded on demand)
    _cache: Dict[str, str] = field(default_factory=dict, repr=False)
    
    def get_file(self, name: str) -> Optional[Path]:
        """Get file path by name"""
        for collection in [self.scripts, self.templates, self.examples, self.references]:
            if name in collection:
                return collection[name]
        return None
    
    def read_file(self, name: str) -> Optional[str]:
        """Read file content (with caching)"""
        if name in self._cache:
            return self._cache[name]
        
        path = self.get_file(name)
        if not path or not path.exists():
            return None
        
        try:
            content = path.read_text(encoding="utf-8")
            self._cache[name] = content
            return content
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None
    
    def estimate_tokens(self) -> int:
        """Estimate total tokens (only cached content)"""
        total = 0
        for content in self._cache.values():
            total += len(content) // 4
        return total


@dataclass
class SkillManifest:
    """Complete skill manifest with 3-level progressive disclosure
    
    Follows Claude Code skills specification:
    https://code.claude.com/docs/llms.txt
    """
    # Identity
    name: str
    path: Path
    
    # Three disclosure levels
    level1: SkillLevel1 = field(default=None)
    level2: SkillLevel2 = field(default=None)
    level3: SkillLevel3 = field(default=None)
    
    # Loading state
    level1_loaded: bool = False
    level2_loaded: bool = False
    level3_scanned: bool = False  # L3 file list known, content not loaded
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_loaded: Optional[datetime] = None
    load_count: int = 0
    
    def __post_init__(self):
        if self.level1 is None:
            self.level1 = SkillLevel1(
                name=self.name,
                description="",
                path=self.path
            )
    
    @property
    def description(self) -> str:
        """Get skill description (from L2 if available, else L1)"""
        if self.level2:
            desc = self.level2.get_effective_description()
            if desc:
                return desc
        return self.level1.description if self.level1 else ""
    
    @property
    def category(self) -> str:
        """Get skill category"""
        return self.level1.category if self.level1 else "general"
    
    @property
    def can_auto_invoke(self) -> bool:
        """Check if Claude can auto-invoke this skill"""
        if self.level2 and self.level2.frontmatter:
            return not self.level2.frontmatter.disable_model_invocation
        return True
    
    @property
    def can_user_invoke(self) -> bool:
        """Check if user can invoke this skill via /"""
        if self.level2 and self.level2.frontmatter:
            return self.level2.frontmatter.user_invocable
        return True
    
    @property
    def allowed_tools(self) -> List[str]:
        """Get allowed tools list"""
        if self.level2 and self.level2.frontmatter:
            return self.level2.frontmatter.allowed_tools
        return []
    
    @property
    def context(self) -> SkillContext:
        """Get execution context"""
        if self.level2 and self.level2.frontmatter:
            return self.level2.frontmatter.context
        return SkillContext.INLINE
    
    def get_total_tokens(self) -> int:
        """Get total loaded token count"""
        total = 0
        if self.level1_loaded and self.level1:
            total += self.level1.estimate_tokens()
        if self.level2_loaded and self.level2:
            total += self.level2.estimate_tokens()
        if self.level3:
            total += self.level3.estimate_tokens()
        return total
    
    def to_dict(self, include_level1=True, include_level2=False, include_level3=False) -> Dict[str, Any]:
        """Export manifest to dictionary"""
        result = {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "category": self.category,
            "can_auto_invoke": self.can_auto_invoke,
            "can_user_invoke": self.can_user_invoke,
            "context": self.context.value,
            "level1_loaded": self.level1_loaded,
            "level2_loaded": self.level2_loaded,
            "level3_scanned": self.level3_scanned,
            "total_tokens": self.get_total_tokens(),
        }
        
        if include_level1 and self.level1:
            result["level1"] = {
                "name": self.level1.name,
                "description": self.level1.description,
                "category": self.level1.category,
                "tags": self.level1.tags,
                "aliases": self.level1.aliases,
                "tokens": self.level1.estimate_tokens(),
            }
        
        if include_level2 and self.level2:
            result["level2"] = {
                "frontmatter": self.level2.frontmatter.to_dict(),
                "has_dynamic_injection": self.level2.has_dynamic_injection,
                "referenced_files": self.level2.referenced_files,
                "tokens": self.level2.estimate_tokens(),
            }
        
        if include_level3 and self.level3:
            result["level3"] = {
                "scripts": list(self.level3.scripts.keys()),
                "templates": list(self.level3.templates.keys()),
                "examples": list(self.level3.examples.keys()),
                "references": list(self.level3.references.keys()),
            }
        
        return result


# Regex for dynamic context injection: !`command`
DYNAMIC_INJECTION_PATTERN = re.compile(r'!`([^`]+)`')

# Regex for file references: [name](path) or [path]
FILE_REFERENCE_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\[([^\]]+\.md)\]')


def parse_skill_md(content: str, skill_path: Path) -> SkillLevel2:
    """Parse SKILL.md content into Level 2 data
    
    Handles:
    - YAML frontmatter extraction
    - Dynamic injection detection (!`command`)
    - File reference extraction ([file.md])
    """
    frontmatter_text = ""
    body_content = content
    frontmatter_dict = {}
    
    # Extract frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            body_content = parts[2].strip()
            try:
                frontmatter_dict = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
    
    # Parse frontmatter
    frontmatter = SkillFrontmatter.from_dict(frontmatter_dict)
    
    # Detect dynamic injection
    has_dynamic_injection = bool(DYNAMIC_INJECTION_PATTERN.search(body_content))
    
    # Extract file references
    referenced_files = []
    for match in FILE_REFERENCE_PATTERN.finditer(body_content):
        # match.group(1) and group(2) for [name](path) format
        # match.group(3) for [path] format
        ref = match.group(2) or match.group(3)
        if ref:
            referenced_files.append(ref)
    
    return SkillLevel2(
        raw_content=content,
        frontmatter_text=frontmatter_text,
        body_content=body_content,
        frontmatter=frontmatter,
        referenced_files=referenced_files,
        has_dynamic_injection=has_dynamic_injection,
    )
