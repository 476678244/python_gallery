"""Configuration models for SafeClaw"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    context_length: int = Field(default=4096, gt=0)
    show_thinking: bool = False


class SafetyConfig(BaseModel):
    """Safety configuration"""
    enable_confirmation: bool = True
    blacklist_commands: List[str] = [
        "rm -rf /", "format", "mkfs"
    ]
    whitelist_operations: List[str] = [
        "read_file", "chat"
    ]


class MemoryConfig(BaseModel):
    """Memory system configuration"""
    enable_vector_search: bool = False
    max_active_memories: int = 20
    memory_retention_days: int = 30
    dormant_wakeup_threshold: float = 0.6
    deep_memory_compression: str = "maximum"


class SafeClawConfig(BaseModel):
    """Main configuration for SafeClaw"""
    llm: LLMConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    debug: bool = False
    log_level: str = "INFO"
