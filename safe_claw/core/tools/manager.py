"""Tool Manager for SafeClaw

Manages builtin tools and skills system tools separately from the main agent.
Extracted from official_integration.py for better separation of concerns.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from langchain_core.tools import tool

from safe_claw.core.skills import SkillDiscovery, SkillScanner, SkillExecutor

logger = logging.getLogger(__name__)


class ToolManager:
    """Manages SafeClaw tools including builtin tools and skills system tools"""

    def __init__(self, 
                 skill_scanner: SkillScanner,
                 skill_discovery: SkillDiscovery,
                 skill_executor: SkillExecutor):
        self.skill_scanner = skill_scanner
        self.skill_discovery = skill_discovery
        self.skill_executor = skill_executor
        self._builtin_tools: List = []
        self._skills_tools: List = []
        self._all_tools: List = []
        
        # Output callback for real-time streaming
        self._output_callback: Optional[Callable[[str], None]] = None

        # Initialize tools
        self._initialize_builtin_tools()
        # self._initialize_skills_tools()
        self._combine_tools()

    def _initialize_builtin_tools(self):
        """Initialize SafeClaw builtin tools"""
        
        @tool
        def safe_claw_memory_search(query: str) -> str:
            """Search SafeClaw memory for relevant information"""
            # This would integrate with SafeClaw's memory system
            return f"Memory search results for: {query}"

        @tool
        def safe_claw_log_operation(operation: str, details: str) -> str:
            """Log operations for audit trail"""
            logger.info(f"SafeClaw operation: {operation} - {details}")
            return f"Logged operation: {operation}"

        @tool
        def safe_claw_file_read(file_path: str) -> str:
            """Read file contents safely"""
            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    return path.read_text()[:2000]  # Limit to 2000 chars
                else:
                    return f"File not found: {file_path}"
            except Exception as e:
                return f"Error reading file: {str(e)}"

        @tool
        def safe_claw_file_write(file_path: str, content: str) -> str:
            """Write content to file safely"""
            try:
                path = Path(file_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                return f"Successfully wrote to: {file_path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"

        @tool
        def ls(path: str) -> str:
            """Lists all files and directories in a directory with detailed information including type, size, and modification time."""
            try:
                import os
                from datetime import datetime
                
                dir_path = Path(path)
                if not dir_path.exists():
                    return f"Directory not found: {path}"
                if not dir_path.is_dir():
                    return f"Not a directory: {path}"
                
                items = []
                for item in dir_path.iterdir():
                    # Get file info
                    stat_info = item.stat()
                    size = stat_info.st_size
                    mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Determine type
                    if item.is_file():
                        item_type = "FILE"
                    elif item.is_dir():
                        item_type = "DIR"
                    else:
                        item_type = "OTHER"
                    
                    # Format size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f}KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f}MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f}GB"
                    
                    items.append(f"{item_type:6} {size_str:>8} {mtime} {item.name}")
                
                if not items:
                    return "Directory is empty"
                
                return "\n".join(sorted(items))
            except Exception as e:
                return f"Error listing directory: {str(e)}"

        self._builtin_tools = [
            safe_claw_memory_search,
            safe_claw_log_operation,
            safe_claw_file_read,
            safe_claw_file_write,
            ls
        ]
        
        logger.info(f"Initialized {len(self._builtin_tools)} builtin tools")

    def _initialize_skills_tools(self):
        """Initialize skills system tools"""
        
        @tool
        def skill_discover_and_execute(query: str, arguments: str = "") -> str:
            """Discover and execute a skill based on natural language query
            
            Skills are dynamically scanned from folders with progressive disclosure:
            - Level 1: metadata (~100 tokens, always loaded)
            - Level 2: SKILL.md content (~5k tokens, loaded on trigger)
            - Level 3: supporting files (unlimited, loaded on demand)
            
            Args:
                query: Natural language description of what you want to do
                arguments: Optional space-separated arguments for the skill
            
            Examples:
                - "analyze python code for bugs"
                - "convert csv to json" with arguments="data.csv output.json"
                - "fetch website content" with arguments="https://example.com"
            """
            try:
                args_list = arguments.split() if arguments else []
                result = self.skill_discovery.find_skill(
                    query=query,
                    arguments=args_list,
                    auto_trigger=True,
                    output_callback=self._output_callback
                )

                if result.success and result.execution_result:
                    execution = result.execution_result
                    if execution.get("success"):
                        # Check if it's a bash execution result
                        if execution.get("type") == "inline_bash":
                            bash_result = execution.get("bash_result", {})
                            if bash_result.get("success"):
                                # Return success with output from last command
                                results = bash_result.get("results", [])
                                if results:
                                    last_result = results[-1]
                                    stdout = last_result.get("stdout", "")
                                    stderr = last_result.get("stderr", "")
                                    output = stdout if stdout else stderr
                                    return f"✅ Skill '{result.skill_name}' executed successfully:\n{output}"
                                return f"✅ Skill '{result.skill_name}' executed successfully"
                            else:
                                # Bash execution failed
                                results = bash_result.get("results", [])
                                if results:
                                    failed_result = results[-1]
                                    stderr = failed_result.get("stderr", "Unknown error")
                                    return f"❌ Skill '{result.skill_name}' failed: {stderr}"
                                return f"❌ Skill '{result.skill_name}' failed"
                        else:
                            # Regular inline execution (LLM-based)
                            return f"✅ Skill '{result.skill_name}' executed successfully:\n{execution.get('result', '')}"
                    else:
                        return f"❌ Skill '{result.skill_name}' failed: {execution.get('error', 'Unknown error')}"
                elif result.level.value >= 2:  # L2_LOADED or higher
                    return f"⚠️ Found skill '{result.skill_name}' but execution failed. Error: {result.error}"
                else:
                    candidates = result.candidates[:3] if result.candidates else []
                    if candidates:
                        candidate_names = [c.skill.name for c in candidates]
                        return f"❓ No suitable skill found for: {query}\nConsider trying: {', '.join(candidate_names)}"
                    else:
                        return f"❓ No skill found for: {query}"

            except Exception as e:
                logger.error(f"Skill execution error: {e}")
                return f"❌ Error discovering/executing skill: {str(e)}"

        @tool
        def skill_list_available(category: str = "") -> str:
            """List available skills, optionally filtered by category

            Skills are dynamically discovered from folders. Categories include:
            - data: CSV, JSON, SQL processing
            - web: HTTP, crawling, API interactions
            - file: File operations and management
            - code: Code analysis, formatting, linting
            - image: Image processing and analysis
            - text: NLP, parsing, summarization
            - finance: Stock analysis, portfolio management
            - general: General purpose skills

            Args:
                category: Optional category filter (e.g., 'data', 'web', 'general')
            """
            try:
                if not self.skill_scanner.loaded:
                    self.skill_scanner.scan_all_skills()

                entries = list(self.skill_scanner.index.values())
                if category:
                    # Try exact category match first
                    filtered_by_category = [e for e in entries if e.category.lower() == category.lower()]
                    if filtered_by_category:
                        entries = filtered_by_category
                    else:
                        # Fallback: check if category is actually a skill name
                        skill_match = [e for e in entries if e.name.lower() == category.lower()]
                        if skill_match:
                            # Return info about this specific skill
                            skill = skill_match[0]
                            return f"📁 {skill.category.upper()} - {skill.name}\n{skill.description[:200]}"
                        else:
                            # No match found
                            return f"No skills found in category '{category}'. Available categories: {set(e.category for e in entries)}"

                if not entries:
                    return f"No skills found" + (f" in category '{category}'" if category else "")

                # Group by category
                by_category = {}
                for entry in entries:
                    cat = entry.category or "general"
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(entry)

                result = []
                for cat, skills in sorted(by_category.items()):
                    result.append(f"📁 {cat.upper()} ({len(skills)} skills):")
                    for skill in sorted(skills, key=lambda s: s.name):
                        invocable = "🔄" if skill.auto_trigger else "👤"
                        result.append(f"  {invocable} {skill.name}: {skill.description[:80]}")
                    result.append("")

                return "\n".join(result)

            except Exception as e:
                logger.error(f"Error listing skills: {e}")
                return f"❌ Error listing skills: {str(e)}"

        @tool
        def skill_get_prompt(skill_name: str, arguments: str = "") -> str:
            """Get the prompt content for a skill (for manual execution)
            
            This retrieves the Level 2 content of a skill without executing it.
            Useful for understanding what a skill will do before running it.
            
            Args:
                skill_name: Name of the skill
                arguments: Optional space-separated arguments
            """
            try:
                args_list = arguments.split() if arguments else []
                prompt = self.skill_discovery.get_skill_prompt(skill_name, args_list)

                if prompt:
                    return f"📋 Skill '{skill_name}' prompt:\n\n{prompt}"
                else:
                    return f"❌ Skill '{skill_name}' not found or not loaded"

            except Exception as e:
                logger.error(f"Error getting skill prompt: {e}")
                return f"❌ Error getting skill prompt: {str(e)}"

        self._skills_tools = [
            skill_discover_and_execute,
            skill_list_available,
            skill_get_prompt
        ]
        
        logger.info(f"Initialized {len(self._skills_tools)} skills system tools")

    def _combine_tools(self):
        """Combine all tools into a single list"""
        self._all_tools = self._builtin_tools + self._skills_tools
        logger.info(f"Total tools: {len(self._builtin_tools)} builtin + {len(self._skills_tools)} skills = {len(self._all_tools)}")

    def get_all_tools(self) -> List:
        """Get all tools (builtin + skills)"""
        return self._all_tools

    def get_builtin_tools(self) -> List:
        """Get only builtin tools"""
        return self._builtin_tools

    def get_skills_tools(self) -> List:
        """Get only skills system tools"""
        return self._skills_tools

    def estimate_tokens(self) -> int:
        """Estimate tokens consumed by all tools descriptions"""
        total_tokens = 0

        for tool in self._all_tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                # LangChain tool object
                name_tokens = len(tool.name.split()) * 1.3
                desc_tokens = len(tool.description.split()) * 1.3
                total_tokens += name_tokens + desc_tokens
            elif hasattr(tool, '__doc__'):
                # Function-based tool
                doc_tokens = len(str(tool.__doc__).split()) * 1.3 if tool.__doc__ else 0
                total_tokens += doc_tokens
            else:
                # Default estimate for unknown tool types
                total_tokens += 50  # Conservative estimate per tool

        return int(total_tokens)

    def limit_tools(self, max_tools: int) -> List:
        """Limit the number of tools to fit context constraints
        
        Args:
            max_tools: Maximum number of tools to return
            
        Returns:
            List of tools limited to max_tools (prioritizes builtin tools)
        """
        if len(self._all_tools) <= max_tools:
            return self._all_tools
        
        # Prioritize builtin tools first, then skills tools
        builtin_count = len(self._builtin_tools)
        if builtin_count >= max_tools:
            return self._builtin_tools[:max_tools]
        
        # Return all builtin + some skills tools
        remaining = max_tools - builtin_count
        return self._builtin_tools + self._skills_tools[:remaining]
    
    def set_output_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        """Set the output callback for real-time streaming
        
        Args:
            callback: Function to call with each line of output during bash command execution
        """
        self._output_callback = callback
    
    def get_output_callback(self) -> Optional[Callable[[str], None]]:
        """Get the current output callback"""
        return self._output_callback
