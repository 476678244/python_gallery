"""Permission Manager for SafeClaw

Manages tool permissions for skills.
Extracted from executor.py for better separation of concerns.
"""

import re
import logging
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ToolPermission(Enum):
    """Permission levels for tools"""
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_CONFIRMATION = "confirmation"


class ToolPermissionRule:
    """Single tool permission rule"""
    
    def __init__(self, pattern: str, permission: ToolPermission):
        self.pattern = pattern
        self.permission = permission
    
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
    
    Also manages safe file write paths.
    """
    
    def __init__(self, allowed_tools: List[str], safe_write_paths: Optional[List[str]] = None):
        self.allowed_patterns: List[ToolPermissionRule] = []
        self.denied_patterns: List[ToolPermissionRule] = []
        self.allow_all = False
        
        # Safe write paths - directories where write operations are allowed
        self.safe_write_paths: List[Path] = []
        if safe_write_paths is None:
            # Default safe write path: user's workspace directory
            self.safe_write_paths.append(Path.home() / "Downloads/workspace")
        else:
            self.safe_write_paths.extend([Path(p) for p in safe_write_paths])
        
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
    
    def is_restricted(self) -> bool:
        """Check if permissions are restricted"""
        return not self.allow_all
    
    def is_safe_write_path(self, file_path: str) -> bool:
        """Check if a file path is safe for write operations
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the path is within a safe write directory
        """
        path = Path(file_path).resolve()
        
        for safe_dir in self.safe_write_paths:
            safe_dir_resolved = safe_dir.resolve()
            try:
                # Check if path is within or equal to safe directory
                if path == safe_dir_resolved or safe_dir_resolved in path.parents or path.is_relative_to(safe_dir_resolved):
                    return True
            except (ValueError, RuntimeError):
                # Handle cases where paths can't be compared
                continue
        
        return False
    
    def add_safe_write_path(self, path: str) -> None:
        """Add a directory to the safe write paths list
        
        Args:
            path: Directory path to allow write operations in
        """
        self.safe_write_paths.append(Path(path).resolve())
    
    def get_safe_write_paths(self) -> List[str]:
        """Get list of safe write paths"""
        return [str(p) for p in self.safe_write_paths]


def create_permission_manager(allowed_tools: List[str]) -> ToolPermissionManager:
    """Factory function for permission manager"""
    return ToolPermissionManager(allowed_tools)
