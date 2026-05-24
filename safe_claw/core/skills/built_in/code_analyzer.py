"""Code analysis skills for SafeClaw"""

import ast
import re
from typing import Dict, Any, List, Optional
import logging

from safe_claw.core.skills.base_skill import CodeSkill

logger = logging.getLogger(__name__)

class AnalyzeCodeSkill(CodeSkill):
    """Skill for analyzing code structure and quality"""
    
    def __init__(self):
        super().__init__("analyze_code", "Analyze code structure, complexity, and quality")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to analyze"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (auto-detected if not provided)",
                    "default": None
                },
                "file_extension": {
                    "type": "string",
                    "description": "File extension for language detection",
                    "default": None
                }
            },
            "required": ["code"]
        }
    
    def _execute_skill(self, code: str, language: str = None, file_extension: str = None) -> Dict[str, Any]:
        """Execute code analysis"""
        try:
            # Detect language
            if not language:
                language = self.detect_language(code, file_extension)
            
            # Validate code
            is_valid, validation_msg = self.validate_code(code, language)
            if not is_valid:
                return {"success": False, "error": validation_msg}
            
            # Analyze based on language
            if language == "python":
                analysis = self._analyze_python(code)
            elif language == "javascript":
                analysis = self._analyze_javascript(code)
            elif language == "java":
                analysis = self._analyze_java(code)
            else:
                analysis = self._analyze_generic(code)
            
            self.increment_usage()
            
            return {
                "success": True,
                "language": language,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code"""
        try:
            tree = ast.parse(code)
            
            # Count different node types
            functions = []
            classes = []
            imports = []
            variables = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": len(node.args.args),
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(f"from {node.module}")
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            # Calculate complexity metrics
            complexity = self._calculate_python_complexity(tree)
            
            return {
                "type": "python",
                "functions": functions,
                "classes": classes,
                "imports": list(set(imports)),
                "variables": list(set(variables)),
                "complexity": complexity,
                "lines_of_code": len(code.split('\n')),
                "ast_nodes": len(list(ast.walk(tree)))
            }
            
        except SyntaxError as e:
            return {"type": "python", "error": f"Syntax error: {e}"}
    
    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        analysis = {
            "type": "javascript",
            "functions": [],
            "variables": [],
            "imports": [],
            "lines_of_code": len(code.split('\n'))
        }
        
        # Find functions
        function_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\(',
            r'let\s+(\w+)\s*=\s*\(',
            r'var\s+(\w+)\s*=\s*\(',
            r'(\w+)\s*:\s*function',
            r'(\w+)\s*=\s*function'
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, code)
            analysis["functions"].extend(matches)
        
        # Find variables
        var_patterns = [r'(?:const|let|var)\s+(\w+)\s*=', r'(\w+)\s*=' ]
        for pattern in var_patterns:
            matches = re.findall(pattern, code)
            analysis["variables"].extend(matches)
        
        # Find imports
        import_patterns = [r'import.*from\s+[\'"]([^\'"]+)[\'"]', r'require\([\'"]([^\'"]+)[\'"]\)']
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            analysis["imports"].extend(matches)
        
        # Remove duplicates
        analysis["functions"] = list(set(analysis["functions"]))
        analysis["variables"] = list(set(analysis["variables"]))
        analysis["imports"] = list(set(analysis["imports"]))
        
        return analysis
    
    def _analyze_java(self, code: str) -> Dict[str, Any]:
        """Analyze Java code"""
        analysis = {
            "type": "java",
            "classes": [],
            "methods": [],
            "imports": [],
            "lines_of_code": len(code.split('\n'))
        }
        
        # Find classes
        class_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?class\s+(\w+)', code)
        analysis["classes"] = class_matches
        
        # Find methods
        method_pattern = r'(?:public\s+|private\s+|protected\s+|static\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s]+)?\s*{'
        method_matches = re.findall(method_pattern, code)
        analysis["methods"] = [m for m in method_matches if m not in ['if', 'while', 'for', 'switch']]
        
        # Find imports
        import_matches = re.findall(r'import\s+([\w\.\*]+);', code)
        analysis["imports"] = import_matches
        
        return analysis
    
    def _analyze_generic(self, code: str) -> Dict[str, Any]:
        """Generic code analysis for unknown languages"""
        lines = code.split('\n')
        
        # Basic metrics
        analysis = {
            "type": "generic",
            "lines_of_code": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]),
            "estimated_functions": len(re.findall(r'\w+\s*\(', code)),
            "keywords": self.extract_keywords(code)
        }
        
        return analysis
    
    def _calculate_python_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate Python code complexity metrics"""
        complexity = {
            "cyclomatic_complexity": 1,  # Base complexity
            "cognitive_complexity": 0,
            "nesting_depth": 0
        }
        
        for node in ast.walk(tree):
            # Cyclomatic complexity
            if isinstance(node, ast.If):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.While):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.For):
                complexity["cyclomatic_complexity"] += 1
            elif hasattr(ast, 'AsyncFor') and isinstance(node, ast.AsyncFor):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.With):
                complexity["cyclomatic_complexity"] += 1
            elif hasattr(ast, 'AsyncWith') and isinstance(node, ast.AsyncWith):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.BoolOp):
                complexity["cyclomatic_complexity"] += len(node.values) - 1
        
        return complexity

class CodeQualitySkill(CodeSkill):
    """Skill for checking code quality and best practices"""
    
    def __init__(self):
        super().__init__("code_quality", "Check code quality and suggest improvements")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to check"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "default": None
                }
            },
            "required": ["code"]
        }
    
    def _execute_skill(self, code: str, language: str = None) -> Dict[str, Any]:
        """Execute code quality check"""
        try:
            if not language:
                language = self.detect_language(code)
            
            issues = []
            suggestions = []
            
            if language == "python":
                issues, suggestions = self._check_python_quality(code)
            elif language == "javascript":
                issues, suggestions = self._check_javascript_quality(code)
            else:
                issues, suggestions = self._check_generic_quality(code)
            
            self.increment_usage()
            
            return {
                "success": True,
                "language": language,
                "quality_score": self._calculate_quality_score(len(issues), len(code)),
                "issues": issues,
                "suggestions": suggestions,
                "metrics": self._get_quality_metrics(code)
            }
            
        except Exception as e:
            logger.error(f"Error checking code quality: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_python_quality(self, code: str) -> tuple[List[Dict], List[str]]:
        """Check Python code quality"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Line length
            if len(line) > 120:
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": f"Line too long ({len(line)} > 120 characters)"
                })
            
            # Trailing whitespace
            if line.endswith(' '):
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": "Trailing whitespace"
                })
            
            # Missing docstring for functions
            if stripped.startswith('def ') and '"""' not in code[code.find(line):code.find(line) + 200]:
                suggestions.append(f"Consider adding docstring to function at line {i}")
            
            # Check for TODO comments
            if 'TODO' in stripped or 'FIXME' in stripped:
                issues.append({
                    "line": i,
                    "type": "maintenance",
                    "message": "TODO/FIXME comment found",
                    "suggestion": "Complete the TODO or remove the comment"
                })
        
        # Check for imports
        if 'import *' in code:
            issues.append({
                "line": None,
                "type": "style",
                "message": "Avoid using 'import *'"
            })
        
        return issues, suggestions
    
    def _check_javascript_quality(self, code: str) -> tuple[List[Dict], List[str]]:
        """Check JavaScript code quality"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Use == instead of ===
            if '==' in stripped and '===' not in stripped:
                issues.append({
                    "line": i,
                    "type": "best_practice",
                    "message": "Use === instead of =="
                })
            
            # Use var instead of let/const
            if 'var ' in stripped:
                issues.append({
                    "line": i,
                    "type": "modernization",
                    "message": "Use let or const instead of var"
                })
            
            # Missing semicolons
            if stripped and not stripped.endswith((';', '{', '}')) and not any(keyword in stripped for keyword in ['if', 'for', 'while', 'function']):
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": "Missing semicolon"
                })
        
        return issues, suggestions
    
    def _check_generic_quality(self, code: str) -> tuple[List[Dict], List[str]]:
        """Generic code quality check"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Very long lines
            if len(line) > 150:
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": f"Very long line ({len(line)} characters)"
                })
            
            # Multiple consecutive empty lines
            if i > 1 and not lines[i-2].strip() and not line.strip():
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": "Multiple consecutive empty lines"
                })
        
        return issues, suggestions
    
    def _calculate_quality_score(self, issue_count: int, code_length: int) -> float:
        """Calculate quality score (0-100)"""
        if code_length == 0:
            return 100.0
        
        # Penalize based on issues per 100 lines
        issues_per_100_lines = (issue_count / code_length) * 100
        score = max(0, 100 - (issues_per_100_lines * 10))
        
        return round(score, 1)
    
    def _get_quality_metrics(self, code: str) -> Dict[str, Any]:
        """Get quality metrics"""
        lines = code.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith(('#', '//', '/*', '*'))]),
            "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
        }

class CodeFormatterSkill(CodeSkill):
    """Skill for formatting code"""
    
    def __init__(self):
        super().__init__("format_code", "Format code according to language conventions")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to format"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "default": None
                }
            },
            "required": ["code"]
        }
    
    def _execute_skill(self, code: str, language: str = None) -> Dict[str, Any]:
        """Execute code formatting"""
        try:
            if not language:
                language = self.detect_language(code)
            
            if language == "python":
                formatted_code = self._format_python(code)
            elif language == "javascript":
                formatted_code = self._format_javascript(code)
            else:
                formatted_code = self._format_generic(code)
            
            self.increment_usage()
            
            return {
                "success": True,
                "language": language,
                "formatted_code": formatted_code,
                "changes_made": len(formatted_code) != len(code)
            }
            
        except Exception as e:
            logger.error(f"Error formatting code: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_python(self, code: str) -> str:
        """Basic Python formatting"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Decrease indent for closing blocks
            if stripped.startswith(('except', 'elif', 'else', 'finally', ')')):
                indent_level = max(0, indent_level - 1)
            
            # Apply indentation
            formatted_line = '    ' * indent_level + stripped
            formatted_lines.append(formatted_line)
            
            # Increase indent for opening blocks
            if stripped.endswith(':'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def _format_javascript(self, code: str) -> str:
        """Basic JavaScript formatting"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
            
            # Apply indentation
            formatted_line = '    ' * indent_level + stripped
            formatted_lines.append(formatted_line)
            
            # Increase indent for opening braces
            if stripped.endswith('{'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def _format_generic(self, code: str) -> str:
        """Generic formatting - just clean up whitespace"""
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            formatted_line = line.rstrip()
            formatted_lines.append(formatted_line)
        
        # Remove multiple consecutive empty lines
        result = []
        empty_count = 0
        
        for line in formatted_lines:
            if line.strip():
                result.append(line)
                empty_count = 0
            else:
                if empty_count < 2:
                    result.append(line)
                empty_count += 1
        
        return '\n'.join(result)
