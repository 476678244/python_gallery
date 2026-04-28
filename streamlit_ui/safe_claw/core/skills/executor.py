"""Skill Executor - Subagent execution and tool permission control

Handles:
- Tool permission filtering (allowed-tools from frontmatter)
- Subagent execution (context: fork)
- Variable substitution at execution time
- Permission validation
- Extraction and execution of bash commands from SKILL.md
"""

import re
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field

from streamlit_ui.safe_claw.core.skills.manifest import SkillManifest, SkillContext, SkillFrontmatter
from streamlit_ui.safe_claw.core.skills.loader import LoadContext, SkillLoader
from streamlit_ui.safe_claw.core.permissions import ToolPermissionManager

logger = logging.getLogger(__name__)


# Regex for extracting bash:execute code blocks
BASH_EXECUTE_PATTERN = re.compile(r'```bash:execute\n(.*?)\n```', re.DOTALL)


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
    
    # Real-time output callback
    output_callback: Optional[Callable[[str], None]] = None


class SkillExecutor:
    """Executes skills with permission control and subagent support"""
    
    def __init__(self, loader: Optional[SkillLoader] = None):
        self.loader = loader or SkillLoader()
        self._execution_history: List[Dict[str, Any]] = []
    
    def extract_execute_commands(self, body_content: str, 
                                context: ExecutionContext,
                                skill_path: Path) -> List[str]:
        """Extract and substitute variables from bash:execute code blocks
        
        Args:
            body_content: SKILL.md body content
            context: Execution context with arguments
            skill_path: Path to the skill directory
        
        Returns:
            List of executable commands with variables substituted
        """
        # Extract bash:execute blocks
        matches = BASH_EXECUTE_PATTERN.findall(body_content)
        
        if not matches:
            return []
        
        # Prepare variable substitutions
        substitutions = self._prepare_variable_substitutions(context, skill_path)
        
        # Substitute variables in each command
        commands = []
        for command_template in matches:
            command = command_template.strip()
            
            # Substitute variables
            for var_name, var_value in substitutions.items():
                command = command.replace(f"${var_name}", var_value)
            
            commands.append(command)
        
        return commands
    
    def execute_bash_commands(self, commands: List[str], working_dir: Optional[Path] = None,
                             output_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Execute bash commands sequentially with real-time output streaming
        
        Args:
            commands: List of bash commands to execute
            working_dir: Working directory for execution
            output_callback: Optional callback for real-time output (called with each line)
            
        Returns:
            Dict with success status, output, and error info
        """
        results = []
        all_success = True
        
        for i, command in enumerate(commands, 1):
            logger.info(f"Executing bash command {i}/{len(commands)}: {command[:100]}...")
            
            stdout_lines = []
            stderr_lines = []
            
            try:
                # Use Popen for real-time streaming
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line buffered
                )
                
                # Stream stdout in real-time
                if process.stdout:
                    for line in process.stdout:
                        line = line.rstrip('\n')
                        stdout_lines.append(line)
                        if output_callback:
                            output_callback(line)
                
                # Stream stderr in real-time
                if process.stderr:
                    for line in process.stderr:
                        line = line.rstrip('\n')
                        stderr_lines.append(line)
                        if output_callback:
                            output_callback(f"[stderr] {line}")
                
                # Wait for process to complete
                process.wait(timeout=3600)  # 1 hour timeout
                
                stdout = '\n'.join(stdout_lines)
                stderr = '\n'.join(stderr_lines)
                
                # Add final output to thinking content
                if output_callback:
                    if stdout:
                        output_callback(f"[stdout complete]\n{stdout}")
                    if stderr:
                        output_callback(f"[stderr complete]\n{stderr}")
                
                results.append({
                    "command": command,
                    "success": process.returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": process.returncode
                })
                
                if process.returncode != 0:
                    logger.error(f"Command failed with return code {process.returncode}")
                    logger.error(f"stderr: {stderr}")
                    all_success = False
                    # Stop on first error
                    break
                else:
                    logger.info(f"Command {i} succeeded")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Command timed out after 1 hour")
                results.append({
                    "command": command,
                    "success": False,
                    "stdout": '\n'.join(stdout_lines),
                    "stderr": "Command timed out after 1 hour",
                    "returncode": -1
                })
                all_success = False
                process.kill()  # Ensure process is terminated
                break
            except Exception as e:
                logger.error(f"Command execution error: {e}")
                results.append({
                    "command": command,
                    "success": False,
                    "stdout": '\n'.join(stdout_lines),
                    "stderr": str(e),
                    "returncode": -1
                })
                all_success = False
                break
        
        return {
            "success": all_success,
            "results": results,
            "total_commands": len(commands),
            "executed_commands": len(results)
        }
    
    def _prepare_variable_substitutions(self, context: ExecutionContext, 
                                       skill_path: Path) -> Dict[str, str]:
        """Prepare variable substitutions for command templates
        
        Args:
            context: Execution context
            skill_path: Path to the skill directory
        
        Returns:
            Dictionary mapping variable names to values
        """
        substitutions = {}
        
        # Get input file from arguments
        if context.arguments:
            input_file = context.arguments[0] if context.arguments else ""
            substitutions["INPUT_FILE"] = input_file
            
            # Generate output file name
            if input_file:
                # Remove extension and add _transcription.txt
                input_path = Path(input_file)
                output_file = str(input_path.parent / f"{input_path.stem}_transcription.txt")
                substitutions["OUTPUT_FILE"] = output_file
                
                # Generate temp audio file name (same directory, same basename with .wav)
                temp_audio_file = str(input_path.parent / f"{input_path.stem}.wav")
                substitutions["TEMP_AUDIO_FILE"] = temp_audio_file
                
                # Generate chunk directory name (same directory, same basename with _chunks)
                chunk_dir = str(input_path.parent / f"{input_path.stem}_chunks")
                substitutions["CHUNK_DIR"] = chunk_dir
            else:
                substitutions["OUTPUT_FILE"] = str(Path.home() / "Downloads/workspace/transcription.txt")
                substitutions["TEMP_AUDIO_FILE"] = str(Path.home() / "Downloads/workspace/extracted_audio.wav")
                substitutions["CHUNK_DIR"] = str(Path.home() / "Downloads/workspace/audio_chunks")
        else:
            substitutions["INPUT_FILE"] = ""
            substitutions["OUTPUT_FILE"] = str(Path.home() / "Downloads/workspace/transcription.txt")
            substitutions["TEMP_AUDIO_FILE"] = str(Path.home() / "Downloads/workspace/extracted_audio.wav")
            substitutions["CHUNK_DIR"] = str(Path.home() / "Downloads/workspace/audio_chunks")
        
        # Fixed substitutions
        substitutions["SKILL_PATH"] = str(skill_path)
        
        return substitutions
    
    def prepare_execution(self, manifest: SkillManifest, 
                         arguments: List[str] = None,
                         session_id: Optional[str] = None,
                         working_dir: Optional[Path] = None,
                         output_callback: Optional[Callable[[str], None]] = None) -> ExecutionContext:
        """Prepare execution context from manifest
        
        Sets up:
        - Permission manager from allowed-tools
        - Subagent configuration from context/agent fields
        - Variable substitution context
        - Real-time output callback
        """
        context = ExecutionContext(
            session_id=session_id,
            arguments=arguments or [],
            working_dir=working_dir,
            env_vars={},
            output_callback=output_callback
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
        - Extracted executable commands from bash:execute blocks
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
        
        # Extract executable commands from bash:execute blocks
        execute_commands = self.extract_execute_commands(
            manifest.level2.body_content,
            context,
            manifest.path
        )
        
        # Add executable commands section if available
        if execute_commands:
            prompt_parts.append("\n## Execute Commands\n")
            for i, cmd in enumerate(execute_commands, 1):
                prompt_parts.append(f"**Step {i}:**\n```bash\n{cmd}\n```")
            prompt_parts.append("\nExecute these commands to complete the task.\n")
        
        # Add body content (documentation)
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
        
        If bash:execute commands exist, actually execute them.
        Otherwise, returns the prompt content for the LLM to execute.
        """
        # Check if skill has bash:execute commands
        if manifest.level2 and manifest.level2.body_content:
            commands = self.extract_execute_commands(
                manifest.level2.body_content,
                context,
                manifest.path
            )
            
            if commands:
                # Actually execute the bash commands
                logger.info(f"Executing {len(commands)} bash commands for skill {manifest.name}")
                bash_result = self.execute_bash_commands(commands, context.working_dir, context.output_callback)
                
                # Record execution
                execution_record = {
                    "skill_name": manifest.name,
                    "session_id": context.session_id,
                    "context": "inline_bash",
                    "agent_type": context.agent_type,
                    "arguments": context.arguments,
                    "bash_commands": commands,
                    "bash_result": bash_result,
                }
                self._execution_history.append(execution_record)
                context.execution_count += 1
                context.last_execution = manifest.name
                
                # Return the actual execution result
                return {
                    "success": bash_result["success"],
                    "type": "inline_bash",
                    "bash_result": bash_result,
                    "manifest": manifest.to_dict(
                        include_level1=True,
                        include_level2=True,
                        include_level3=False
                    ),
                    "permissions": self._get_permission_info(context),
                }
        
        # No bash commands - return prompt for LLM execution
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
                working_dir: Optional[Path] = None,
                output_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Execute a skill (main entry point)
        
        Automatically determines inline vs subagent execution
        based on manifest context setting.
        """
        # Prepare execution context
        context = self.prepare_execution(
            manifest=manifest,
            arguments=arguments or [],
            session_id=session_id,
            working_dir=working_dir,
            output_callback=output_callback
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
