"""Safety policies and rules for SafeClaw"""

import re
from typing import Dict, List, Any, Optional
from enum import Enum

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SafetyPolicy:
    """Base safety policy class"""
    
    def __init__(self, name: str, description: str, risk_level: RiskLevel):
        self.name = name
        self.description = description
        self.risk_level = risk_level
    
    def check(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if content violates this policy"""
        # Base implementation - always safe
        return {
            "safe": True,
            "risk_level": self.risk_level,
            "message": "Base policy check passed"
        }

class FileOperationPolicy(SafetyPolicy):
    """Policy for file operations"""
    
    def __init__(self):
        super().__init__(
            "file_operations",
            "Controls and monitors file system operations",
            RiskLevel.MEDIUM
        )
        
        self.dangerous_paths = [
            "/etc", "/boot", "/sys", "/proc", "/dev",
            "C:\\Windows", "C:\\Program Files", "C:\\System32"
        ]
        
        self.protected_extensions = [
            ".exe", ".dll", ".sys", ".bat", ".cmd", ".sh",
            ".scr", ".vbs", ".js", ".jar", ".com", ".pif"
        ]
    
    def check(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check file operation safety"""
        result = {
            "violates": False,
            "risk_level": RiskLevel.LOW,
            "warnings": [],
            "requires_confirmation": False
        }
        
        content_lower = content.lower()
        
        # Check for dangerous paths
        for path in self.dangerous_paths:
            if path.lower() in content_lower:
                result["violates"] = True
                result["risk_level"] = RiskLevel.HIGH
                result["warnings"].append(f"Attempted access to protected path: {path}")
        
        # Check for protected file extensions
        for ext in self.protected_extensions:
            if ext in content_lower:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.MEDIUM
                result["warnings"].append(f"Operation on protected file type: {ext}")
        
        # Check for mass deletion
        if any(pattern in content_lower for pattern in ["rm *", "del *", "delete all"]):
            result["violates"] = True
            result["risk_level"] = RiskLevel.HIGH
            result["warnings"].append("Mass file deletion detected")
        
        return result

class SystemCommandPolicy(SafetyPolicy):
    """Policy for system commands"""
    
    def __init__(self):
        super().__init__(
            "system_commands",
            "Controls execution of system commands",
            RiskLevel.HIGH
        )
        
        self.blocked_commands = [
            "rm -rf /", "format c:", "del /s /q", "shutdown",
            "reboot", "halt", "passwd", "su", "sudo su",
            "chmod 777", "chown root", "crontab"
        ]
        
        self.privileged_commands = [
            "sudo", "su", "doas", "pkexec", "gksudo"
        ]
    
    def check(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check system command safety"""
        result = {
            "violates": False,
            "risk_level": RiskLevel.LOW,
            "warnings": [],
            "requires_confirmation": False
        }
        
        content_lower = content.lower()
        
        # Check for blocked commands
        for cmd in self.blocked_commands:
            if cmd in content_lower:
                result["violates"] = True
                result["risk_level"] = RiskLevel.CRITICAL
                result["warnings"].append(f"Blocked system command: {cmd}")
        
        # Check for privileged commands
        for cmd in self.privileged_commands:
            if cmd in content_lower:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.HIGH
                result["warnings"].append(f"Privileged command detected: {cmd}")
        
        # Check for shell injection patterns
        injection_patterns = [
            r"\|\s*sh", r"\|\s*bash", r"\|\s*cmd",
            r"\$\(", r"`.*`", r";\s*rm", r"&&\s*rm"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, content):
                result["violates"] = True
                result["risk_level"] = RiskLevel.CRITICAL
                result["warnings"].append(f"Shell injection pattern detected: {pattern}")
        
        return result

class NetworkPolicy(SafetyPolicy):
    """Policy for network operations"""
    
    def __init__(self):
        super().__init__(
            "network_operations",
            "Controls network requests and downloads",
            RiskLevel.MEDIUM
        )
        
        self.blocked_domains = [
            "malware-site.com", "phishing-site.com"
        ]
        
        self.suspicious_tlds = [
            ".tk", ".ml", ".ga", ".cf", ".bit", ".onion"
        ]
        
        self.require_confirmation = [
            "download", "wget", "curl", "fetch", "git clone"
        ]
    
    def check(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check network operation safety"""
        result = {
            "violates": False,
            "risk_level": RiskLevel.LOW,
            "warnings": [],
            "requires_confirmation": False
        }
        
        content_lower = content.lower()
        
        # Check for blocked domains
        for domain in self.blocked_domains:
            if domain in content_lower:
                result["violates"] = True
                result["risk_level"] = RiskLevel.HIGH
                result["warnings"].append(f"Blocked domain: {domain}")
        
        # Check for suspicious TLDs
        for tld in self.suspicious_tlds:
            if tld in content_lower:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.MEDIUM
                result["warnings"].append(f"Suspicious TLD detected: {tld}")
        
        # Check for operations requiring confirmation
        for op in self.require_confirmation:
            if op in content_lower:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.MEDIUM
                result["warnings"].append(f"Network operation requires confirmation: {op}")
        
        # Check for localhost/internal network access
        if any(pattern in content_lower for pattern in ["127.0.0.1", "localhost", "192.168.", "10."]):
            result["requires_confirmation"] = True
            result["risk_level"] = RiskLevel.MEDIUM
            result["warnings"].append("Internal network access detected")
        
        return result

class DataPrivacyPolicy(SafetyPolicy):
    """Policy for data privacy and PII"""
    
    def __init__(self):
        super().__init__(
            "data_privacy",
            "Protects personally identifiable information",
            RiskLevel.MEDIUM
        )
        
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
        ]
        
        self.sensitive_keywords = [
            "password", "secret", "api key", "token", "private key",
            "credit card", "ssn", "social security", "bank account"
        ]
    
    def check(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check for PII and sensitive data"""
        result = {
            "violates": False,
            "risk_level": RiskLevel.LOW,
            "warnings": [],
            "requires_confirmation": False
        }
        
        content_lower = content.lower()
        
        # Check for PII patterns
        for pattern in self.pii_patterns:
            matches = re.findall(pattern, content)
            if matches:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.HIGH
                result["warnings"].append(f"Potential PII detected: {len(matches)} matches")
        
        # Check for sensitive keywords
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                result["requires_confirmation"] = True
                result["risk_level"] = RiskLevel.MEDIUM
                result["warnings"].append(f"Sensitive keyword detected: {keyword}")
        
        return result

class PolicyEngine:
    """Engine for managing and executing safety policies"""
    
    def __init__(self):
        self.policies = {
            "file_operations": FileOperationPolicy(),
            "system_commands": SystemCommandPolicy(),
            "network_operations": NetworkPolicy(),
            "data_privacy": DataPrivacyPolicy()
        }
    
    def check_all_policies(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check content against all policies"""
        results = {
            "safe": True,
            "overall_risk": RiskLevel.LOW,
            "violations": [],
            "warnings": [],
            "requires_confirmation": False,
            "policy_results": {}
        }
        
        for policy_name, policy in self.policies.items():
            policy_result = policy.check(content, context)
            results["policy_results"][policy_name] = policy_result
            
            # Aggregate results
            if policy_result["violates"]:
                results["safe"] = False
                results["violations"].extend(policy_result["warnings"])
            
            if policy_result["requires_confirmation"]:
                results["requires_confirmation"] = True
            
            results["warnings"].extend(policy_result["warnings"])
            
            # Update overall risk level
            if policy_result["risk_level"].value == "critical":
                results["overall_risk"] = RiskLevel.CRITICAL
            elif policy_result["risk_level"].value == "high" and results["overall_risk"].value != "critical":
                results["overall_risk"] = RiskLevel.HIGH
            elif policy_result["risk_level"].value == "medium" and results["overall_risk"].value in ["low", "medium"]:
                results["overall_risk"] = RiskLevel.MEDIUM
        
        return results
    
    def add_policy(self, name: str, policy: SafetyPolicy):
        """Add a custom policy"""
        self.policies[name] = policy
    
    def remove_policy(self, name: str):
        """Remove a policy"""
        if name in self.policies:
            del self.policies[name]
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies"""
        return {
            name: {
                "name": policy.name,
                "description": policy.description,
                "risk_level": policy.risk_level.value
            }
            for name, policy in self.policies.items()
        }
