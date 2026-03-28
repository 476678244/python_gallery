"""Official DeepAgents Integration for SafeClaw

Integrates with the new 3-level progressive disclosure skills system:
- Level 1: name + description (~100 tokens, always loaded)
- Level 2: SKILL.md content (~5k tokens, loaded on trigger)
- Level 3: Supporting files (loaded on demand)
"""

from typing import Dict, Any, Optional, List
import logging
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from deepagents import create_deep_agent
from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig
from streamlit_ui.safe_claw.core.skills import (
    SkillDiscovery, SkillScanner, SkillExecutor,
    discover_skill, get_skill_scanner
)

logger = logging.getLogger(__name__)


class SafeClawDeepAgent:
    """SafeClaw wrapper for official DeepAgents with progressive skills integration"""
    
    def __init__(self, llm_service: LLMService, config: Dict[str, Any] = None):
        self.llm_service = llm_service
        self.config = config or {}
        self.deep_agent = None
        
        # Initialize skills system
        self.skill_scanner = get_skill_scanner()
        self.skill_discovery = SkillDiscovery(self.skill_scanner)
        self.skill_executor = SkillExecutor()
        self._skill_tools_cache: Dict[str, Any] = {}
        
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the official DeepAgent"""
        try:
            # Convert LLMService to LangChain model
            model = self._create_langchain_model()
            
            # Get tools and skills paths list
            tools = self._get_safe_claw_tools()
            skills_paths = self._get_skills_paths()
            
            # Create DeepAgent with SafeClaw configuration
            self.deep_agent = create_deep_agent(
                model=model,
                system_prompt=self.config.get("system_prompt", self._get_default_prompt()),
                tools=tools,
                skills=skills_paths  # Pass skills paths instead of names
            )
            
            logger.info(f"Official DeepAgent initialized successfully with {len(tools)} tools and {len(skills_paths)} skills")
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepAgent: {e}")
            raise
    
    def _create_langchain_model(self):
        """Create LangChain model from LLMService config"""
        llm_config = self.llm_service.gateway.config
        
        # Map SafeClaw provider strings to LangChain model strings
        provider_model_map = {
            "openai": f"openai:{llm_config.model}",
            "anthropic": f"anthropic:{llm_config.model}",
            "ollama": f"ollama:{llm_config.model}",
            "google": f"google:{llm_config.model}",
        }
        
        model_string = provider_model_map.get(
            llm_config.provider, 
            f"openai:{llm_config.model}"  # Default to OpenAI
        )
        
        return init_chat_model(
            model=model_string,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )
    
    def _get_default_prompt(self) -> str:
        """Get default SafeClaw system prompt"""
        return """You are SafeClaw, a helpful and safe AI assistant with access to both builtin tools and a progressive skills system.

Your capabilities are organized into two categories:

## BUILTIN TOOLS (Core SafeClaw Functions)
These are always available, optimized tools for common operations:
- `safe_claw_memory_search`: Search memory and context
- `safe_claw_log_operation`: Log operations for audit
- `safe_claw_file_read`: Read files safely (limited to 2000 chars)
- `safe_claw_file_write`: Write files safely with path creation

## SKILLS SYSTEM (Dynamic, Progressive Disclosure)
Skills are discovered from folders with 3-level loading for efficiency:
- **Level 1**: Metadata only (~100 tokens/skill, always loaded)
- **Level 2**: Full SKILL.md content (~5k tokens, loaded on trigger)
- **Level 3**: Supporting files (unlimited, loaded on demand)

### Skills Tools:
- `skill_discover_and_execute`: Find and run skills by natural language
- `skill_list_available`: Browse skills by category
- `skill_get_prompt`: Preview skill logic before execution

### Skill Categories:
- **data**: CSV, JSON, SQL processing
- **web**: HTTP requests, crawling, APIs
- **file**: Advanced file operations
- **code**: Analysis, formatting, linting
- **image**: Processing and analysis
- **text**: NLP, parsing, summarization
- **finance**: Stock analysis, portfolios

## Usage Guidelines:
1. **Use builtin tools** for: basic file ops, memory search, logging
2. **Use skills** for: complex domain-specific tasks, data processing
3. **Always check** skill prompts with `skill_get_prompt` before execution
4. **Use `skill_list_available`** to discover capabilities

## Safety Principles:
- Always prioritize user safety and data privacy
- Ask for confirmation before destructive operations
- Skills have built-in permission controls and safe execution
- Use builtin tools for simple operations, skills for complex tasks

You have access to filesystem, builtin tools, and a dynamic skills system. Use these capabilities to help users effectively and safely."""
    
    def _get_safe_claw_tools(self) -> List:
        """Get SafeClaw-specific tools including both builtin tools and progressive skills"""
        tools = []
        
        # === BUILTIN TOOLS ===
        # Core SafeClaw builtin tools
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
                from pathlib import Path
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
                from pathlib import Path
                path = Path(file_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                return f"Successfully wrote to: {file_path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"
        
        tools.extend([
            safe_claw_memory_search,
            safe_claw_log_operation,
            safe_claw_file_read,
            safe_claw_file_write
        ])
        
        # === SKILLS SYSTEM TOOLS ===
        # Skills discovery and execution tools
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
                    auto_trigger=True
                )
                
                if result.success and result.execution_result:
                    execution = result.execution_result
                    if execution.get("success"):
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
            
            Args:
                category: Optional category filter
            """
            try:
                if not self.skill_scanner.loaded:
                    self.skill_scanner.scan_all_skills()
                
                entries = list(self.skill_scanner.index.values())
                if category:
                    entries = [e for e in entries if e.category.lower() == category.lower()]
                
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
        
        tools.extend([
            skill_discover_and_execute,
            skill_list_available,
            skill_get_prompt
        ])
        
        logger.info(f"Loaded {len(tools)} SafeClaw tools: {len([t for t in tools if 'skill_' not in t.name])} builtin + {len([t for t in tools if 'skill_' in t.name])} skills")
        return tools
    
    def _get_skills_paths(self) -> List[str]:
        """Get skills paths for DeepAgents"""
        try:
            # Get skills directory paths relative to project root
            from pathlib import Path
            import os
            
            # Find skills directories
            project_root = Path(__file__).parent.parent.parent.parent.parent
            skills_dir = project_root / "streamlit_ui"  / "skills"
            
            paths = []
            if skills_dir.exists():
                # Iterate through all directories to find SKILL.md files
                for skill_path in skills_dir.rglob("SKILL.md"):
                    # Get the parent directory of SKILL.md (the actual skill directory)
                    skill_dir = skill_path.parent
                    
                    # Convert to relative path from project root
                    rel_path = skill_dir.relative_to(project_root)
                    
                    # Convert to POSIX format and add trailing slash
                    path_str = str(rel_path).replace("\\", "/") + "/"
                    
                    if path_str not in paths:
                        paths.append(path_str)
            
            logger.info(f"Found skills paths from SKILL.md files: {paths}")
            return paths
            
        except Exception as e:
            logger.error(f"Error getting skills paths: {e}")
            return []
    
    def _get_available_skills(self) -> List[str]:
        """Get list of available skill names for DeepAgents skills parameter"""
        try:
            if not self.skill_scanner.loaded:
                self.skill_scanner.scan_all_skills()
            
            # Get all skill names from the scanner
            skill_names = list(self.skill_scanner.index.keys())
            
            # Filter to only include user-invocable skills
            user_invocable_skills = []
            for name in skill_names:
                entry = self.skill_scanner.index.get(name)
                if entry and entry.user_invocable:
                    user_invocable_skills.append(name)
            
            logger.info(f"Found {len(user_invocable_skills)} user-invocable skills out of {len(skill_names)} total")
            return user_invocable_skills
            
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            return []
    
    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Invoke DeepAgent with messages"""
        try:
            # Convert SafeClaw message format to DeepAgent format
            deep_agent_input = {"messages": messages}
            
            # Execute DeepAgent
            result = self.deep_agent.invoke(deep_agent_input)
            
            # Convert result back to SafeClaw format
            return {
                "content": result.get("content", ""),
                "tool_calls": result.get("tool_calls", []),
                "success": True,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"DeepAgent invocation error: {e}")
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": [],
                "success": False,
                "metadata": {"error": str(e)}
            }
    
    def stream(self, messages: List[Dict[str, str]]):
        """Stream DeepAgent response"""
        try:
            deep_agent_input = {"messages": messages}
            
            for chunk in self.deep_agent.stream(deep_agent_input):
                yield {
                    "content": chunk.get("content", ""),
                    "type": chunk.get("type", "chunk"),
                    "metadata": chunk.get("metadata", {})
                }
                
        except Exception as e:
            logger.error(f"DeepAgent streaming error: {e}")
            yield {
                "content": f"Error: {str(e)}",
                "type": "error",
                "metadata": {"error": str(e)}
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get DeepAgent information including skills statistics"""
        if not self.deep_agent:
            return {"status": "not_initialized"}
        
        try:
            # Get info from the compiled graph
            graph_info = getattr(self.deep_agent, 'get_graph', lambda: {})()
            
            # Get skills statistics
            skills_stats = {}
            available_skills = self._get_available_skills()
            
            if self.skill_scanner.loaded:
                entries = list(self.skill_scanner.index.values())
                skills_stats = {
                    "total_skills": len(entries),
                    "user_invocable": len(available_skills),
                    "categories": len(set(e.category for e in entries)),
                    "auto_trigger_skills": len([e for e in entries if e.auto_trigger]),
                }
            
            return {
                "type": "official_deep_agent",
                "status": "initialized",
                "graph_info": graph_info,
                "llm_config": self.llm_service.gateway.get_model_info(),
                "tools": {
                    "total_count": len(self._get_safe_claw_tools()),
                    "builtin_count": 4,
                    "skills_system_count": 3
                },
                "skills": {
                    "names_count": len(available_skills),
                    "names": available_skills[:10],  # Show first 10
                    "stats": skills_stats,
                    "progressive_disclosure": {
                        "levels": ["L1 (metadata)", "L2 (content)", "L3 (files)"],
                        "default_tokens": {"L1": "~100", "L2": "~5k", "L3": "unlimited"}
                    }
                }
            }
        except Exception as e:
            return {
                "type": "official_deep_agent",
                "status": "error",
                "error": str(e)
            }


class DeepAgentFactory:
    """Factory for creating SafeClaw DeepAgents"""
    
    @staticmethod
    def create_agent(llm_service: LLMService, config: Dict[str, Any] = None) -> SafeClawDeepAgent:
        """Create a SafeClaw DeepAgent"""
        return SafeClawDeepAgent(llm_service, config)
    
    @staticmethod
    def create_with_memory(llm_service: LLMService, memory_manager, config: Dict[str, Any] = None) -> SafeClawDeepAgent:
        """Create a SafeClaw DeepAgent with memory integration"""
        # Add memory-specific configuration
        memory_config = config or {}
        memory_config["memory_manager"] = memory_manager
        
        return SafeClawDeepAgent(llm_service, memory_config)
