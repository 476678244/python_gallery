"""Configuration service for SafeClaw"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from safe_claw.models.config import SafeClawConfig, LLMConfig, SafetyConfig, MemoryConfig

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for managing SafeClaw configuration"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.config_file = self.workspace_path / "config.json"
        
        # Default configuration
        self.default_config = SafeClawConfig(
            llm=LLMConfig(
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=2000
            ),
            safety=SafetyConfig(
                enable_confirmation=True,
                blacklist_commands=["rm -rf /", "format", "mkfs"],
                whitelist_operations=["read_file", "chat"]
            ),
            memory=MemoryConfig(
                enable_vector_search=False,
                active_memory_max=20,
                dormant_wakeup_threshold=0.6,
                deep_memory_compression="maximum"
            ),
            debug=False,
            log_level="INFO"
        )
        
        # Load or create configuration
        self._config = self._load_config()
        
        logger.info("Configuration service initialized")
    
    @property
    def config(self) -> SafeClawConfig:
        """Get current configuration"""
        return self._config
    
    def get_config(self) -> SafeClawConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, config: SafeClawConfig) -> bool:
        """Update configuration"""
        try:
            # Create a copy of the config to avoid reference issues
            self._config = SafeClawConfig(
                llm=LLMConfig(**config.llm.dict()),
                safety=SafetyConfig(**config.safety.dict()),
                memory=MemoryConfig(**config.memory.dict()),
                debug=config.debug,
                log_level=config.log_level
            )
            return self._save_config()
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
    
    def update_llm_config(self, llm_config: LLMConfig) -> bool:
        """Update LLM configuration"""
        try:
            self._config.llm = llm_config
            return self._save_config()
        except Exception as e:
            logger.error(f"Error updating LLM configuration: {e}")
            return False
    
    def update_safety_config(self, safety_config: SafetyConfig) -> bool:
        """Update safety configuration"""
        try:
            self._config.safety = safety_config
            return self._save_config()
        except Exception as e:
            logger.error(f"Error updating safety configuration: {e}")
            return False
    
    def update_memory_config(self, memory_config: MemoryConfig) -> bool:
        """Update memory configuration"""
        try:
            self._config.memory = memory_config
            return self._save_config()
        except Exception as e:
            logger.error(f"Error updating memory configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            # Create a copy of the default config
            self._config = SafeClawConfig(
                llm=LLMConfig(**self.default_config.llm.dict()),
                safety=SafetyConfig(**self.default_config.safety.dict()),
                memory=MemoryConfig(**self.default_config.memory.dict()),
                debug=self.default_config.debug,
                log_level=self.default_config.log_level
            )
            return self._save_config()
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False
    
    def get_llm_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get available LLM providers and their models"""
        providers = {
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
                "requires_api_key": True,
                "base_url": "https://api.openai.com/v1"
            },
            "anthropic": {
                "name": "Anthropic",
                "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                "requires_api_key": True,
                "base_url": "https://api.anthropic.com"
            },
            "ollama": {
                "name": "Ollama",
                "models": ["llama2", "llama3", "mistral", "codellama", "phi"],
                "requires_api_key": False,
                "base_url": "http://localhost:11434"
            }
        }
        return providers
    
    def validate_config(self, config: SafeClawConfig) -> tuple[bool, List[str]]:
        """Validate configuration"""
        errors = []
        
        # Validate LLM config
        if not config.llm.provider:
            errors.append("LLM provider is required")
        
        if not config.llm.model:
            errors.append("LLM model is required")
        
        if config.llm.provider in ["openai", "anthropic"] and not config.llm.api_key:
            errors.append(f"API key required for {config.llm.provider}")
        
        # Validate temperature
        if not 0.0 <= config.llm.temperature <= 2.0:
            errors.append("LLM temperature must be between 0.0 and 2.0")
        
        # Validate max tokens
        if not 100 <= config.llm.max_tokens <= 8000:
            errors.append("LLM max tokens must be between 100 and 8000")
        
        # Validate memory config
        if not 5 <= config.memory.active_memory_max <= 100:
            errors.append("Active memory max must be between 5 and 100")
        
        if not 0.0 <= config.memory.dormant_wakeup_threshold <= 1.0:
            errors.append("Dormant wakeup threshold must be between 0.0 and 1.0")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level not in valid_log_levels:
            errors.append(f"Log level must be one of: {', '.join(valid_log_levels)}")
        
        return len(errors) == 0, errors
    
    def export_config(self, format: str = "json") -> str:
        """Export configuration"""
        if format == "json":
            return json.dumps(self._config.dict(), indent=2)
        elif format == "env":
            return self._config_to_env()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_config(self, config_data: str, format: str = "json") -> bool:
        """Import configuration"""
        try:
            if format == "json":
                config_dict = json.loads(config_data)
                config = SafeClawConfig(**config_dict)
            elif format == "env":
                config = self._env_to_config(config_data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # Validate before importing
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                logger.error(f"Invalid configuration: {errors}")
                return False
            
            return self.update_config(config)
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_config_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        history_file = self.workspace_path / "config_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Sort by timestamp and limit
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error loading config history: {e}")
            return []
    
    def backup_config(self) -> str:
        """Create a backup of current configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.workspace_path / f"config_backup_{timestamp}.json"
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(self._config.dict(), f, indent=2, default=str)
            
            logger.info(f"Configuration backed up to {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
            return ""
    
    def restore_config(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            with open(backup_path, 'r') as f:
                config_dict = json.load(f)
            
            config = SafeClawConfig(**config_dict)
            return self.update_config(config)
            
        except Exception as e:
            logger.error(f"Error restoring configuration: {e}")
            return False
    
    def _load_config(self) -> SafeClawConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)
                
                config = SafeClawConfig(**config_dict)
                
                # Validate loaded config
                is_valid, errors = self.validate_config(config)
                if not is_valid:
                    logger.warning(f"Invalid configuration found: {errors}. Using defaults.")
                    # Return a copy of default config
                    return SafeClawConfig(
                        llm=LLMConfig(**self.default_config.llm.dict()),
                        safety=SafetyConfig(**self.default_config.safety.dict()),
                        memory=MemoryConfig(**self.default_config.memory.dict()),
                        debug=self.default_config.debug,
                        log_level=self.default_config.log_level
                    )
                
                return config
                
            except Exception as e:
                logger.error(f"Error loading configuration: {e}. Using defaults.")
                # Return a copy of default config
                return SafeClawConfig(
                    llm=LLMConfig(**self.default_config.llm.dict()),
                    safety=SafetyConfig(**self.default_config.safety.dict()),
                    memory=MemoryConfig(**self.default_config.memory.dict()),
                    debug=self.default_config.debug,
                    log_level=self.default_config.log_level
                )
        else:
            # Create default config file
            # Return a copy of default config, not the reference
            default_copy = SafeClawConfig(
                llm=LLMConfig(**self.default_config.llm.dict()),
                safety=SafetyConfig(**self.default_config.safety.dict()),
                memory=MemoryConfig(**self.default_config.memory.dict()),
                debug=self.default_config.debug,
                log_level=self.default_config.log_level
            )
            # Set _config temporarily to default to allow saving
            self._config = default_copy
            self._save_config()
            return default_copy
    
    def _save_config(self) -> bool:
        """Save configuration to file"""
        try:
            # Ensure workspace exists
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Save current config
            with open(self.config_file, 'w') as f:
                json.dump(self._config.dict(), f, indent=2, default=str)
            
            # Add to history
            self._add_to_history()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _add_to_history(self):
        """Add configuration change to history"""
        history_file = self.workspace_path / "config_history.json"
        
        try:
            # Load existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new entry
            history.append({
                "timestamp": datetime.now().isoformat(),
                "config": self._config.dict()
            })
            
            # Keep only last 50 entries
            history = history[-50:]
            
            # Save history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error adding to config history: {e}")
    
    def _config_to_env(self) -> str:
        """Convert configuration to environment format"""
        env_lines = []
        
        # LLM config
        env_lines.append(f"LLM_PROVIDER={self._config.llm.provider}")
        env_lines.append(f"LLM_MODEL={self._config.llm.model}")
        env_lines.append(f"LLM_TEMPERATURE={self._config.llm.temperature}")
        env_lines.append(f"LLM_MAX_TOKENS={self._config.llm.max_tokens}")
        if self._config.llm.api_key:
            env_lines.append(f"LLM_API_KEY={self._config.llm.api_key}")
        if self._config.llm.base_url:
            env_lines.append(f"LLM_BASE_URL={self._config.llm.base_url}")
        
        # Safety config
        env_lines.append(f"SAFETY_ENABLE_CONFIRMATION={self._config.safety.enable_confirmation}")
        env_lines.append(f"SAFETY_BLACKLIST_COMMANDS={','.join(self._config.safety.blacklist_commands)}")
        env_lines.append(f"SAFETY_WHITELIST_OPERATIONS={','.join(self._config.safety.whitelist_operations)}")
        
        # Memory config
        env_lines.append(f"MEMORY_ENABLE_VECTOR_SEARCH={self._config.memory.enable_vector_search}")
        env_lines.append(f"MEMORY_ACTIVE_MEMORY_MAX={self._config.memory.active_memory_max}")
        env_lines.append(f"MEMORY_DORMANT_WAKEUP_THRESHOLD={self._config.memory.dormant_wakeup_threshold}")
        env_lines.append(f"MEMORY_DEEP_MEMORY_COMPRESSION={self._config.memory.deep_memory_compression}")
        
        # General config
        env_lines.append(f"DEBUG={self._config.debug}")
        env_lines.append(f"LOG_LEVEL={self._config.log_level}")
        
        return "\n".join(env_lines)
    
    def _env_to_config(self, env_data: str) -> SafeClawConfig:
        """Convert environment format to configuration"""
        env_vars = {}
        for line in env_data.split('\n'):
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        # Parse environment variables
        llm_config = LLMConfig(
            provider=env_vars.get("LLM_PROVIDER", "openai"),
            model=env_vars.get("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=env_vars.get("LLM_API_KEY"),
            base_url=env_vars.get("LLM_BASE_URL"),
            temperature=float(env_vars.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(env_vars.get("LLM_MAX_TOKENS", "2000"))
        )
        
        safety_config = SafetyConfig(
            enable_confirmation=env_vars.get("SAFETY_ENABLE_CONFIRMATION", "true").lower() == "true",
            blacklist_commands=env_vars.get("SAFETY_BLACKLIST_COMMANDS", "").split(','),
            whitelist_operations=env_vars.get("SAFETY_WHITELIST_OPERATIONS", "").split(',')
        )
        
        memory_config = MemoryConfig(
            enable_vector_search=env_vars.get("MEMORY_ENABLE_VECTOR_SEARCH", "false").lower() == "true",
            active_memory_max=int(env_vars.get("MEMORY_ACTIVE_MEMORY_MAX", "20")),
            dormant_wakeup_threshold=float(env_vars.get("MEMORY_DORMANT_WAKEUP_THRESHOLD", "0.6")),
            deep_memory_compression=env_vars.get("MEMORY_DEEP_MEMORY_COMPRESSION", "maximum")
        )
        
        return SafeClawConfig(
            llm=llm_config,
            safety=safety_config,
            memory=memory_config,
            debug=env_vars.get("DEBUG", "false").lower() == "true",
            log_level=env_vars.get("LOG_LEVEL", "INFO")
        )
