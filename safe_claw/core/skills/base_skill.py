"""Base skill class for SafeClaw"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseSkill(ABC):
    """Abstract base class for all SafeClaw skills"""
    
    def __init__(self, name: str, description: str, category: str = "general"):
        self.name = name
        self.description = description
        self.category = category
        self.created_at = datetime.now()
        self.usage_count = 0
        
        logger.info(f"Initialized skill: {self.name}")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the skill with given parameters"""
        return self._execute_with_validation(**kwargs)
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for this skill"""
        return self._get_parameter_schema()
    
    def _execute_with_validation(self, **kwargs) -> Dict[str, Any]:
        """Execute skill with input validation"""
        try:
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(kwargs)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Parameter validation failed: {error_msg}",
                    "result": None
                }
            
            # Execute skill
            result = self._execute_skill(**kwargs)
            
            return {
                "success": True,
                "result": result,
                "execution_time": getattr(self, '_execution_time', 0),
                "skill_name": self.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Skill execution failed: {str(e)}",
                "result": None
            }
    
    @abstractmethod
    def _execute_skill(self, **kwargs) -> Any:
        """Actual skill implementation (override in subclasses)"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate input parameters"""
        try:
            schema = self.get_parameters()
            required = schema.get("required", [])
            
            # Check required parameters
            for param in required:
                if param not in parameters:
                    return False, f"Missing required parameter: {param}"
            
            # Check parameter types
            properties = schema.get("properties", {})
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    param_schema = properties[param_name]
                    expected_type = param_schema.get("type")
                    
                    if not self._validate_parameter_type(param_value, expected_type):
                        return False, f"Parameter {param_name} should be of type {expected_type}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get default parameter schema (override in subclasses)"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def get_skill_info(self) -> Dict[str, Any]:
        """Get comprehensive skill information"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.get_parameters(),
            "usage_count": getattr(self, 'usage_count', 0),
            "success_rate": getattr(self, 'success_rate', 0.0),
            "last_used": getattr(self, 'last_used', None)
        }
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
    
    def can_handle(self, query: str) -> float:
        """Determine if this skill can handle the query (confidence score 0-1)"""
        # Base implementation - override in subclasses
        query_lower = query.lower()
        name_lower = self.name.lower()
        
        if name_lower in query_lower:
            return 0.8
        
        # Check for keywords in description
        desc_words = self.description.lower().split()
        matches = sum(1 for word in desc_words if word in query_lower)
        
        if matches > 0:
            return min(0.6, matches * 0.1)
        
        return 0.0

class FileSkill(BaseSkill):
    """Base class for file-related skills"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, "file_operations")
    
    def validate_file_path(self, file_path: str) -> tuple[bool, str]:
        """Validate file path for safety"""
        import os
        
        # Check for dangerous paths
        dangerous_paths = [
            "/etc", "/boot", "/sys", "/proc", "/dev",
            "C:\\Windows", "C:\\Program Files", "C:\\System32"
        ]
        
        for dangerous in dangerous_paths:
            if dangerous in file_path:
                return False, f"Access to protected path not allowed: {dangerous}"
        
        # Check path traversal
        if ".." in file_path:
            return False, "Path traversal not allowed"
        
        return True, ""
    
    def ensure_safe_directory(self, base_path: str, file_path: str) -> str:
        """Ensure file path is within safe directory"""
        import os
        
        # Make file path absolute relative to base path
        if not os.path.isabs(file_path):
            file_path = os.path.join(base_path, file_path)
        
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        # Ensure it's within base path
        if not file_path.startswith(os.path.normpath(base_path)):
            raise ValueError(f"File path outside safe directory: {file_path}")
        
        return file_path

class CodeSkill(BaseSkill):
    """Base class for code-related skills"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, "code_analysis")
    
    def detect_language(self, code: str, file_extension: str = None) -> str:
        """Detect programming language from code or file extension"""
        if file_extension:
            extension_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp',
                '.rb': 'ruby',
                '.go': 'go',
                '.rs': 'rust',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.json': 'json',
                '.xml': 'xml'
            }
            
            if file_extension.lower() in extension_map:
                return extension_map[file_extension.lower()]
        
        # Simple keyword-based detection
        code_lower = code.lower()
        
        if 'def ' in code_lower and 'import ' in code_lower:
            return 'python'
        elif 'function ' in code_lower and '{' in code:
            return 'javascript'
        elif 'public class ' in code_lower:
            return 'java'
        elif '#include' in code_lower:
            return 'cpp' if 'using namespace' in code_lower else 'c'
        elif 'using System' in code_lower:
            return 'csharp'
        
        return 'unknown'
    
    def validate_code(self, code: str, language: str) -> tuple[bool, str]:
        """Basic code validation"""
        if not code.strip():
            return False, "Code is empty"
        
        # Language-specific validation
        if language == 'python':
            if 'import os' in code and 'system(' in code:
                return False, "Potentially dangerous system calls detected"
        elif language == 'javascript':
            if 'eval(' in code or 'Function(' in code:
                return False, "Potentially dangerous code execution detected"
        
        return True, ""
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text"""
        import re
        from collections import Counter
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count frequency
        word_freq = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_freq.most_common(max_keywords)]

class AnalysisSkill(BaseSkill):
    """Base class for analysis skills"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, "analysis")
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text"""
        import re
        from collections import Counter
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count frequency
        word_freq = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_freq.most_common(max_keywords)]
    
    def calculate_complexity(self, text: str) -> Dict[str, Any]:
        """Calculate text complexity metrics"""
        sentences = text.split('.')
        words = text.split()
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "complexity_score": min(1.0, (avg_sentence_length / 20 + avg_word_length / 10) / 2)
        }
