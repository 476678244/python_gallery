"""Tool Manager for SafeClaw

Manages builtin tools and skills system tools separately from the main agent.
Extracted from official_integration.py for better separation of concerns.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from langchain_core.tools import tool

from safe_claw.core.skills import SkillDiscovery, SkillScanner, SkillExecutor
from safe_claw.core.tools.web import WebToolError, fetch_url, search_web

logger = logging.getLogger(__name__)

_MEMORY_SEARCH_MAX_CHARS = 400
_MEMORY_SEARCH_TOP_K = 8


class ToolManager:
    """Manages SafeClaw tools including builtin tools and skills system tools"""

    def __init__(
        self,
        skill_scanner: SkillScanner,
        skill_discovery: SkillDiscovery,
        skill_executor: SkillExecutor,
        memory_manager: Any = None,
    ):
        self.skill_scanner = skill_scanner
        self.skill_discovery = skill_discovery
        self.skill_executor = skill_executor
        self.memory_manager = memory_manager
        self._builtin_tools: List = []
        self._skills_tools: List = []
        self._all_tools: List = []

        # Output callback for real-time streaming
        self._output_callback: Optional[Callable[[str], None]] = None

        # Initialize tools (skills tools honor SkillDiscovery enabled filter)
        self._initialize_builtin_tools()
        self._initialize_skills_tools()
        self._combine_tools()

    def _require_memory_manager(self, tool_name: str) -> Any:
        if self.memory_manager is None:
            raise ValueError(
                f"[ToolManager] {tool_name} requires MemoryManager\n"
                f"  Expected: ToolManager(..., memory_manager=MemoryManager(...))\n"
                f"  Actual: None\n"
                f"  Hint: pass via SafeClawDeepAgent config / DeepAgentFactory.create_with_memory"
            )
        return self.memory_manager

    def _format_memory_search_results(self, query: str, results: List[Any]) -> str:
        if not results:
            return f"No memories found for: {query}"

        lines = [f"Found {len(results)} memories for: {query}", ""]
        for i, result in enumerate(results[:_MEMORY_SEARCH_TOP_K], 1):
            memory = result.memory
            content = (memory.content or "").strip().replace("\n", " ")
            if len(content) > _MEMORY_SEARCH_MAX_CHARS:
                content = content[: _MEMORY_SEARCH_MAX_CHARS - 3] + "..."
            layer = (
                memory.layer.value
                if hasattr(memory.layer, "value")
                else str(memory.layer)
            )
            lines.append(
                f"{i}. [{layer}] score={result.score:.2f} "
                f"importance={memory.importance_score:.2f} id={memory.id}"
            )
            lines.append(f"   {content}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _initialize_builtin_tools(self):
        """Initialize SafeClaw builtin tools"""

        @tool
        def safe_claw_memory_search(query: str, max_results: int = 8) -> str:
            """Search SafeClaw long-term memory (jargon, preferences, past notes).

            Use when the user asks about remembered facts, jargon, or prior context
            that may not be in the current system injection.
            """
            mm = self._require_memory_manager("safe_claw_memory_search")
            q = (query or "").strip()
            if not q:
                raise ValueError(
                    "[ToolManager] safe_claw_memory_search requires a non-empty query\n"
                    "  Actual: empty/whitespace"
                )
            limit = max(1, min(int(max_results or _MEMORY_SEARCH_TOP_K), 20))
            results = mm.search_memories(q, max_results=limit)
            logger.info(
                "[ToolManager] memory_search query=%r hits=%d", q, len(results)
            )
            return self._format_memory_search_results(q, results)

        @tool
        def safe_claw_memory_write(
            content: str,
            importance: float = 0.7,
            keywords: str = "",
        ) -> str:
            """Explicitly store a durable memory (preferences, jargon, facts).

            Prefer this over hoping the post-turn auto-write will keep the fact.
            Not available in ask/plan/safe modes (memory_auto_write off).
            """
            mm = self._require_memory_manager("safe_claw_memory_write")
            text = (content or "").strip()
            if not text:
                raise ValueError(
                    "[ToolManager] safe_claw_memory_write requires non-empty content\n"
                    "  Actual: empty/whitespace"
                )
            try:
                score = float(importance)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"[ToolManager] safe_claw_memory_write invalid importance\n"
                    f"  Expected: float in [0, 1]\n"
                    f"  Actual: {importance!r}"
                ) from exc
            if score < 0.0 or score > 1.0:
                raise ValueError(
                    f"[ToolManager] safe_claw_memory_write importance out of range\n"
                    f"  Expected: 0.0 <= importance <= 1.0\n"
                    f"  Actual: {score}"
                )
            kw = [k.strip() for k in (keywords or "").split(",") if k.strip()]
            memory_id = mm.add_memory(
                content=text[:4000],
                importance_score=score,
                keywords=kw,
                metadata={"source": "agent_tool", "type": "explicit"},
            )
            logger.info(
                "[ToolManager] memory_write id=%s importance=%.2f", memory_id, score
            )
            return (
                f"Remembered (id={memory_id}, importance={score:.2f}): "
                f"{text[:200]}{'...' if len(text) > 200 else ''}"
            )

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

        @tool
        def web_search(query: str, max_results: int = 5) -> str:
            """Search the public web for current information (docs, news, APIs).

            Prefer Tavily/Brave when API keys are configured; otherwise uses
            DuckDuckGo Instant Answer (not a full SERP). Use web_fetch to read a URL.
            """
            try:
                return search_web(query, max_results=max_results)
            except WebToolError:
                raise
            except Exception as e:
                raise WebToolError(
                    f"[web_search] Unexpected error\n"
                    f"  Query: {query!r}\n"
                    f"  Error: {type(e).__name__}: {e}"
                ) from e

        @tool
        def web_fetch(url: str, max_chars: int = 12000) -> str:
            """Fetch a public http(s) URL and return extracted text (HTML stripped).

            Blocks localhost / private IPs. Prefer this over shell curl/wget.
            """
            try:
                return fetch_url(url, max_chars=max_chars)
            except WebToolError:
                raise
            except Exception as e:
                raise WebToolError(
                    f"[web_fetch] Unexpected error\n"
                    f"  URL: {url!r}\n"
                    f"  Error: {type(e).__name__}: {e}"
                ) from e

        self._builtin_tools = [
            safe_claw_memory_search,
            safe_claw_memory_write,
            safe_claw_log_operation,
            safe_claw_file_read,
            safe_claw_file_write,
            ls,
            web_search,
            web_fetch,
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

                # Honor enabled allowlist (same SoT as DeepAgent skills=)
                if hasattr(self.skill_discovery, "_enabled_entries"):
                    entries = self.skill_discovery._enabled_entries()
                else:
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

    def get_tools_for_policy(
        self,
        *,
        skill_execute: str,
        allow_create: bool,
        allow_edit: bool,
        memory_auto_write: bool = True,
        ppt_tools: bool = False,
        workspace_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
        on_ppt_preview: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List:
        """Filter tools by ModePolicy (Fail Fast / hard gate).

        - skill_execute off → drop skill_discover_and_execute
        - allow_create False → drop safe_claw_file_write
        - allow_create True + allow_edit False → replace write with create-only wrapper
        - memory_auto_write False → drop safe_claw_memory_write (ask/plan/safe)
        - ppt_tools True → append safe_claw_ppt_* (only /ppt mode)
        """
        blocked: set[str] = set()
        if skill_execute == "off":
            blocked.add("skill_discover_and_execute")
        if not allow_create:
            blocked.add("safe_claw_file_write")
        if not memory_auto_write:
            blocked.add("safe_claw_memory_write")

        filtered = []
        for t in self._all_tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", "")
            if name in blocked:
                continue
            if name == "safe_claw_file_write" and allow_create and not allow_edit:
                filtered.append(self._make_create_only_file_write())
                continue
            filtered.append(t)

        if ppt_tools:
            if workspace_dir is None:
                raise ValueError(
                    "[ToolManager] ppt_tools=True requires workspace_dir\n"
                    "  Expected: Path to WORKSPACE_DIR\n"
                    "  Actual: None"
                )
            from safe_claw.core.tools.ppt import build_ppt_tools

            filtered.extend(
                build_ppt_tools(
                    Path(workspace_dir),
                    session_id=session_id or "_default",
                    on_preview=on_ppt_preview,
                )
            )

        logger.info(
            "[ToolManager] skill_execute=%s allow_create=%s allow_edit=%s "
            "memory_auto_write=%s ppt_tools=%s → %d tools",
            skill_execute,
            allow_create,
            allow_edit,
            memory_auto_write,
            ppt_tools,
            len(filtered),
        )
        return filtered

    def _make_create_only_file_write(self):
        """Builtin write that refuses overwrite (safe mode)."""

        @tool
        def safe_claw_file_write(file_path: str, content: str) -> str:
            """Create a new file only — fails if the path already exists (safe mode)."""
            try:
                path = Path(file_path)
                if path.exists():
                    return (
                        f"Error: File already exists (safe mode create-only): {file_path}"
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                return f"Successfully created: {file_path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"

        return safe_claw_file_write

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
