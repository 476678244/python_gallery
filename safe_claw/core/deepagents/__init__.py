"""Simplified DeepAgent with Middleware Architecture"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Execution context for DeepAgent"""
    session_id: str
    user_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result from DeepAgent execution"""
    success: bool
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Middleware(ABC):
    """Base middleware interface"""
    
    @abstractmethod
    async def before_execution(self, context: ExecutionContext, input_data: str) -> tuple[str, Dict[str, Any]]:
        """Process before execution"""
        pass
    
    @abstractmethod
    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> ExecutionResult:
        """Process after execution"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Middleware name"""
        pass


class MemoryMiddleware(Middleware):
    """Memory management middleware"""
    
    def __init__(self, memory_backend):
        self.memory_backend = memory_backend
    
    @property
    def name(self) -> str:
        return "memory"
    
    async def before_execution(self, context: ExecutionContext, input_data: str) -> tuple[str, Dict[str, Any]]:
        """Retrieve relevant memories before execution"""
        try:
            # Get relevant memories based on input
            relevant_memories = await self.memory_backend.search_memories(input_data, context.session_id)
            
            # Add memories to context metadata
            context.metadata["relevant_memories"] = relevant_memories
            
            # Prepend memory context to input
            if relevant_memories:
                memory_context = "\n\nRelevant memories:\n" + "\n".join([f"- {mem}" for mem in relevant_memories[:3]])
                enhanced_input = f"{memory_context}\n\nUser input: {input_data}"
            else:
                enhanced_input = input_data
                
            return enhanced_input, context.metadata
            
        except Exception as e:
            logger.error(f"Memory middleware error: {e}")
            return input_data, context.metadata
    
    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> ExecutionResult:
        """Store execution result in memory"""
        try:
            # Store the interaction in memory
            await self.memory_backend.store_interaction(
                session_id=context.session_id,
                input_data=context.metadata.get("original_input", ""),
                response=result.content,
                timestamp=context.timestamp
            )
            return result
        except Exception as e:
            logger.error(f"Memory storage error: {e}")
            return result


class SandboxMiddleware(Middleware):
    """Sandbox execution middleware"""
    
    def __init__(self, sandbox_config: Dict[str, Any] = None):
        self.sandbox_config = sandbox_config or {}
        self.allowed_operations = self.sandbox_config.get("allowed_operations", [])
        self.dangerous_operations = self.sandbox_config.get("dangerous_operations", ["rm", "format", "delete"])
    
    @property
    def name(self) -> str:
        return "sandbox"
    
    async def before_execution(self, context: ExecutionContext, input_data: str) -> tuple[str, Dict[str, Any]]:
        """Check input for dangerous operations"""
        # Check for dangerous operations
        for dangerous_op in self.dangerous_operations:
            if dangerous_op.lower() in input_data.lower():
                error_msg = f"Dangerous operation detected: {dangerous_op}. This operation is not allowed."
                context.metadata["sandbox_blocked"] = True
                context.metadata["block_reason"] = error_msg
                return "", context.metadata
        
        return input_data, context.metadata
    
    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> ExecutionResult:
        """Validate execution results"""
        if context.metadata.get("sandbox_blocked"):
            result.success = False
            result.error_message = context.metadata.get("block_reason", "Operation blocked by sandbox")
            result.content = ""
        
        return result


class LogMiddleware(Middleware):
    """Logging middleware"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self.execution_log: List[Dict[str, Any]] = []
    
    @property
    def name(self) -> str:
        return "log"
    
    async def before_execution(self, context: ExecutionContext, input_data: str) -> tuple[str, Dict[str, Any]]:
        """Log execution start"""
        log_entry = {
            "timestamp": context.timestamp.isoformat(),
            "session_id": context.session_id,
            "request_id": context.request_id,
            "event": "execution_start",
            "input_length": len(input_data)
        }
        self.execution_log.append(log_entry)
        logger.info(f"DeepAgent execution started: {context.request_id}")
        
        # Store original input for memory middleware
        context.metadata["original_input"] = input_data
        return input_data, context.metadata
    
    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> ExecutionResult:
        """Log execution completion"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": context.session_id,
            "request_id": context.request_id,
            "event": "execution_complete",
            "success": result.success,
            "response_length": len(result.content),
            "execution_time": result.execution_time,
            "tool_calls_count": len(result.tool_calls)
        }
        if result.error_message:
            log_entry["error"] = result.error_message
        
        self.execution_log.append(log_entry)
        logger.info(f"DeepAgent execution completed: {context.request_id}, success: {result.success}")
        
        return result


class DeepAgent:
    """Simplified DeepAgent with middleware support"""
    
    def __init__(self, llm_service, system_prompt: str = None):
        self.llm_service = llm_service
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.middleware_stack: List[Middleware] = []
        self.execution_count = 0
        
        # Add default middleware
        self.add_middleware(LogMiddleware())
        self.add_middleware(SandboxMiddleware())
        self.add_middleware(MemoryMiddleware(None))  # Will be configured later
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware to the stack"""
        self.middleware_stack.append(middleware)
    
    def remove_middleware(self, middleware_name: str):
        """Remove middleware by name"""
        self.middleware_stack = [m for m in self.middleware_stack if m.name != middleware_name]
    
    def set_memory_backend(self, memory_backend):
        """Set memory backend for memory middleware"""
        for middleware in self.middleware_stack:
            if isinstance(middleware, MemoryMiddleware):
                middleware.memory_backend = memory_backend
                break
    
    async def execute(self, input_data: str, context: ExecutionContext) -> ExecutionResult:
        """Execute input through middleware stack and LLM"""
        start_time = datetime.now()
        
        try:
            # Process through middleware stack (before execution)
            processed_input = input_data
            for middleware in self.middleware_stack:
                processed_input, context.metadata = await middleware.before_execution(context, processed_input)
            
            # Check if execution was blocked
            if context.metadata.get("sandbox_blocked"):
                result = ExecutionResult(success=False, content="", error_message=context.metadata.get("block_reason"))
            else:
                # Execute with LLM
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": processed_input}
                ]
                
                response = await self.llm_service.ainvoke(messages)
                result = ExecutionResult(success=True, content=response)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Process through middleware stack (after execution)
            for middleware in reversed(self.middleware_stack):
                result = await middleware.after_execution(context, result)
            
            self.execution_count += 1
            return result
            
        except Exception as e:
            logger.error(f"DeepAgent execution error: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                success=False,
                content="",
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def stream_execute(self, input_data: str, context: ExecutionContext) -> Iterator[str]:
        """Stream execution with middleware support"""
        start_time = datetime.now()
        
        try:
            # Process through middleware stack (before execution)
            processed_input = input_data
            for middleware in self.middleware_stack:
                processed_input, context.metadata = await middleware.before_execution(context, processed_input)
            
            # Check if execution was blocked
            if context.metadata.get("sandbox_blocked"):
                error_msg = context.metadata.get("block_reason", "Operation blocked")
                yield f"Error: {error_msg}"
                return
            
            # Stream from LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": processed_input}
            ]
            
            full_response = ""
            async for chunk in self.llm_service.astream(messages):
                full_response += chunk
                yield chunk
            
            # Create final result for middleware processing
            execution_time = (datetime.now() - start_time).total_seconds()
            result = ExecutionResult(success=True, content=full_response, execution_time=execution_time)
            
            # Process through middleware stack (after execution)
            for middleware in reversed(self.middleware_stack):
                result = await middleware.after_execution(context, result)
            
            self.execution_count += 1
            
        except Exception as e:
            logger.error(f"DeepAgent stream execution error: {e}")
            yield f"Error: {str(e)}"
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "execution_count": self.execution_count,
            "middleware_stack": [m.name for m in self.middleware_stack],
            "middleware_count": len(self.middleware_stack),
            "system_prompt_length": len(self.system_prompt)
        }
    
    def get_middleware_logs(self, middleware_name: str) -> List[Dict[str, Any]]:
        """Get logs from specific middleware"""
        for middleware in self.middleware_stack:
            if middleware.name == middleware_name and hasattr(middleware, 'execution_log'):
                return middleware.execution_log
        return []
