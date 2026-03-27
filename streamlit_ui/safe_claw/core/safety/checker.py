"""Safety checker for SafeClaw"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from safe_claw.models.config import SafetyConfig
from safe_claw.core.graph.state import SafeClawState

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Safety checker for validating operations and requests"""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.audit_log = []
        
        logger.info("Safety checker initialized")
    
    def check_request(self, user_input: str, session_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if a user request is safe"""
        safety_result = {
            "safe": True,
            "risk_level": "low",
            "warnings": [],
            "blocked_commands": [],
            "requires_confirmation": False,
            "audit_entry": None
        }
        
        # Check for blacklisted commands
        blocked_commands = self._check_blacklisted_commands(user_input)
        if blocked_commands:
            safety_result["safe"] = False
            safety_result["risk_level"] = "high"
            safety_result["blocked_commands"] = blocked_commands
            safety_result["warnings"].append(f"Blocked dangerous commands: {', '.join(blocked_commands)}")
        
        # Check for suspicious patterns
        suspicious_patterns = self._check_suspicious_patterns(user_input)
        if suspicious_patterns:
            safety_result["risk_level"] = "medium"
            safety_result["warnings"].extend([f"Suspicious pattern detected: {pattern}" for pattern in suspicious_patterns])
            safety_result["requires_confirmation"] = True
        
        # Check for file operations that need confirmation
        file_operations = self._check_file_operations(user_input)
        if file_operations and self.config.enable_confirmation:
            safety_result["requires_confirmation"] = True
            safety_result["warnings"].append(f"File operations require confirmation: {', '.join(file_operations)}")
        
        # Check for system commands
        system_commands = self._check_system_commands(user_input)
        if system_commands:
            safety_result["risk_level"] = "medium"
            safety_result["requires_confirmation"] = True
            safety_result["warnings"].append(f"System commands detected: {', '.join(system_commands)}")
        
        # Create audit entry
        audit_entry = self._create_audit_entry(user_input, session_id, safety_result)
        safety_result["audit_entry"] = audit_entry
        self.audit_log.append(audit_entry)
        
        # Determine overall safety
        is_safe = safety_result["safe"] and (not safety_result["requires_confirmation"] or not self.config.enable_confirmation)
        
        return is_safe, self._generate_safety_message(safety_result), safety_result
    
    def check_tool_call(self, tool_name: str, tool_args: Dict[str, Any], session_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if a tool call is safe"""
        safety_result = {
            "safe": True,
            "risk_level": "low",
            "warnings": [],
            "requires_confirmation": False,
            "audit_entry": None
        }
        
        # Check tool-specific safety
        tool_safety = self._check_tool_safety(tool_name, tool_args)
        safety_result.update(tool_safety)
        
        # Create audit entry
        tool_call_str = f"{tool_name}({tool_args})"
        audit_entry = self._create_audit_entry(tool_call_str, session_id, safety_result)
        safety_result["audit_entry"] = audit_entry
        self.audit_log.append(audit_entry)
        
        is_safe = safety_result["safe"] and (not safety_result["requires_confirmation"] or not self.config.enable_confirmation)
        
        return is_safe, self._generate_tool_safety_message(safety_result), safety_result
    
    def _check_blacklisted_commands(self, user_input: str) -> List[str]:
        """Check for blacklisted commands"""
        found_commands = []
        user_input_lower = user_input.lower()
        
        for command in self.config.blacklist_commands:
            if command.lower() in user_input_lower:
                found_commands.append(command)
        
        return found_commands
    
    def _check_suspicious_patterns(self, user_input: str) -> List[str]:
        """Check for suspicious patterns"""
        patterns = {
            r'\brm\s+-rf\s+/': "Remove root directory",
            r'\bsudo\s+rm': "Sudo remove command",
            r'\bformat\s+': "Format command",
            r'\bmkfs\s+': "Make filesystem",
            r'\bdd\s+if=/dev/zero': "Disk wipe command",
            r'\bchmod\s+777': "Set all permissions",
            r'\bchown\s+root': "Change ownership to root",
            r'\b>\s+/dev/': "Write to device files",
            r'\bcurl\s+\|\s+sh': "Download and execute script",
            r'\bwget\s+\|\s+bash': "Download and execute script"
        }
        
        found_patterns = []
        for pattern, description in patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                found_patterns.append(description)
        
        return found_patterns
    
    def _check_file_operations(self, user_input: str) -> List[str]:
        """Check for file operations"""
        file_ops = []
        user_input_lower = user_input.lower()
        
        operations = ["delete", "remove", "write", "create", "move", "copy", "modify", "edit"]
        file_indicators = ["file", "directory", "folder"]
        
        for op in operations:
            if op in user_input_lower:
                for indicator in file_indicators:
                    if indicator in user_input_lower:
                        file_ops.append(f"{op} {indicator}")
                        break
        
        return file_ops
    
    def _check_system_commands(self, user_input: str) -> List[str]:
        """Check for system commands"""
        system_commands = []
        user_input_lower = user_input.lower()
        
        commands = ["sudo", "su", "passwd", "crontab", "systemctl", "service", "init", "shutdown", "reboot"]
        
        for cmd in commands:
            if cmd in user_input_lower:
                system_commands.append(cmd)
        
        return system_commands
    
    def _check_tool_safety(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Check tool-specific safety"""
        result = {
            "safe": True,
            "risk_level": "low",
            "warnings": [],
            "requires_confirmation": False
        }
        
        # File operation tools
        if tool_name in ["write_file", "delete_file", "create_directory", "move_file"]:
            result["requires_confirmation"] = True
            result["risk_level"] = "medium"
            result["warnings"].append(f"File operation '{tool_name}' requires confirmation")
        
        # System tools
        elif tool_name in ["execute_command", "run_script"]:
            result["risk_level"] = "high"
            result["requires_confirmation"] = True
            result["warnings"].append(f"System operation '{tool_name}' requires confirmation")
            
            # Check for dangerous arguments
            if tool_args:
                args_str = str(tool_args).lower()
                if any(danger in args_str for danger in ["rm", "delete", "format", "sudo"]):
                    result["safe"] = False
                    result["risk_level"] = "critical"
                    result["warnings"].append("Dangerous arguments detected in tool call")
        
        # Network tools
        elif tool_name in ["download_file", "web_request"]:
            result["risk_level"] = "medium"
            result["warnings"].append(f"Network operation '{tool_name}' requires caution")
            
            # Check for suspicious URLs
            if "url" in tool_args:
                url = tool_args["url"]
                if self._is_suspicious_url(url):
                    result["requires_confirmation"] = True
                    result["warnings"].append("Suspicious URL detected")
        
        return result
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is suspicious"""
        suspicious_indicators = [
            "bit.ly", "tinyurl.com", "short.link",  # URL shorteners
            "pastebin.com", "hastebin.com",         # Pastebin sites
            "127.0.0.1", "localhost",               # Local addresses
            "file://", "ftp://",                     # Non-HTTP protocols
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in suspicious_indicators)
    
    def _create_audit_entry(self, content: str, session_id: str, safety_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create audit log entry"""
        return {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "content": content[:200] + "..." if len(content) > 200 else content,
            "safe": safety_result["safe"],
            "risk_level": safety_result["risk_level"],
            "warnings": safety_result["warnings"],
            "requires_confirmation": safety_result["requires_confirmation"],
            "blocked_commands": safety_result.get("blocked_commands", [])
        }
    
    def _generate_safety_message(self, safety_result: Dict[str, Any]) -> str:
        """Generate safety message for user"""
        if not safety_result["safe"]:
            return f"❌ **Request Blocked** - Dangerous commands detected: {', '.join(safety_result['blocked_commands'])}"
        
        if safety_result["requires_confirmation"] and self.config.enable_confirmation:
            warnings_text = "; ".join(safety_result["warnings"])
            return f"⚠️ **Confirmation Required** - {warnings_text}"
        
        if safety_result["warnings"]:
            warnings_text = "; ".join(safety_result["warnings"])
            return f"⚡ **Warnings** - {warnings_text}"
        
        return "✅ **Safe** - Request approved"
    
    def _generate_tool_safety_message(self, safety_result: Dict[str, Any]) -> str:
        """Generate safety message for tool calls"""
        if not safety_result["safe"]:
            return f"❌ **Tool Call Blocked** - Safety check failed: {'; '.join(safety_result['warnings'])}"
        
        if safety_result["requires_confirmation"] and self.config.enable_confirmation:
            return f"⚠️ **Tool Call Requires Confirmation** - {'; '.join(safety_result['warnings'])}"
        
        if safety_result["warnings"]:
            return f"⚡ **Tool Call Warnings** - {'; '.join(safety_result['warnings'])}"
        
        return "✅ **Tool Call Safe** - Approved"
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:]
    
    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety statistics"""
        total_checks = len(self.audit_log)
        if total_checks == 0:
            return {"total_checks": 0}
        
        blocked = sum(1 for entry in self.audit_log if not entry["safe"])
        required_confirmation = sum(1 for entry in self.audit_log if entry["requires_confirmation"])
        
        risk_levels = {}
        for entry in self.audit_log:
            level = entry["risk_level"]
            risk_levels[level] = risk_levels.get(level, 0) + 1
        
        return {
            "total_checks": total_checks,
            "blocked_requests": blocked,
            "confirmation_required": required_confirmation,
            "block_rate": blocked / total_checks,
            "risk_distribution": risk_levels
        }
    
    def clear_audit_log(self):
        """Clear audit log"""
        self.audit_log.clear()
        logger.info("Audit log cleared")
