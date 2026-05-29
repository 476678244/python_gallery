"""Secure Backend Implementation for SafeClaw

Implements:
1. SecureBackend - State persistence with encryption (for LangGraph checkpointer)
2. SecureFilesystemBackend - DeepAgents BackendProtocol with encryption (for file operations)
"""

import json
import logging
import hashlib
import os
import re
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class BackendConfig:
    """Configuration for secure backend"""
    enabled: bool = False
    backend_type: str = "file_encrypted"  # file_encrypted, memory, custom
    enable_persistence: bool = True
    enable_checkpoints: bool = True
    encrypt_state: bool = True  # REQUIRED for security
    allow_network_access: bool = False  # MUST be False for security
    storage_path: Optional[str] = None
    encryption_key: Optional[str] = None  # Derived if not provided
    max_checkpoints: int = 100
    checkpoint_interval: int = 60  # seconds


class SecureBackend:
    """Secure backend implementation with encryption and persistence"""
    
    def __init__(self, config: BackendConfig, workspace_path: Path):
        self.config = config
        self.workspace_path = workspace_path
        self.storage_path = Path(config.storage_path) if config.storage_path else workspace_path / "backend_state"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self._fernet: Optional[Fernet] = None
        if config.encrypt_state:
            self._init_encryption()
        
        # State storage
        self._state_cache: Dict[str, Any] = {}
        self._checkpoint_index: List[Dict[str, Any]] = []
        
        logger.info(f"SecureBackend initialized with type={config.backend_type}, encryption={config.encrypt_state}")
    
    def _init_encryption(self):
        """Initialize encryption key"""
        if self.config.encryption_key:
            # Use provided key
            key_bytes = self.config.encryption_key.encode() if isinstance(self.config.encryption_key, str) else self.config.encryption_key
            # Ensure key is 32 bytes for Fernet
            if len(key_bytes) < 32:
                key_bytes = key_bytes.ljust(32, b'\0')
            else:
                key_bytes = key_bytes[:32]
            self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
        else:
            # Derive key from workspace path (deterministic but not exposed)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'safe_claw_salt',  # Fixed salt for reproducibility
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(str(self.storage_path).encode()))
            self._fernet = Fernet(key)
        
        logger.info("Encryption initialized with Fernet")
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet"""
        if not self._fernet:
            return data
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet"""
        if not self._fernet:
            return encrypted_data
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - data may be corrupted")
    
    def save_state(self, thread_id: str, checkpoint_id: str, state: Dict[str, Any]) -> bool:
        """Save state with optional encryption"""
        try:
            # Serialize state
            state_json = json.dumps(state, default=str, indent=2)
            
            # Encrypt if enabled
            if self.config.encrypt_state:
                state_json = self._encrypt_data(state_json)
            
            # Save to file
            thread_dir = self.storage_path / thread_id
            thread_dir.mkdir(parents=True, exist_ok=True)
            
            checkpoint_file = thread_dir / f"checkpoint_{checkpoint_id}.json"
            with open(checkpoint_file, 'w') as f:
                f.write(state_json)
            
            # Update checkpoint index
            self._update_checkpoint_index(thread_id, checkpoint_id, checkpoint_file)
            
            # Update cache
            self._state_cache[f"{thread_id}:{checkpoint_id}"] = state
            
            logger.debug(f"Saved state for thread={thread_id}, checkpoint={checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load state with optional decryption"""
        try:
            # Check cache first
            cache_key = f"{thread_id}:{checkpoint_id}"
            if cache_key in self._state_cache:
                return self._state_cache[cache_key]
            
            # Load from file
            thread_dir = self.storage_path / thread_id
            checkpoint_file = thread_dir / f"checkpoint_{checkpoint_id}.json"
            
            if not checkpoint_file.exists():
                logger.warning(f"Checkpoint not found: {checkpoint_file}")
                return None
            
            with open(checkpoint_file, 'r') as f:
                state_json = f.read()
            
            # Decrypt if enabled
            if self.config.encrypt_state:
                state_json = self._decrypt_data(state_json)
            
            # Deserialize
            state = json.loads(state_json)
            
            # Update cache
            self._state_cache[cache_key] = state
            
            logger.debug(f"Loaded state for thread={thread_id}, checkpoint={checkpoint_id}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def list_checkpoints(self, thread_id: str) -> List[str]:
        """List available checkpoints for a thread"""
        try:
            thread_dir = self.storage_path / thread_id
            if not thread_dir.exists():
                return []
            
            checkpoints = []
            for file in thread_dir.glob("checkpoint_*.json"):
                checkpoint_id = file.stem.replace("checkpoint_", "")
                checkpoints.append(checkpoint_id)
            
            return sorted(checkpoints)
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint"""
        try:
            thread_dir = self.storage_path / thread_id
            checkpoint_file = thread_dir / f"checkpoint_{checkpoint_id}.json"
            
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                
                # Remove from cache
                cache_key = f"{thread_id}:{checkpoint_id}"
                self._state_cache.pop(cache_key, None)
                
                # Update index
                self._checkpoint_index = [
                    cp for cp in self._checkpoint_index 
                    if not (cp.get("thread_id") == thread_id and cp.get("checkpoint_id") == checkpoint_id)
                ]
                
                logger.debug(f"Deleted checkpoint {checkpoint_id} for thread {thread_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    def cleanup_old_checkpoints(self, thread_id: str, keep_count: int = 10) -> int:
        """Clean up old checkpoints, keeping only the most recent N"""
        try:
            checkpoints = self.list_checkpoints(thread_id)
            
            if len(checkpoints) <= keep_count:
                return 0
            
            # Sort checkpoints by timestamp from index, not alphabetically
            # Get checkpoint info from index
            thread_checkpoints = [
                cp for cp in self._checkpoint_index 
                if cp.get("thread_id") == thread_id
            ]
            
            # Sort by timestamp (newest first)
            thread_checkpoints.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Keep only the most recent N
            checkpoints_to_keep = set(cp.get("checkpoint_id") for cp in thread_checkpoints[:keep_count])
            checkpoints_to_delete = [
                cp.get("checkpoint_id") for cp in thread_checkpoints 
                if cp.get("checkpoint_id") not in checkpoints_to_keep
            ]
            
            deleted_count = 0
            for checkpoint_id in checkpoints_to_delete:
                if self.delete_checkpoint(thread_id, checkpoint_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old checkpoints for thread {thread_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0
    
    def _update_checkpoint_index(self, thread_id: str, checkpoint_id: str, file_path: Path):
        """Update the checkpoint index for tracking"""
        index_entry = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "file_path": str(file_path),
            "timestamp": datetime.now().isoformat(),
            "size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        # Remove existing entry for this checkpoint
        self._checkpoint_index = [
            cp for cp in self._checkpoint_index 
            if not (cp.get("thread_id") == thread_id and cp.get("checkpoint_id") == checkpoint_id)
        ]
        
        # Add new entry
        self._checkpoint_index.append(index_entry)
        
        # Trim index if too large
        if len(self._checkpoint_index) > self.config.max_checkpoints:
            # Sort by timestamp and keep newest
            self._checkpoint_index.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            self._checkpoint_index = self._checkpoint_index[:self.config.max_checkpoints]
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information"""
        return {
            "backend_type": self.config.backend_type,
            "encryption_enabled": self.config.encrypt_state,
            "persistence_enabled": self.config.enable_persistence,
            "checkpoints_enabled": self.config.enable_checkpoints,
            "storage_path": str(self.storage_path),
            "cached_states": len(self._state_cache),
            "checkpoint_count": len(self._checkpoint_index),
            "max_checkpoints": self.config.max_checkpoints
        }
    
    def validate_security(self) -> tuple[bool, List[str]]:
        """Validate security configuration"""
        errors = []
        
        # Check encryption
        if not self.config.encrypt_state:
            errors.append("State encryption is not enabled")
        
        # Check network access
        if self.config.allow_network_access:
            errors.append("Network access is enabled (should be disabled for security)")
        
        # Check storage path
        if self.storage_path and not os.access(self.storage_path, os.W_OK):
            errors.append(f"Storage path is not writable: {self.storage_path}")
        
        return len(errors) == 0, errors


class BackendFactory:
    """Factory for creating secure backends"""
    
    @staticmethod
    def create_backend(config: Dict[str, Any], workspace_path: Path) -> Optional[SecureBackend]:
        """Create a secure backend from configuration
        
        Args:
            config: Backend configuration dictionary
            workspace_path: Path to workspace directory
            
        Returns:
            SecureBackend instance or None if disabled/invalid
        """
        # Check if backend is enabled
        if not config.get("enabled", False):
            logger.info("Custom backend not enabled, using deepagents default")
            return None
        
        # Convert to BackendConfig
        try:
            backend_config = BackendConfig(
                enabled=config.get("enabled", False),
                backend_type=config.get("backend_type", "file_encrypted"),
                enable_persistence=config.get("enable_persistence", True),
                enable_checkpoints=config.get("enable_checkpoints", True),
                encrypt_state=config.get("encrypt_state", True),
                allow_network_access=config.get("allow_network_access", False),
                storage_path=config.get("storage_path"),
                encryption_key=config.get("encryption_key"),
                max_checkpoints=config.get("max_checkpoints", 100),
                checkpoint_interval=config.get("checkpoint_interval", 60)
            )
        except Exception as e:
            logger.error(f"Failed to parse backend config: {e}")
            return None
        
        # Security validation
        if not backend_config.encrypt_state:
            logger.error("❌ SECURITY VIOLATION: State encryption must be enabled")
            raise ValueError("State encryption is required for security")
        
        if backend_config.allow_network_access:
            logger.error("❌ SECURITY VIOLATION: Network access not allowed")
            raise ValueError("Network access is not allowed for security reasons")
        
        # Create backend
        try:
            backend = SecureBackend(backend_config, workspace_path)
            
            # Validate backend security
            is_valid, errors = backend.validate_security()
            if not is_valid:
                logger.error(f"Backend security validation failed: {errors}")
                raise ValueError(f"Security validation failed: {errors}")
            
            logger.info(f"✅ Secure backend created: {backend_config.backend_type}")
            return backend
            
        except Exception as e:
            logger.error(f"Failed to create backend: {e}")
            raise
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate backend configuration before creating backend
        
        Args:
            config: Backend configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if not isinstance(config.get("enabled"), bool):
            errors.append("enabled must be a boolean")
        
        if config.get("enabled"):
            # Validate backend type
            backend_type = config.get("backend_type", "file_encrypted")
            valid_types = ["file_encrypted", "memory", "custom"]
            if backend_type not in valid_types:
                errors.append(f"backend_type must be one of {valid_types}")
            
            # Security checks
            if not config.get("encrypt_state", True):
                errors.append("encrypt_state must be True for security")
            
            if config.get("allow_network_access", False):
                errors.append("allow_network_access must be False for security")
            
            # Validate numeric values
            if config.get("max_checkpoints", 100) <= 0:
                errors.append("max_checkpoints must be positive")
            
            if config.get("checkpoint_interval", 60) <= 0:
                errors.append("checkpoint_interval must be positive")
        
        return len(errors) == 0, errors


def get_backend_config_example() -> Dict[str, Any]:
    """Get example backend configuration"""
    return {
        "enabled": True,
        "backend_type": "file_encrypted",
        "enable_persistence": True,
        "enable_checkpoints": True,
        "encrypt_state": True,
        "allow_network_access": False,
        "storage_path": None,  # Uses workspace/backend_state by default
        "encryption_key": None,  # Auto-derived from workspace path
        "max_checkpoints": 100,
        "checkpoint_interval": 60
    }


# ============================================================================
# DeepAgents BackendProtocol Implementation (Filesystem Backend)
# ============================================================================

@dataclass
class FileInfo:
    """File information for DeepAgents backend"""
    path: str
    is_dir: Optional[bool] = None
    size: Optional[int] = None
    modified_at: Optional[str] = None


@dataclass
class FileData:
    """File data for DeepAgents backend"""
    content: str
    encoding: str = "utf-8"
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


@dataclass
class GrepMatch:
    """Grep match result"""
    path: str
    line: int
    text: str


@dataclass
class LsResult:
    """Result for ls operation"""
    error: Optional[str] = None
    entries: Optional[List[FileInfo]] = None


@dataclass
class ReadResult:
    """Result for read operation"""
    error: Optional[str] = None
    file_data: Optional[FileData] = None


@dataclass
class WriteResult:
    """Result for write operation"""
    error: Optional[str] = None
    path: Optional[str] = None
    files_update: Optional[Dict[str, Any]] = None


@dataclass
class EditResult:
    """Result for edit operation"""
    error: Optional[str] = None
    path: Optional[str] = None
    files_update: Optional[Dict[str, Any]] = None
    occurrences: Optional[int] = None


@dataclass
class GrepResult:
    """Result for grep operation"""
    error: Optional[str] = None
    matches: Optional[List[GrepMatch]] = None


@dataclass
class GlobResult:
    """Result for glob operation"""
    error: Optional[str] = None
    matches: Optional[List[FileInfo]] = None


@dataclass
class FilesystemBackendConfig:
    """Configuration for filesystem backend"""
    base_path: str  # Base directory for file operations
    encrypt_files: bool = True  # Encrypt file contents
    encryption_key: Optional[str] = None  # Encryption key (derived if None)
    allow_write: bool = True  # Allow file write operations
    allow_delete: bool = False  # Allow file delete operations
    max_file_size: int = 10 * 1024 * 1024  # 10MB max file size
    allowed_extensions: Optional[List[str]] = None  # Allowed file extensions


class SecureFilesystemBackend:
    """Secure filesystem backend implementing DeepAgents BackendProtocol
    
    Provides encrypted file operations for DeepAgents with:
    - File encryption/decryption
    - Access control (read/write/delete permissions)
    - File size limits
    - Extension filtering
    """

    def __init__(self, config: FilesystemBackendConfig):
        self.config = config
        self.base_path = Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self._fernet: Optional[Fernet] = None
        if config.encrypt_files:
            self._init_encryption()
        
        logger.info(f"SecureFilesystemBackend initialized with base_path={self.base_path}, encryption={config.encrypt_files}")

    def _init_encryption(self):
        """Initialize encryption key"""
        if self.config.encryption_key:
            key_bytes = self.config.encryption_key.encode() if isinstance(self.config.encryption_key, str) else self.config.encryption_key
            if len(key_bytes) < 32:
                key_bytes = key_bytes.ljust(32, b'\0')
            else:
                key_bytes = key_bytes[:32]
            self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
        else:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'safe_claw_filesystem',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(str(self.base_path).encode()))
            self._fernet = Fernet(key)
        
        logger.info("Filesystem encryption initialized with Fernet")

    def _encrypt_content(self, content: str) -> str:
        """Encrypt file content"""
        if not self._fernet:
            return content
        encrypted = self._fernet.encrypt(content.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def _decrypt_content(self, encrypted_content: str) -> str:
        """Decrypt file content"""
        if not self._fernet:
            return encrypted_content
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_content.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - file may be corrupted")

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path relative to base path"""
        # Remove leading slash if present
        if file_path.startswith("/"):
            file_path = file_path[1:]
        
        # Prevent path traversal
        resolved = (self.base_path / file_path).resolve()
        base_resolved = self.base_path.resolve()
        
        # Normalize paths for comparison (handle macOS /private/var symlink)
        resolved_str = str(resolved)
        base_resolved_str = str(base_resolved)
        
        # On macOS, /var/folders might be symlinked to /private/var/folders
        # Compare both normalized forms
        if not (resolved_str.startswith(base_resolved_str) or 
                resolved_str.replace("/private/", "/").startswith(base_resolved_str.replace("/private/", "/")) or
                base_resolved_str.replace("/private/", "/").startswith(resolved_str.replace("/private/", "/"))):
            raise ValueError(f"Path traversal detected: {file_path}")
        
        return resolved

    def _check_extension(self, file_path: str) -> bool:
        """Check if file extension is allowed"""
        if not self.config.allowed_extensions:
            return True
        
        ext = Path(file_path).suffix.lower()
        return ext in self.config.allowed_extensions

    def _get_relative_path(self, absolute_path: Path) -> str:
        """Get relative path from base path, handling macOS symlinks"""
        item_str = str(absolute_path)
        base_str = str(self.base_path)
        
        # Remove base path
        rel_path = item_str.replace(base_str + "/", "").replace(base_str, "")
        
        # Handle macOS /private/var symlink
        rel_path = rel_path.replace("/private/", "")
        
        # Remove leading slash if present
        if rel_path.startswith("/"):
            rel_path = rel_path[1:]
        
        return rel_path

    def ls_info(self, path: str) -> list:
        """List directory entries (BackendProtocol interface)"""
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                return []
            
            if not resolved_path.is_dir():
                return []
            
            entries = []
            for item in sorted(resolved_path.iterdir()):
                try:
                    stat = item.stat()
                    rel_path = self._get_relative_path(item)
                    
                    file_info = {
                        "path": "/" + rel_path if not rel_path.startswith("/") else rel_path,
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if item.is_file() else None,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    entries.append(file_info)
                except Exception as e:
                    logger.warning(f"Failed to stat {item}: {e}")
            
            return entries
            
        except ValueError as e:
            logger.error(f"ls_info failed: {e}")
            return []
        except Exception as e:
            logger.error(f"ls_info failed: {e}")
            return []

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read file content (BackendProtocol interface - returns cat -n formatted string)"""
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not resolved_path.exists():
                return f"Error: File '{file_path}' not found"
            
            if not resolved_path.is_file():
                return f"Error: '{file_path}' is not a file"
            
            # Check file size
            file_size = resolved_path.stat().st_size
            if file_size > self.config.max_file_size:
                return f"Error: File too large (max {self.config.max_file_size} bytes)"
            
            # Read file content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Decrypt if enabled
            if self.config.encrypt_files:
                try:
                    content = self._decrypt_content(content)
                except Exception as e:
                    return f"Error: Failed to decrypt file - {str(e)}"
            
            # Apply offset (line-based) and limit
            lines = content.split('\n')
            if offset > 0:
                lines = lines[offset:]
            if limit > 0:
                lines = lines[:limit]
            
            # Format as cat -n style (1-indexed line numbers)
            start_line = offset + 1
            formatted_lines = []
            for i, line in enumerate(lines):
                line_num = start_line + i
                # Truncate long lines
                if len(line) > 2000:
                    line = line[:2000]
                formatted_lines.append(f"{line_num}\t{line}")
            
            return '\n'.join(formatted_lines)
            
        except ValueError as e:
            return str(e)
        except Exception as e:
            logger.error(f"read failed: {e}")
            return f"Error: {str(e)}"

    def write(self, file_path: str, content: str) -> WriteResult:
        """Write file content (create-only)"""
        try:
            if not self.config.allow_write:
                return WriteResult(error="Error: Write operations not allowed")
            
            resolved_path = self._resolve_path(file_path)
            
            # Check if file already exists
            if resolved_path.exists():
                return WriteResult(error=f"Error: File '{file_path}' already exists")
            
            # Check extension
            if not self._check_extension(file_path):
                return WriteResult(error=f"Error: File extension not allowed")
            
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > self.config.max_file_size:
                return WriteResult(error=f"Error: Content too large (max {self.config.max_file_size} bytes)")
            
            # Encrypt if enabled
            if self.config.encrypt_files:
                content = self._encrypt_content(content)
            
            # Create parent directories
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Prepare files_update for state backend (normalize path)
            rel_path = self._get_relative_path(resolved_path)
            files_update = {
                rel_path: {
                    "size": content_size,
                    "modified_at": datetime.now().isoformat()
                }
            }
            
            return WriteResult(path=file_path, files_update=files_update)
            
        except ValueError as e:
            return WriteResult(error=str(e))
        except Exception as e:
            logger.error(f"write failed: {e}")
            return WriteResult(error=f"Error: {str(e)}")

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        """Edit file content"""
        try:
            if not self.config.allow_write:
                return EditResult(error="Error: Write operations not allowed")
            
            resolved_path = self._resolve_path(file_path)
            
            if not resolved_path.exists():
                return EditResult(error=f"Error: File '{file_path}' not found")
            
            if not resolved_path.is_file():
                return EditResult(error=f"Error: '{file_path}' is not a file")
            
            # Read file content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Decrypt if enabled
            if self.config.encrypt_files:
                try:
                    content = self._decrypt_content(content)
                except Exception as e:
                    return EditResult(error=f"Error: Failed to decrypt file - {str(e)}")
            
            # Count occurrences before replacement
            if replace_all:
                occurrences = content.count(old_string)
            else:
                # Find first occurrence
                if old_string in content:
                    occurrences = 1
                else:
                    return EditResult(error=f"Error: '{old_string}' not found in file")
            
            if occurrences == 0:
                return EditResult(error=f"Error: '{old_string}' not found in file")
            
            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
            
            # Encrypt if enabled
            if self.config.encrypt_files:
                new_content = self._encrypt_content(new_content)
            
            # Write file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Prepare files_update (normalize path)
            rel_path = self._get_relative_path(resolved_path)
            files_update = {
                rel_path: {
                    "size": len(new_content.encode('utf-8')),
                    "modified_at": datetime.now().isoformat()
                }
            }
            
            return EditResult(path=file_path, files_update=files_update, occurrences=occurrences)
            
        except ValueError as e:
            return EditResult(error=str(e))
        except Exception as e:
            logger.error(f"edit failed: {e}")
            return EditResult(error=f"Error: {str(e)}")

    def grep_raw(self, pattern: str, path: Optional[str] = None, glob: Optional[str] = None) -> list:
        """Search for pattern in files (BackendProtocol interface)"""
        try:
            matches = []
            search_path = self._resolve_path(path if path else "/")
            
            if not search_path.exists():
                return f"Error: Path '{path}' not found"
            
            # Collect files to search
            files_to_search = []
            if search_path.is_file():
                files_to_search.append(search_path)
            else:
                if glob:
                    # Use glob pattern
                    for item in search_path.glob(glob):
                        if item.is_file():
                            files_to_search.append(item)
                else:
                    # Search all files recursively
                    for item in search_path.rglob("*"):
                        if item.is_file():
                            files_to_search.append(item)
            
            # Search each file
            for file_path in files_to_search:
                try:
                    # Read and decrypt
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if self.config.encrypt_files:
                        try:
                            content = self._decrypt_content(content)
                        except:
                            continue  # Skip files that can't be decrypted
                    
                    # Search for pattern (literal string, not regex per protocol)
                    rel = self._get_relative_path(file_path)
                    abs_path = "/" + rel if not rel.startswith("/") else rel
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if pattern in line:
                            matches.append({
                                "path": abs_path,
                                "line": line_num,
                                "text": line.strip()
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to search {file_path}: {e}")
            
            return matches
            
        except ValueError as e:
            return str(e)
        except Exception as e:
            logger.error(f"grep_raw failed: {e}")
            return f"Error: {str(e)}"

    def glob_info(self, pattern: str, path: str = "/") -> list:
        """Match files using glob pattern (BackendProtocol interface)"""
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                return []
            
            matches = []
            for item in resolved_path.glob(pattern):
                try:
                    stat = item.stat()
                    rel_path = self._get_relative_path(item)
                    abs_path = "/" + rel_path if not rel_path.startswith("/") else rel_path
                    file_info = {
                        "path": abs_path,
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if item.is_file() else None,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    matches.append(file_info)
                except Exception as e:
                    logger.warning(f"Failed to stat {item}: {e}")
            
            return matches
            
        except ValueError as e:
            logger.error(f"glob_info failed: {e}")
            return []
        except Exception as e:
            logger.error(f"glob_info failed: {e}")
            return []


class FilesystemBackendFactory:
    """Factory for creating filesystem backends"""
    
    @staticmethod
    def create_backend(config: Dict[str, Any], workspace_path: Path) -> Optional[SecureFilesystemBackend]:
        """Create a secure filesystem backend from configuration"""
        try:
            fs_config = FilesystemBackendConfig(
                base_path=config.get("base_path", str(workspace_path / "filesystem")),
                encrypt_files=config.get("encrypt_files", True),
                encryption_key=config.get("encryption_key"),
                allow_write=config.get("allow_write", True),
                allow_delete=config.get("allow_delete", False),
                max_file_size=config.get("max_file_size", 10 * 1024 * 1024),
                allowed_extensions=config.get("allowed_extensions")
            )
            
            backend = SecureFilesystemBackend(fs_config)
            logger.info(f"✅ SecureFilesystemBackend created: {fs_config.base_path}")
            return backend
            
        except Exception as e:
            logger.error(f"Failed to create filesystem backend: {e}")
            return None
