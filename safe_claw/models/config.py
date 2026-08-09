"""Configuration models for SafeClaw"""

from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, Literal, Optional, List


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: Literal["openai", "anthropic", "ollama", "google", "deepseek"]
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
    # Auto-write chat turns only when importance >= this threshold
    auto_write_min_importance: float = Field(default=0.6, ge=0.0, le=1.0)
    # Dormant → deep after this many days without access (and low importance)
    dormant_to_deep_days: int = Field(default=14, gt=0)

    @model_validator(mode="before")
    @classmethod
    def _alias_active_memory_max(cls, data: Any) -> Any:
        if isinstance(data, dict) and "active_memory_max" in data:
            data = dict(data)
            if "max_active_memories" not in data:
                data["max_active_memories"] = data["active_memory_max"]
            data.pop("active_memory_max", None)
        return data

    @property
    def active_memory_max(self) -> int:
        """Alias used by older config_service / docs."""
        return self.max_active_memories


class BackendConfig(BaseModel):
    """Backend configuration for deepagents
    
    Security-first principles:
    - Default to None (use deepagents default secure backend)
    - Only enable custom backends if explicitly configured
    - Validate all backend configurations
    """
    enabled: bool = False  # By default, use deepagents' secure default backend
    backend_type: Optional[str] = None  # Type of backend (e.g., "sqlite", "memory", "custom")
    connection_string: Optional[str] = None  # For database backends
    enable_persistence: bool = False  # Whether to enable state persistence
    enable_checkpoints: bool = False  # Whether to enable checkpointing
    max_state_size_mb: int = Field(default=100, gt=0, le=1000)  # Limit state size for security
    encrypt_state: bool = True  # Encrypt persisted state for security
    allow_network_access: bool = False  # Deny network access by default for security


class SafeClawConfig(BaseModel):
    """Main configuration for SafeClaw"""
    llm: LLMConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    debug: bool = False
    log_level: str = "INFO"
