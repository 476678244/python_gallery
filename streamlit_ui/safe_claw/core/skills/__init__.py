"""SafeClaw Skills System - Claude Code Spec Compatible

3-Level Progressive Disclosure:
- Level 1: name + description (~100 tokens, always loaded)
- Level 2: SKILL.md body content (~5k tokens, loaded on trigger)
- Level 3: scripts + reference files (unlimited, loaded on demand)

Reference: https://code.claude.com/docs/llms.txt
"""

# Core manifest and loading
from streamlit_ui.safe_claw.core.skills.manifest import (
    SkillManifest,
    SkillLevel1,
    SkillLevel2,
    SkillLevel3,
    SkillFrontmatter,
    SkillContext,
    SkillEffort,
    parse_skill_md,
)

from streamlit_ui.safe_claw.core.skills.loader import (
    SkillLoader,
    LoadContext,
    get_skill_loader,
)

from streamlit_ui.safe_claw.core.skills.executor import (
    SkillExecutor,
    ExecutionContext,
    ToolPermissionManager,
)

# Scanning and discovery
from streamlit_ui.safe_claw.core.skills.scanner import (
    SkillScanner,
    SkillIndexEntry,
    get_skill_scanner,
)

from streamlit_ui.safe_claw.core.skills.matcher import (
    SemanticMatcher,
    MatchResult,
    get_semantic_matcher,
    KeywordExpander,
    BM25,
)

from streamlit_ui.safe_claw.core.skills.discovery import (
    SkillDiscovery,
    DiscoveryResult,
    DiscoveryLevel,
    discover_skill,
)

from streamlit_ui.safe_claw.core.skills.manager import SkillsManager

# Legacy support
from streamlit_ui.safe_claw.core.skills.base_skill import (
    BaseSkill,
    FileSkill,
    CodeSkill,
    AnalysisSkill,
)

from streamlit_ui.safe_claw.core.skills.registry import (
    SkillRegistry,
    load_builtin_skills,
    load_skills_with_discovery,
    auto_discover_skill,
)

__all__ = [
    # Manifest & Progressive Disclosure
    "SkillManifest",
    "SkillLevel1",
    "SkillLevel2",
    "SkillLevel3",
    "SkillFrontmatter",
    "SkillContext",
    "SkillEffort",
    "parse_skill_md",
    # Loading & Execution
    "SkillLoader",
    "LoadContext",
    "SkillExecutor",
    "ExecutionContext",
    "ToolPermissionManager",
    "get_skill_loader",
    # Discovery
    "SkillScanner",
    "SkillIndexEntry",
    "SemanticMatcher",
    "MatchResult",
    "SkillDiscovery",
    "DiscoveryResult",
    "DiscoveryLevel",
    "discover_skill",
    "get_skill_scanner",
    "get_semantic_matcher",
    "SkillsManager",
    # Utilities
    "KeywordExpander",
    "BM25",
    # Legacy
    "BaseSkill",
    "FileSkill",
    "CodeSkill",
    "AnalysisSkill",
    "SkillRegistry",
    "load_builtin_skills",
    "load_skills_with_discovery",
    "auto_discover_skill",
]
