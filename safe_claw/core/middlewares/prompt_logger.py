"""Prompt Logger Middleware for capturing and logging LLM prompts and responses."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from deepagents.graph import AgentMiddleware

logger = logging.getLogger(__name__)

# Thread-safe storage for LLM call logs (shared with official_integration)
_llm_call_logs_lock = None
_llm_call_logs: Dict[str, List[Dict[str, Any]]] = {}


def set_llm_call_logs_storage(lock, storage: Dict[str, List[Dict[str, Any]]]):
    """Set the shared storage for LLM call logs from the integration module."""
    global _llm_call_logs_lock, _llm_call_logs
    _llm_call_logs_lock = lock
    _llm_call_logs = storage


class PromptLoggerMiddleware(AgentMiddleware):
    """Enhanced middleware to capture and log both LLM prompts and responses"""

    def __init__(self, log_file: Optional[str] = None, print_to_console: bool = True):
        self.log_file = log_file
        self.print_to_console = print_to_console
        self._call_counter = 0
        # Track active calls: runtime_id -> {message_id, prompt_data}
        self._active_calls: Dict[str, Dict[str, Any]] = {}

    def before_model(self, state, runtime):
        """Called before the model is invoked - captures the prompt"""
        self._call_counter += 1

        # Extract messages from state
        messages = state.get("messages", [])
        if not messages:
            return state

        # Get session/message context from state
        session_id = state.get("session_id", "unknown")
        user_id = state.get("user_id", "unknown")
        # Generate a unique message identifier for this execution
        message_id = state.get("message_id", f"{session_id}_{self._call_counter}")

        # Format the prompt for display
        prompt_text = self._format_prompt(messages)
        serialized_messages = self._serialize_messages(messages)

        # Create unique call ID
        call_id = f"call_{self._call_counter}_{datetime.now().strftime('%H%M%S%f')}"

        # Store prompt data for response association
        prompt_data = {
            "call_id": call_id,
            "message_id": message_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "call_number": self._call_counter,
            "messages": serialized_messages,
            "formatted_prompt": prompt_text,
            "token_estimate": len(prompt_text.split()) * 1.3,
            "response": None,  # Will be filled in after_model
            "response_timestamp": None,
            "response_tokens": None,
            "duration_ms": None,
        }

        # Store in active calls for later association with response
        runtime_id = id(runtime) if runtime else call_id
        self._active_calls[runtime_id] = prompt_data

        # Log to shared storage (prompt only initially)
        if _llm_call_logs_lock:
            with _llm_call_logs_lock:
                if message_id not in _llm_call_logs:
                    _llm_call_logs[message_id] = []
                _llm_call_logs[message_id].append(prompt_data)

        # Log to console
        if self.print_to_console:
            print(f"\n{'=' * 80}")
            print(f"🔍 LLM CALL #{self._call_counter} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"📨 Message: {message_id[:50]}...")
            print(f"📊 Estimated tokens: {prompt_data['token_estimate']:.0f}")
            print(f"{'=' * 80}")
            print(prompt_text)
            print(f"{'=' * 80}\n")

        # Log to file if specified
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "type": "prompt",
                        **prompt_data
                    }, indent=2, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error(f"Failed to write prompt log to file: {e}")

        # Log using standard logger
        logger.info(
            f"🔍 LLM CALL #{self._call_counter} [{message_id[:20]}...]: "
            f"{prompt_data['token_estimate']:.0f} tokens, {len(messages)} messages")

        return state

    def after_model(self, state, runtime):
        """Called after the model responds - captures the response"""
        runtime_id = id(runtime) if runtime else None

        if runtime_id and runtime_id in self._active_calls:
            prompt_data = self._active_calls.pop(runtime_id)
            message_id = prompt_data["message_id"]
            call_id = prompt_data["call_id"]

            # Extract response content from state (messages last item is the assistant response)
            messages = state.get("messages", []) if isinstance(state, dict) else []
            response_text = ""
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    response_text = last_msg.get("content", "")
                elif hasattr(last_msg, 'content'):
                    response_text = str(last_msg.content)
                else:
                    response_text = str(last_msg)
            response_tokens = len(response_text.split()) if response_text else 0

            # Calculate duration
            prompt_time = datetime.fromisoformat(prompt_data["timestamp"])
            response_time = datetime.now()
            duration_ms = (response_time - prompt_time).total_seconds() * 1000

            # Update stored data with response
            updated_data = {
                **prompt_data,
                "response": response_text,
                "response_timestamp": response_time.isoformat(),
                "response_tokens": response_tokens,
                "duration_ms": round(duration_ms, 2),
            }

            # Update in shared storage
            if _llm_call_logs_lock:
                with _llm_call_logs_lock:
                    if message_id in _llm_call_logs:
                        for i, call in enumerate(_llm_call_logs[message_id]):
                            if call["call_id"] == call_id:
                                _llm_call_logs[message_id][i] = updated_data
                                break

            # Log to console
            if self.print_to_console:
                print(f"\n{'=' * 80}")
                print(f"✅ LLM RESPONSE #{prompt_data['call_number']} - {response_time.strftime('%H:%M:%S')}")
                print(f"⏱️  Duration: {duration_ms:.0f}ms | 📤 Response tokens: {response_tokens}")
                print(f"{'=' * 80}")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                print(f"{'=' * 80}\n")

            # Log to file
            if self.log_file:
                try:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "type": "response",
                            "call_id": call_id,
                            "message_id": message_id,
                            "timestamp": response_time.isoformat(),
                            "response": response_text,
                            "response_tokens": response_tokens,
                            "duration_ms": duration_ms,
                        }, indent=2, ensure_ascii=False) + "\n")
                except Exception as e:
                    logger.error(f"Failed to write response log to file: {e}")

            logger.info(
                f"✅ LLM RESPONSE #{prompt_data['call_number']} [{message_id[:20]}...]: "
                f"{response_tokens} tokens, {duration_ms:.0f}ms")

        return state

    def _extract_response_text(self, response) -> str:
        """Extract text content from various response formats"""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            # Handle dict response
            if "content" in response:
                return str(response["content"])
            elif "message" in response and "content" in response["message"]:
                return str(response["message"]["content"])
            else:
                return json.dumps(response, ensure_ascii=False)
        elif hasattr(response, 'content'):
            # LangChain message object
            return str(response.content)
        elif hasattr(response, 'dict'):
            # Pydantic model
            try:
                return str(response.dict().get("content", str(response)))
            except:
                return str(response)
        else:
            return str(response)

    def _serialize_messages(self, messages: List) -> List[Dict]:
        """Serialize messages (both dict and LangChain objects) to dict format"""
        serialized = []
        for msg in messages:
            if hasattr(msg, 'dict'):  # LangChain message object
                msg_dict = msg.dict()
                serialized.append({
                    "role": self._get_role_from_message(msg),
                    "content": self._stringify_content(msg.content)
                })
            elif isinstance(msg, dict):  # Already a dict
                serialized.append(msg)
            else:
                serialized.append({
                    "role": "unknown",
                    "content": str(msg)
                })
        return serialized

    def _stringify_content(self, content) -> str:
        """Render message content as readable text.

        Multimodal content (list of parts) is collapsed to its text parts plus
        compact placeholders for images, so base64 data URLs don't bloat logs.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if not isinstance(part, dict):
                    parts.append(str(part))
                    continue
                ptype = part.get("type")
                if ptype == "text":
                    parts.append(part.get("text", ""))
                elif ptype == "image_url":
                    url = (part.get("image_url") or {}).get("url", "")
                    if url.startswith("data:"):
                        mime = url[5:].split(";", 1)[0] or "image"
                        parts.append(f"[image: {mime}, {len(url)} bytes base64]")
                    else:
                        parts.append(f"[image: {url}]")
                else:
                    parts.append(f"[{ptype}]")
            return "\n".join(parts)
        return str(content)

    def _get_role_from_message(self, msg) -> str:
        """Extract role from LangChain message object"""
        msg_type = type(msg).__name__.lower()
        if "human" in msg_type:
            return "user"
        elif "ai" in msg_type or "assistant" in msg_type:
            return "assistant"
        elif "system" in msg_type:
            return "system"
        elif "tool" in msg_type or "function" in msg_type:
            return "tool"
        else:
            return "unknown"

    def _format_prompt(self, messages: List) -> str:
        """Format messages into a readable prompt string"""
        formatted_parts = []

        for msg in messages:
            if hasattr(msg, 'content'):  # LangChain message object
                role = self._get_role_from_message(msg)
                content = self._stringify_content(msg.content)
                tool_name = getattr(msg, 'name', None)
            elif isinstance(msg, dict):  # Dict message
                role = msg.get("role", "unknown")
                content = self._stringify_content(msg.get("content", ""))
                tool_name = msg.get("name")
            else:
                role = "unknown"
                content = str(msg)
                tool_name = None

            # Format based on role
            if role == "system":
                formatted_parts.append(f"🔧 SYSTEM:\n{content}")
            elif role == "user":
                formatted_parts.append(f"👤 USER:\n{content}")
            elif role == "assistant":
                formatted_parts.append(f"🤖 ASSISTANT:\n{content}")
            elif role == "tool":
                tool_name = tool_name or "unknown_tool"
                formatted_parts.append(f"🔧 TOOL ({tool_name}):\n{content}")
            else:
                formatted_parts.append(f"📝 {role}:\n{content}")

        return "\n\n".join(formatted_parts)
