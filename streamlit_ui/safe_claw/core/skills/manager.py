"""Skills Manager for SafeClaw

Manages skills discovery, scanning, and execution context.
Extracted from official_integration.py for better separation of concerns.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from streamlit_ui.safe_claw.core.skills import (
    SkillDiscovery, SkillScanner, SkillExecutor,
    discover_skill, get_skill_scanner
)

logger = logging.getLogger(__name__)


class SkillsManager:
    """Manages skills system for SafeClaw"""

    def __init__(self, external_skills_paths: Optional[List[str]] = None):
        """
        Initialize skills manager
        
        Args:
            external_skills_paths: List of external paths to scan for skills
        """
        self.external_skills_paths = [Path(p) for p in external_skills_paths] if external_skills_paths else []
        
        # Initialize skills system components
        self.skill_scanner = get_skill_scanner(external_skills_paths=self.external_skills_paths)
        self.skill_discovery = SkillDiscovery(self.skill_scanner, external_skills_paths=self.external_skills_paths)
        self.skill_executor = SkillExecutor()
        
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
        """Get skills paths for DeepAgents including external paths
        
        Returns:
            List of skill directory paths as strings
        """
        try:
            # Get skills directory paths relative to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            skills_dir = project_root / "streamlit_ui" / "skills"

            paths = []
            
            # 1. Local skills from streamlit_ui/skills
            if skills_dir.exists():
                # Iterate through all directories to find SKILL.md files
                for skill_path in skills_dir.rglob("SKILL.md"):
                    # Get the parent directory of SKILL.md (the actual skill directory)
                    skill_dir = skill_path.parent

                    # Convert to relative path from project root
                    rel_path = skill_dir.relative_to(project_root)

                    # Convert to POSIX format and add trailing slash
                    path_str = str(rel_path).replace("\\", "/") + "/"

                    if path_str not in paths:
                        paths.append(path_str)

            # 2. External skills paths from config
            if self.external_skills_paths:
                for ext_path in self.external_skills_paths:
                    if ext_path.exists():
                        # Find SKILL.md files in external path
                        for skill_path in ext_path.rglob("SKILL.md"):
                            skill_dir = skill_path.parent
                            
                            # Use absolute path for external skills
                            path_str = str(skill_dir).replace("\\", "/") + "/"
                            
                            if path_str not in paths:
                                paths.append(path_str)

            logger.info(f"Found {len(paths)} skills paths from SKILL.md files")
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

    def get_enabled_skills(self, enabled_skill_names: Optional[List[str]] = None) -> List[str]:
        """Get list of enabled skills, optionally filtered by user selection
        
        This method can be used with the Skill Tree component to get only
        the skills that the user has enabled through the tree interface.
        
        Args:
            enabled_skill_names: Optional list of skill names to filter by.
                If None, returns all user-invocable skills.
                If empty list, returns no skills.
                
        Returns:
            List of enabled skill names
        """
        if not self.skill_scanner.loaded:
            self.skill_scanner.scan_all_skills()
        
        # If no filter provided, return all user-invocable skills
        if enabled_skill_names is None:
            return self.get_available_skills()
        
        # If empty list provided, user disabled all skills
        if not enabled_skill_names:
            return []
        
        # Filter to only include valid, user-invocable skills
        enabled_set = set(enabled_skill_names)
        filtered = []
        
        for name in enabled_skill_names:
            entry = self.skill_scanner.index.get(name)
            if entry and entry.user_invocable:
                filtered.append(name)
            else:
                logger.warning(f"Skill '{name}' not found or not user-invocable, skipping")
        
        logger.info(f"Returning {len(filtered)} enabled skills out of {len(enabled_set)} requested")
        return filtered

    def get_filtered_skills_paths(self, enabled_skill_names: Optional[List[str]] = None) -> List[str]:
        """Get skills paths filtered by enabled skills
        
        Args:
            enabled_skill_names: Optional list of skill names to filter by.
                Only paths for these skills will be returned.
                
        Returns:
            List of skill directory paths as strings
        """
        all_paths = self.get_skills_paths()
        
        # If no filter, return all paths
        if enabled_skill_names is None:
            return all_paths
        
        # If empty list, return no paths
        if not enabled_skill_names:
            return []
        
        # Filter paths to only include enabled skills
        enabled_set = set(enabled_skill_names)
        filtered_paths = []
        
        for path in all_paths:
            # Extract skill name from path (last folder name before trailing slash)
            skill_name = Path(path).name
            if skill_name in enabled_set:
                filtered_paths.append(path)
        
        logger.info(f"Filtered to {len(filtered_paths)} skill paths from {len(all_paths)} total")
        return filtered_paths
