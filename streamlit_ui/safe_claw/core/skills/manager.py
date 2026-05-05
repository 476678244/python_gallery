"""Skills Manager for SafeClaw

Manages skills discovery, scanning, and execution context.
Extracted from official_integration.py for better separation of concerns.
"""

import logging
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

from streamlit_ui.safe_claw.core.skills import (
    SkillDiscovery, SkillScanner, SkillExecutor,
    discover_skill, get_skill_scanner
)

logger = logging.getLogger(__name__)


class SkillsManager:
    """Manages skills system for SafeClaw
    
    This manager maintains the enabled skills state, which is synced with
    the skill tree UI. Backend owns the state; frontend reads/writes to it.
    """

    def __init__(self, external_skills_paths: Optional[List[str]] = None):
        """
        Initialize skills manager
        
        Args:
            external_skills_paths: List of external paths to scan for skills.
                If None, automatically discovers linked_skills at project root.
        """
        if external_skills_paths:
            self.external_skills_paths = [Path(p) for p in external_skills_paths]
        else:
            # Auto-discover linked_skills at project root
            self.external_skills_paths = []
            project_root = Path(__file__).parent.parent.parent.parent.parent
            linked_skills_path = project_root / "linked_skills"
            if linked_skills_path.exists():
                self.external_skills_paths.append(linked_skills_path)
                logger.info(f"Auto-discovered linked_skills: {linked_skills_path}")
        
        # Initialize skills system components
        self.skill_scanner = get_skill_scanner(external_skills_paths=self.external_skills_paths)
        self.skill_discovery = SkillDiscovery(self.skill_scanner, external_skills_paths=self.external_skills_paths)
        self.skill_executor = SkillExecutor()
        
        # Enabled skills state - backend owns this
        self._enabled_skills: Optional[Set[str]] = None
        
        logger.info(f"SkillsManager initialized with {len(self.external_skills_paths)} external paths")

    def get_skill_scanner(self) -> SkillScanner:
        """Get the skill scanner"""
        return self.skill_scanner

    def get_skill_discovery(self) -> SkillDiscovery:
        """Get the skill discovery"""
        return self.skill_discovery

    def get_skill_executor(self) -> SkillExecutor:
        """Get the skill executor"""
        return self.skill_executor

    def get_skills_paths(self) -> List[str]:
        """Get skills paths for DeepAgents - progressive/iterative discovery
        
        All directories containing SKILL.md files are considered skills.
        Scans multiple sources iteratively:
        1. linked_skills/ - symlinked skill collections
        2. streamlit_ui/skills/ - local skills
        3. External skills paths from configuration
        
        Returns:
            List of skill directory paths as strings
        """
        try:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            paths = []
            scanned_sources = []
            
            # Define all skill sources to scan iteratively
            skill_sources = []
            
            # 1. linked_skills/ at project root - support symlinks
            linked_skills = project_root / "linked_skills"
            if linked_skills.exists() or linked_skills.is_symlink():
                skill_sources.append(("linked_skills", linked_skills, True))
            
            # 2. Local streamlit_ui/skills
            local_skills = project_root / "streamlit_ui" / "skills"
            if local_skills.exists():
                skill_sources.append(("local_skills", local_skills, False))
            
            # 3. External skills paths - support symlinks
            for ext_path in self.external_skills_paths:
                if ext_path.exists() or ext_path.is_symlink():
                    skill_sources.append(("external", ext_path, True))
            
            # Iteratively scan each source for SKILL.md files
            for source_name, source_path, use_absolute in skill_sources:
                skill_count = 0
                
                # Handle symlinked source directories by resolving them
                scan_path = source_path
                if source_path.is_symlink():
                    try:
                        scan_path = source_path.resolve()
                        logger.info(f"Resolved symlink {source_path} -> {scan_path}")
                    except Exception as e:
                        logger.warning(f"Failed to resolve symlink {source_path}: {e}")
                        continue
                
                if not scan_path.exists():
                    logger.warning(f"Skill source does not exist: {scan_path}")
                    continue
                
                # For linked_skills, iterate through collection subdirs (which may be symlinks)
                if source_name == "linked_skills" and scan_path.is_dir():
                    for collection_dir in scan_path.iterdir():
                        # Support both regular dirs and symlinked collection dirs
                        if collection_dir.is_dir() or collection_dir.is_symlink():
                            collection_scan_path = collection_dir
                            # Resolve symlinked collection dir
                            if collection_dir.is_symlink():
                                try:
                                    collection_scan_path = collection_dir.resolve()
                                    logger.info(f"  Scanning symlinked collection: {collection_dir.name} -> {collection_scan_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to resolve collection symlink {collection_dir}: {e}")
                                    continue
                            
                            # Scan this collection for SKILL.md files
                            if collection_scan_path.exists():
                                for skill_md in collection_scan_path.rglob("SKILL.md"):
                                    skill_dir = skill_md.parent
                                    # Use absolute path for symlinked skills
                                    path_str = str(skill_dir.resolve()).replace("\\", "/") + "/"
                                    
                                    if path_str not in paths:
                                        paths.append(path_str)
                                        skill_count += 1
                else:
                    # Progressive scan: find all SKILL.md files recursively
                    for skill_md in scan_path.rglob("SKILL.md"):
                        skill_dir = skill_md.parent
                        
                        if use_absolute:
                            # Use absolute path for external/linked skills
                            path_str = str(skill_dir.resolve()).replace("\\", "/") + "/"
                        else:
                            # Use relative path for local skills
                            try:
                                rel_path = skill_dir.relative_to(project_root)
                                path_str = str(rel_path).replace("\\", "/") + "/"
                            except ValueError:
                                path_str = str(skill_dir).replace("\\", "/") + "/"
                        
                        if path_str not in paths:
                            paths.append(path_str)
                            skill_count += 1
                
                if skill_count > 0:
                    scanned_sources.append(f"{source_name}({skill_count})")
            
            logger.info(f"Progressive scan found {len(paths)} skills from: {', '.join(scanned_sources)}")
            return paths

        except Exception as e:
            logger.error(f"Error getting skills paths: {e}")
            return []

    def get_available_skills(self) -> List[str]:
        """Get list of available skill names for DeepAgents skills parameter
        
        Returns:
            List of user-invocable skill names
        """
        try:
            if not self.skill_scanner.loaded:
                self.skill_scanner.scan_all_skills()

            # Get all skill names from the scanner
            skill_names = list(self.skill_scanner.index.keys())

            # Filter to only include user-invocable skills
            user_invocable_skills = []
            for name in skill_names:
                entry = self.skill_scanner.index.get(name)
                if entry and entry.user_invocable:
                    user_invocable_skills.append(name)

            logger.info(f"Found {len(user_invocable_skills)} user-invocable skills out of {len(skill_names)} total")
            return user_invocable_skills

        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            return []

    def estimate_skills_tokens(self, skills_paths: List[str]) -> int:
        """Estimate tokens consumed by skills metadata (Level 1 only)
        
        Args:
            skills_paths: List of skill paths
            
        Returns:
            Estimated token count
        """
        # Level 1 metadata only ~100 tokens per skill
        return len(skills_paths) * 100

    def scan_all_skills(self):
        """Force scan all skills"""
        self.skill_scanner.scan_all_skills()
        logger.info("Scanned all skills")

    def get_skill_count(self) -> int:
        """Get total number of discovered skills"""
        if not self.skill_scanner.loaded:
            self.skill_scanner.scan_all_skills()
        return len(self.skill_scanner.index)

    def get_skill_categories(self) -> Dict[str, int]:
        """Get skills grouped by category
        
        Returns:
            Dictionary mapping category names to skill counts
        """
        if not self.skill_scanner.loaded:
            self.skill_scanner.scan_all_skills()

        categories = {}
        for entry in self.skill_scanner.index.values():
            cat = entry.category or "general"
            categories[cat] = categories.get(cat, 0) + 1
        
        return categories

    def set_enabled_skills(self, enabled_skill_names: List[str]) -> None:
        """Set the enabled skills state
        
        This is called by the frontend (skill tree) to update which
        skills are enabled. Backend owns this state.
        
        Args:
            enabled_skill_names: List of skill names to enable
        """
        self._enabled_skills = set(enabled_skill_names) if enabled_skill_names else set()
        logger.info(f"Set {len(self._enabled_skills)} enabled skills")

    def get_enabled_skills(self) -> List[str]:
        """Get list of enabled skills based on stored state
        
        Returns skills filtered by the enabled set. If no enabled set
        has been configured via set_enabled_skills(), returns all
        user-invocable skills.
        
        Returns:
            List of enabled skill names
        """
        if not self.skill_scanner.loaded:
            self.skill_scanner.scan_all_skills()
        
        # Get all available user-invocable skills
        all_skills = self.get_available_skills()
        
        # If no enabled set configured, return all skills
        if self._enabled_skills is None:
            logger.info(f"No skill tree config, returning all {len(all_skills)} skills")
            return all_skills
        
        # If empty set, user disabled all skills
        if not self._enabled_skills:
            return []
        
        # Filter to only enabled skills
        filtered = [name for name in all_skills if name in self._enabled_skills]
        logger.info(f"Skill Tree: {len(filtered)} enabled out of {len(all_skills)} total skills")
        return filtered

    def get_enabled_skills_state(self) -> Optional[Set[str]]:
        """Get the raw enabled skills state
        
        Used by frontend to sync skill tree UI with backend state.
        
        Returns:
            Set of enabled skill names, or None if not configured
        """
        return self._enabled_skills.copy() if self._enabled_skills is not None else None

    def get_filtered_skills_paths(self) -> List[str]:
        """Get skills paths filtered by enabled skills state
        
        Uses the internal enabled skills state set via set_enabled_skills().
        If no state has been set, returns all skill paths.
        
        Returns:
            List of skill directory paths as strings
        """
        all_paths = self.get_skills_paths()
        
        # Get enabled skills (uses internal state)
        enabled_skills = self.get_enabled_skills()
        
        # If no filter applied (all skills enabled), return all paths
        if len(enabled_skills) == len(self.get_available_skills()):
            return all_paths
        
        # Filter paths to only include enabled skills
        enabled_set = set(enabled_skills)
        filtered_paths = []
        
        for path in all_paths:
            # Extract skill name from path (last folder name before trailing slash)
            skill_name = Path(path).name
            if skill_name in enabled_set:
                filtered_paths.append(path)
        
        logger.info(f"Filtered to {len(filtered_paths)} skill paths from {len(all_paths)} total")
        return filtered_paths
