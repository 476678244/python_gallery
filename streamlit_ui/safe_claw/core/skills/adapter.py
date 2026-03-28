"""Tool adapter for integrating skills with LangGraph"""

import logging
from typing import Dict, Any, List, Optional, Callable
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry
from streamlit_ui.safe_claw.core.skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)

class SkillTool(BaseTool):
    """LangGraph tool adapter for skills"""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    skill: BaseSkill = Field(description="Underlying skill")
    
    def __init__(self, skill: BaseSkill):
        super().__init__(
            name=skill.name,
            description=skill.description,
            skill=skill
        )
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Run the skill tool"""
        try:
            # Validate parameters
            is_valid, error_msg = self.skill.validate_parameters(kwargs)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            # Execute skill
            result = self.skill.execute(**kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Error executing skill {self.skill.name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async run the skill tool"""
        return self._run(**kwargs)

class SkillAdapter:
    """Adapter for converting skills to LangGraph tools"""
    
    def __init__(self, skill_registry: SkillRegistry):
        self.skill_registry = skill_registry
        self.tools: Dict[str, SkillTool] = {}
        
        logger.info("Skill adapter initialized")
    
    def create_tool(self, skill_name: str) -> Optional[SkillTool]:
        """Create a tool from a skill"""
        skill = self.skill_registry.get_skill(skill_name)
        if not skill:
            logger.error(f"Skill not found: {skill_name}")
            return None
        
        tool = SkillTool(skill)
        self.tools[skill_name] = tool
        
        logger.info(f"Created tool for skill: {skill_name}")
        return tool
    
    def create_all_tools(self) -> Dict[str, SkillTool]:
        """Create tools for all registered skills"""
        tools = {}
        
        for skill_name in self.skill_registry.get_all_skills():
            tool = self.create_tool(skill_name)
            if tool:
                tools[skill_name] = tool
        
        logger.info(f"Created {len(tools)} tools")
        return tools
    
    def get_tool(self, skill_name: str) -> Optional[SkillTool]:
        """Get a tool by skill name"""
        return self.tools.get(skill_name)
    
    def get_all_tools(self) -> Dict[str, SkillTool]:
        """Get all tools"""
        return self.tools.copy()
    
    def get_tools_for_query(self, query: str, min_confidence: float = 0.3) -> List[SkillTool]:
        """Get tools that can handle a query"""
        skills = self.skill_registry.find_skills_for_query(query, min_confidence)
        tools = []
        
        for skill, confidence in skills:
            tool = self.get_tool(skill.name)
            if not tool:
                tool = self.create_tool(skill.name)
            if tool:
                tools.append((tool, confidence))
        
        # Sort by confidence
        tools.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, _ in tools]
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for LangGraph"""
        schemas = []
        
        for tool in self.tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.skill.get_parameters()
            }
            schemas.append(schema)
        
        return schemas
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool directly"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}
        
        return tool._run(**parameters)
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information"""
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "skill_info": tool.skill.get_skill_info(),
            "parameters": tool.skill.get_parameters()
        }
    
    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search tools by name or description"""
        query_lower = query.lower()
        results = []
        
        for tool in self.tools.values():
            score = 0
            
            # Name match
            if query_lower in tool.name.lower():
                score += 10
            
            # Description match
            if query_lower in tool.description.lower():
                score += 5
            
            # Category match
            if query_lower in tool.skill.category.lower():
                score += 3
            
            if score > 0:
                results.append({
                    "tool": self.get_tool_info(tool.name),
                    "relevance_score": score
                })
        
        # Sort by score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        stats = {
            "total_tools": len(self.tools),
            "total_executions": 0,
            "tool_usage": {},
            "category_usage": {}
        }
        
        for tool in self.tools.values():
            usage = tool.skill.usage_count
            stats["total_executions"] += usage
            stats["tool_usage"][tool.name] = usage
            
            # Category usage
            category = tool.skill.category
            if category not in stats["category_usage"]:
                stats["category_usage"][category] = 0
            stats["category_usage"][category] += usage
        
        return stats

class ToolExecutor:
    """Tool execution manager with safety checks"""
    
    def __init__(self, skill_adapter: SkillAdapter, safety_checker=None):
        self.skill_adapter = skill_adapter
        self.safety_checker = safety_checker
        
        logger.info("Tool executor initialized")
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    session_id: str = None) -> Dict[str, Any]:
        """Execute a tool with safety checks"""
        try:
            # Safety check if available
            if self.safety_checker and session_id:
                tool_call_str = f"{tool_name}({parameters})"
                is_safe, safety_msg, safety_result = self.safety_checker.check_tool_call(
                    tool_name, parameters, session_id
                )
                
                if not is_safe:
                    return {
                        "success": False,
                        "error": f"Tool execution blocked: {safety_msg}",
                        "safety_result": safety_result
                    }
                
                if safety_result.get("requires_confirmation"):
                    return {
                        "success": False,
                        "error": f"Tool execution requires confirmation: {safety_msg}",
                        "safety_result": safety_result,
                        "requires_confirmation": True
                    }
            
            # Execute tool
            result = self.skill_adapter.execute_tool(tool_name, parameters)
            
            # Log execution
            logger.info(f"Executed tool {tool_name} with result: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        tools = []
        
        for tool_name, tool in self.skill_adapter.get_all_tools().items():
            tools.append({
                "name": tool_name,
                "description": tool.description,
                "category": tool.skill.category,
                "parameters": tool.skill.get_parameters()
            })
        
        return tools
    
    def suggest_tools(self, query: str) -> List[Dict[str, Any]]:
        """Suggest tools for a query"""
        tools = self.skill_adapter.get_tools_for_query(query)
        
        suggestions = []
        for tool in tools:
            suggestions.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.skill.category,
                "confidence": tool.skill.can_handle(query)
            })
        
        return suggestions
