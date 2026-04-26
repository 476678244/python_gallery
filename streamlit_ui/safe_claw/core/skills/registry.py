"""Skill registry for SafeClaw"""

import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from streamlit_ui.safe_claw.core.skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)

class SkillRegistry:
    """Registry for managing skills"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.categories: Dict[str, List[str]] = {}
        
        logger.info("Skill registry initialized")
    
    def register_skill(self, skill: BaseSkill) -> bool:
        """Register a skill"""
        if skill.name in self.skills:
            logger.warning(f"Skill {skill.name} already registered, overwriting")
        
        self.skills[skill.name] = skill
        
        # Update category
        if skill.category not in self.categories:
            self.categories[skill.category] = []
        if skill.name not in self.categories[skill.category]:
            self.categories[skill.category].append(skill.name)
        
        logger.info(f"Registered skill: {skill.name}")
        return True
    
    def unregister_skill(self, skill_name: str) -> bool:
        """Unregister a skill"""
        if skill_name not in self.skills:
            logger.warning(f"Skill {skill_name} not found")
            return False
        
        skill = self.skills[skill_name]
        
        # Remove from category
        if skill.category in self.categories and skill_name in self.categories[skill.category]:
            self.categories[skill.category].remove(skill_name)
        
        # Remove from registry
        del self.skills[skill_name]
        
        logger.info(f"Unregistered skill: {skill_name}")
        return True
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name"""
        return self.skills.get(skill_name)
    
    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """Get all skills in a category"""
        if category not in self.categories:
            return []
        
        return [self.skills[name] for name in self.categories[category]]
    
    def get_all_skills(self) -> Dict[str, BaseSkill]:
        """Get all registered skills"""
        return self.skills.copy()
    
    def find_skills_for_query(self, query: str, min_confidence: float = 0.3) -> List[tuple[BaseSkill, float]]:
        """Find skills that can handle a query"""
        results = []
        
        for skill in self.skills.values():
            confidence = skill.can_handle(query)
            if confidence >= min_confidence:
                results.append((skill, confidence))
        
        # Sort by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_best_skill(self, query: str) -> Optional[BaseSkill]:
        """Get the best skill for a query"""
        candidates = self.find_skills_for_query(query)
        return candidates[0][0] if candidates else None
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get skill information"""
        skill = self.skills.get(skill_name)
        return skill.get_skill_info() if skill else None
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get registry information"""
        return {
            "total_skills": len(self.skills),
            "categories": {
                category: {
                    "count": len(skills),
                    "skills": skills
                }
                for category, skills in self.categories.items()
            },
            "skills": {
                name: skill.get_skill_info()
                for name, skill in self.skills.items()
            }
        }
    
    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """Search skills by name or description"""
        query_lower = query.lower()
        results = []
        
        for skill in self.skills.values():
            score = 0
            
            # Name match
            if query_lower in skill.name.lower():
                score += 10
            
            # Description match
            if query_lower in skill.description.lower():
                score += 5
            
            # Category match
            if query_lower in skill.category.lower():
                score += 3
            
            if score > 0:
                results.append({
                    "skill": skill.get_skill_info(),
                    "relevance_score": score
                })
        
        # Sort by score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get skill usage statistics"""
        stats = {
            "total_executions": 0,
            "skill_usage": {},
            "category_usage": {},
            "most_used": None,
            "least_used": None
        }
        
        for skill in self.skills.values():
            usage = skill.usage_count
            stats["total_executions"] += usage
            stats["skill_usage"][skill.name] = usage
            
            # Category usage
            if skill.category not in stats["category_usage"]:
                stats["category_usage"][skill.category] = 0
            stats["category_usage"][skill.category] += usage
        
        # Find most and least used
        if stats["skill_usage"]:
            most_used = max(stats["skill_usage"], key=stats["skill_usage"].get)
            least_used = min(stats["skill_usage"], key=stats["skill_usage"].get)
            stats["most_used"] = most_used
            stats["least_used"] = least_used
        
        return stats

def load_builtin_skills() -> SkillRegistry:
    """Load built-in skills with progressive discovery support"""
    registry = SkillRegistry()
    
    # Load built-in skills (hot cache)
    try:
        from streamlit_ui.safe_claw.core.skills.built_in.file_ops import (
            ReadFileSkill, WriteFileSkill, ListFilesSkill,
            DeleteFileSkill, CreateDirectorySkill
        )
        registry.register_skill(ReadFileSkill())
        registry.register_skill(WriteFileSkill())
        registry.register_skill(ListFilesSkill())
        registry.register_skill(DeleteFileSkill())
        registry.register_skill(CreateDirectorySkill())
        
        from streamlit_ui.safe_claw.core.skills.built_in.code_analyzer import (
            AnalyzeCodeSkill, CodeQualitySkill, CodeFormatterSkill
        )
        registry.register_skill(AnalyzeCodeSkill())
        registry.register_skill(CodeQualitySkill())
        registry.register_skill(CodeFormatterSkill())
        
        logger.info(f"Loaded {len(registry.skills)} built-in skills")
        
    except ImportError as e:
        logger.error(f"Failed to load built-in skills: {e}")
    
    return registry


def load_skills_with_discovery(query: str = None, external_skills_paths: List[Path] = None) -> tuple[SkillRegistry, Any]:
    """Load skills with progressive discovery system
    
    Args:
        query: Optional initial query to trigger skill discovery
        external_skills_paths: List of external skills directories to scan
        
    Returns:
        (SkillRegistry, DiscoveryResult) - registry and discovery result
    """
    from streamlit_ui.safe_claw.core.skills.discovery import SkillDiscovery, DiscoveryResult
    from streamlit_ui.safe_claw.core.skills.scanner import get_skill_scanner
    
    # Start with built-in skills
    registry = load_builtin_skills()
    
    # Initialize discovery system with external skills paths
    discovery = SkillDiscovery(registry, external_skills_paths=external_skills_paths)
    
    result = None
    if query:
        # Trigger progressive discovery
        result = discovery.find_skill(query)
        logger.info(f"Discovery result: {result.level.name} - {result.skill.name if result.skill else 'None'}")
    
    return registry, result


def auto_discover_skill(registry: SkillRegistry, query: str, external_skills_paths: List[Path] = None) -> Any:
    """Auto-discover and load a skill for a query
    
    This is the main entry point for lazy skill discovery.
    Example: auto_discover_skill(registry, "parse csv file")
    
    Args:
        registry: Skill registry to use
        query: Query to find skill for
        external_skills_paths: List of external skills directories to scan
    """
    from streamlit_ui.safe_claw.core.skills.discovery import SkillDiscovery
    from streamlit_ui.safe_claw.core.skills.scanner import get_skill_scanner
    
    # Initialize discovery system with external paths
    scanner = get_skill_scanner(external_skills_paths=external_skills_paths)
    discovery = SkillDiscovery(scanner, external_skills_paths=external_skills_paths)
    result = discovery.find_skill(query)
    
    if result.success:
        return result
    
    if result.missing_skill_hint:
        logger.warning(f"Missing skill detected: {result.missing_skill_hint['missing_skill']}")
    
    return None
