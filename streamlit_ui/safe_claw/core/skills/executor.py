"""Skill Executor - Subagent execution and tool permission control

Handles:
- Tool permission filtering (allowed-tools from frontmatter)
- Subagent execution (context: fork)
- Variable substitution at execution time
- Permission validation
"""

import re
import yaml
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field

from safe_claw.core.skills.manifest import SkillManifest, SkillContext, SkillFrontmatter
from safe_claw.core.skills.loader import LoadContext, SkillLoader

logger = logging.getLogger(__name__)


class ToolPermission(Enum):
    """Permission levels for tools"""
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_CONFIRMATION = "confirmation"


@dataclass
class ToolPermissionRule:
    """Single tool permission rule"""
    pattern: str  # Tool name or pattern with *
    permission: ToolPermission
    
    def matches(self, tool_name: str) -> bool:
        """Check if rule matches a tool name"""
        if self.pattern.endswith("*"):
            prefix = self.pattern[:-1]
            return tool_name.startswith(prefix)
        return tool_name == self.pattern


class ToolPermissionManager:
    """Manages tool permissions for skills
    
    Parses allowed-tools from frontmatter:
    - Tool names: "Read", "Grep", "Glob"
    - Patterns: "Bash(git *)" - git subcommands allowed
    - All tools with "*"
    """
    
    def __init__(self, allowed_tools: List[str]):
        self.allowed_patterns: List[ToolPermissionRule] = []
        self.denied_patterns: List[ToolPermissionRule] = []
        self.allow_all = False
        
        self._parse_patterns(allowed_tools)
    
    def _parse_patterns(self, allowed_tools: List[str]):
        """Parse allowed-tools list into rules"""
        if not allowed_tools:
            # No restriction - allow all
            self.allow_all = True
            return
        
        for tool_spec in allowed_tools:
            tool_spec = tool_spec.strip()
            if not tool_spec:
                continue
            
            # Check for Bash(pattern) format
            bash_match = re.match(r'Bash\(([^)]+)\)', tool_spec)
            if bash_match:
                # Bash with restrictions
                bash_pattern = bash_match.group(1).strip()
                self.allowed_patterns.append(ToolPermissionRule(
                    pattern=f"Bash:{bash_pattern}",
                    permission=ToolPermission.ALLOWED
                ))
            else:
                # Simple tool name
                if tool_spec == "*":
                    self.allow_all = True
                    return
                self.allowed_patterns.append(ToolPermissionRule(
                    pattern=tool_spec,
                    permission=ToolPermission.ALLOWED
                ))
    
    def can_use_tool(self, tool_name: str, tool_args: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
        """Check if a tool can be used
        
        Returns: (is_allowed, reason_if_denied)
        """
        if self.allow_all:
            return True, None
        
        # Check Bash patterns
        if tool_name == "Bash" and tool_args:
            command = tool_args.get("command", "")
            # Extract first word (command)
            cmd_parts = command.strip().split()
            if cmd_parts:
                base_cmd = cmd_parts[0]
                bash_tool_name = f"Bash:{base_cmd}"
                
                # Check if any Bash pattern matches
                for rule in self.allowed_patterns:
                    if rule.pattern.startswith("Bash:"):
                        pattern_cmd = rule.pattern[5:]  # Remove "Bash:" prefix
                        if pattern_cmd.endswith("*"):
                            if base_cmd.startswith(pattern_cmd[:-1]):
                                return True, None
                        elif base_cmd == pattern_cmd:
                            return True, None
                
                # Bash command not in allowed list
                return False, f"Bash command '{base_cmd}' not in allowed-tools"
        
        # Check regular tool patterns
        for rule in self.allowed_patterns:
            if rule.pattern == tool_name or rule.matches(tool_name):
                return True, None
        
        return False, f"Tool '{tool_name}' not in allowed-tools"
    
    def get_allowed_tools(self) -> List[str]:
        """Get list of allowed tool patterns"""
        if self.allow_all:
            return ["*"]
        return [rule.pattern for rule in self.allowed_patterns]


@dataclass
class ExecutionContext:
    """Context for skill execution"""
    session_id: Optional[str] = None
    arguments: List[str] = field(default_factory=list)
    working_dir: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    # Permission control
    permission_manager: Optional[ToolPermissionManager] = None
    
    # Subagent configuration
    agent_type: Optional[str] = None  # "Explore", "Plan", "general-purpose"
    
    # Execution tracking
    execution_count: int = 0
    last_execution: Optional[str] = None


class SkillExecutor:
    """Executes skills with permission control and subagent support"""
    
    def __init__(self, loader: Optional[SkillLoader] = None):
        self.loader = loader or SkillLoader()
        self._execution_history: List[Dict[str, Any]] = []
    
    def prepare_execution(self, manifest: SkillManifest, 
                         arguments: List[str] = None,
                         session_id: Optional[str] = None,
                         working_dir: Optional[Path] = None) -> ExecutionContext:
        """Prepare execution context from manifest
        
        Sets up:
        - Permission manager from allowed-tools
        - Subagent configuration from context/agent fields
        - Variable substitution context
        """
        context = ExecutionContext(
            session_id=session_id,
            arguments=arguments or [],
            working_dir=working_dir,
            env_vars={}
        )
        
        if manifest.level2 and manifest.level2.frontmatter:
            fm = manifest.level2.frontmatter
            
            # Setup permission manager
            if fm.allowed_tools:
                context.permission_manager = ToolPermissionManager(fm.allowed_tools)
            
            # Setup subagent configuration
            if fm.agent:
                context.agent_type = fm.agent
        
        return context
    
    def get_skill_prompt(self, manifest: SkillManifest, 
                        context: ExecutionContext,
                        include_body: bool = True) -> str:
        """Get the full prompt for skill execution
        
        This combines:
        - Level 2 body content (with variable substitution)
        - Any referenced support files (Level 3)
        """
        if not manifest.level2:
            # Load L2 if not already loaded
            load_context = LoadContext(
                session_id=context.session_id,
                arguments=context.arguments,
                working_dir=context.working_dir,
                env_vars=context.env_vars
            )
            manifest.level2 = self.loader.load_level2(manifest.path, load_context)
            manifest.level2_loaded = True
        
        if not manifest.level2:
            return f"# Skill: {manifest.name}\n\nNo instructions available."
        
        prompt_parts = []
        
        # Add skill header
        prompt_parts.append(f"# /{manifest.name}")
        if manifest.description:
            prompt_parts.append(f"\n{manifest.description}\n")
        
        # Add body content
        if include_body:
            body = manifest.level2.body_content
            
            # Apply variable substitution if needed
            if context.arguments and not manifest.level2.has_dynamic_injection:
                # Arguments not yet substituted
                load_context = LoadContext(
                    session_id=context.session_id,
                    arguments=context.arguments,
                    working_dir=context.working_dir,
                    env_vars=context.env_vars
                )
                body = self.loader._substitute_variables(body, load_context, manifest.path)
            
            prompt_parts.append(body)
        
        # Check if we need to append arguments
        if context.arguments and "$ARGUMENTS" not in manifest.level2.body_content:
            args_str = " ".join(context.arguments)
            prompt_parts.append(f"\n\n**Arguments:** {args_str}")
        
        return "\n".join(prompt_parts)
    
    def execute_inline(self, manifest: SkillManifest, 
                      context: ExecutionContext) -> Dict[str, Any]:
        """Execute skill inline (in current context)
        
        Returns the prompt content for the LLM to execute.
        The actual execution happens in the main conversation.
        """
        prompt = self.get_skill_prompt(manifest, context)
        
        # Record execution
        execution_record = {
            "skill_name": manifest.name,
            "session_id": context.session_id,
            "context": "inline",
            "agent_type": context.agent_type,
            "arguments": context.arguments,
            "prompt_length": len(prompt),
        }
        self._execution_history.append(execution_record)
        context.execution_count += 1
        context.last_execution = manifest.name
        
        return {
            "success": True,
            "type": "inline",
            "prompt": prompt,
            "manifest": manifest.to_dict(
                include_level1=True,
                include_level2=True,
                include_level3=False
            ),
            "permissions": self._get_permission_info(context),
        }
    
    def execute_in_subagent(self, manifest: SkillManifest,
                           context: ExecutionContext) -> Dict[str, Any]:
        """Execute skill in isolated subagent (context: fork)
        
        This prepares the subagent configuration but doesn't actually
        create the subagent (that's handled by the agent system).
        """
        prompt = self.get_skill_prompt(manifest, context)
        
        # Determine agent type
        agent_type = context.agent_type or "general-purpose"
        
        # For fork context, the prompt becomes the task for the subagent
        subagent_config = {
            "type": agent_type,
            "task": prompt,
            "permissions": context.permission_manager.get_allowed_tools() if context.permission_manager else ["*"],
            "session_id": context.session_id,
        }
        
        # Record execution
        execution_record = {
            "skill_name": manifest.name,
            "session_id": context.session_id,
            "context": "fork",
            "agent_type": agent_type,
            "arguments": context.arguments,
        }
        self._execution_history.append(execution_record)
        context.execution_count += 1
        context.last_execution = manifest.name
        
        return {
            "success": True,
            "type": "subagent",
            "subagent_config": subagent_config,
            "prompt": prompt,
            "manifest": manifest.to_dict(
                include_level1=True,
                include_level2=True,
                include_level3=False
            ),
        }
    
    def execute(self, manifest: SkillManifest,
                arguments: List[str] = None,
                session_id: Optional[str] = None,
                working_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute a skill (main entry point)
        
        Automatically determines inline vs subagent execution
        based on manifest context setting.
        """
        # Prepare execution context
        context = self.prepare_execution(
            manifest=manifest,
            arguments=arguments or [],
            session_id=session_id,
            working_dir=working_dir
        )
        
        # Determine execution mode
        execution_context = manifest.context
        
        if execution_context == SkillContext.FORK:
            return self.execute_in_subagent(manifest, context)
        else:
            return self.execute_inline(manifest, context)
    
    def validate_tool_call(self, context: ExecutionContext,
                          tool_name: str, 
                          tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate if a tool call is permitted"""
        if not context.permission_manager:
            return True, None
        
        allowed, reason = context.permission_manager.can_use_tool(tool_name, tool_args)
        return allowed, reason
    
    def _get_permission_info(self, context: ExecutionContext) -> Dict[str, Any]:
        """Get permission information for response"""
        if not context.permission_manager:
            return {
                "restricted": False,
                "allowed_tools": ["*"]
            }
        
        return {
            "restricted": True,
            "allowed_tools": context.permission_manager.get_allowed_tools()
        }
    
    def get_execution_history(self, 
                             skill_name: Optional[str] = None,
                             session_id: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history with optional filtering"""
        history = self._execution_history
        
        if skill_name:
            history = [h for h in history if h["skill_name"] == skill_name]
        
        if session_id:
            history = [h for h in history if h.get("session_id") == session_id]
        
        return history[-limit:]


def create_permission_manager(allowed_tools: List[str]) -> ToolPermissionManager:
    """Factory function for permission manager"""
    return ToolPermissionManager(allowed_tools)
