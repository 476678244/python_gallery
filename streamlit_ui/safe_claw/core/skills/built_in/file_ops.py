"""File operations skills for SafeClaw"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import logging

from core.skills.base_skill import FileSkill

logger = logging.getLogger(__name__)

class ReadFileSkill(FileSkill):
    """Skill for reading file contents"""
    
    def __init__(self):
        super().__init__("read_file", "Read the contents of a file")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (optional)",
                    "default": None
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, encoding: str = "utf-8", max_lines: int = None) -> Dict[str, Any]:
        """Execute file reading"""
        try:
            # Validate file path
            is_safe, error_msg = self.validate_file_path(file_path)
            if not is_safe:
                return {"success": False, "error": error_msg}
            
            # Ensure file is in safe directory
            safe_path = self.ensure_safe_directory(os.getcwd(), file_path)
            
            if not os.path.exists(safe_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not os.path.isfile(safe_path):
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            
            # Read file
            with open(safe_path, 'r', encoding=encoding) as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip('\n'))
                    content = '\n'.join(lines)
                    truncated = i >= max_lines - 1
                else:
                    content = f.read()
                    truncated = False
            
            # Get file info
            file_stat = os.stat(safe_path)
            
            self.increment_usage()
            
            return {
                "success": True,
                "content": content,
                "file_info": {
                    "path": file_path,
                    "size": file_stat.st_size,
                    "modified": file_stat.st_mtime,
                    "encoding": encoding
                },
                "truncated": truncated
            }
            
        except UnicodeDecodeError:
            return {"success": False, "error": f"Failed to decode file with encoding: {encoding}"}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {"success": False, "error": str(e)}

class WriteFileSkill(FileSkill):
    """Skill for writing file contents"""
    
    def __init__(self):
        super().__init__("write_file", "Write content to a file")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True
                }
            },
            "required": ["file_path", "content"]
        }
    
    def execute(self, file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> Dict[str, Any]:
        """Execute file writing"""
        try:
            # Validate file path
            is_safe, error_msg = self.validate_file_path(file_path)
            if not is_safe:
                return {"success": False, "error": error_msg}
            
            # Ensure file is in safe directory
            safe_path = self.ensure_safe_directory(os.getcwd(), file_path)
            
            # Create parent directories if needed
            parent_dir = os.path.dirname(safe_path)
            if create_dirs and parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write file
            with open(safe_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            self.increment_usage()
            
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content.encode(encoding)),
                "encoding": encoding
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {"success": False, "error": str(e)}

class ListFilesSkill(FileSkill):
    """Skill for listing files in a directory"""
    
    def __init__(self):
        super().__init__("list_files", "List files and directories in a path")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to list"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List files recursively",
                    "default": False
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files and directories",
                    "default": False
                },
                "pattern": {
                    "type": "string",
                    "description": "File pattern to match (e.g., '*.py')",
                    "default": "*"
                }
            },
            "required": ["directory_path"]
        }
    
    def execute(self, directory_path: str, recursive: bool = False, 
                show_hidden: bool = False, pattern: str = "*") -> Dict[str, Any]:
        """Execute directory listing"""
        try:
            # Validate directory path
            is_safe, error_msg = self.validate_file_path(directory_path)
            if not is_safe:
                return {"success": False, "error": error_msg}
            
            # Ensure directory is in safe directory
            safe_path = self.ensure_safe_directory(os.getcwd(), directory_path)
            
            if not os.path.exists(safe_path):
                return {"success": False, "error": f"Directory not found: {directory_path}"}
            
            if not os.path.isdir(safe_path):
                return {"success": False, "error": f"Path is not a directory: {directory_path}"}
            
            # List files
            files = []
            
            if recursive:
                for root, dirs, filenames in os.walk(safe_path):
                    if not show_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for filename in filenames:
                        if show_hidden or not filename.startswith('.'):
                            if self._matches_pattern(filename, pattern):
                                full_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(full_path, safe_path)
                                file_info = self._get_file_info(full_path, rel_path)
                                files.append(file_info)
            else:
                for item in os.listdir(safe_path):
                    if show_hidden or not item.startswith('.'):
                        if self._matches_pattern(item, pattern):
                            full_path = os.path.join(safe_path, item)
                            file_info = self._get_file_info(full_path, item)
                            files.append(file_info)
            
            self.increment_usage()
            
            return {
                "success": True,
                "directory": directory_path,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def _get_file_info(self, full_path: str, rel_path: str) -> Dict[str, Any]:
        """Get file information"""
        stat = os.stat(full_path)
        return {
            "name": rel_path,
            "path": full_path,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "size": stat.st_size if os.path.isfile(full_path) else None,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:]
        }

class DeleteFileSkill(FileSkill):
    """Skill for deleting files or directories"""
    
    def __init__(self):
        super().__init__("delete_file", "Delete a file or directory")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file or directory to delete"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Delete directories recursively",
                    "default": False
                }
            },
            "required": ["path"]
        }
    
    def execute(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """Execute file/directory deletion"""
        try:
            # Validate path
            is_safe, error_msg = self.validate_file_path(path)
            if not is_safe:
                return {"success": False, "error": error_msg}
            
            # Ensure path is in safe directory
            safe_path = self.ensure_safe_directory(os.getcwd(), path)
            
            if not os.path.exists(safe_path):
                return {"success": False, "error": f"Path not found: {path}"}
            
            # Delete file or directory
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                deleted_type = "file"
            elif os.path.isdir(safe_path):
                if recursive:
                    shutil.rmtree(safe_path)
                else:
                    try:
                        os.rmdir(safe_path)
                    except OSError as e:
                        return {"success": False, "error": f"Directory not empty: {e}"}
                deleted_type = "directory"
            else:
                return {"success": False, "error": f"Unknown path type: {path}"}
            
            self.increment_usage()
            
            return {
                "success": True,
                "path": path,
                "type": deleted_type,
                "recursive": recursive
            }
            
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return {"success": False, "error": str(e)}

class CreateDirectorySkill(FileSkill):
    """Skill for creating directories"""
    
    def __init__(self):
        super().__init__("create_directory", "Create a directory")
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to create"
                },
                "parents": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True
                }
            },
            "required": ["directory_path"]
        }
    
    def execute(self, directory_path: str, parents: bool = True) -> Dict[str, Any]:
        """Execute directory creation"""
        try:
            # Validate directory path
            is_safe, error_msg = self.validate_file_path(directory_path)
            if not is_safe:
                return {"success": False, "error": error_msg}
            
            # Ensure directory is in safe directory
            safe_path = self.ensure_safe_directory(os.getcwd(), directory_path)
            
            if os.path.exists(safe_path):
                return {"success": False, "error": f"Path already exists: {directory_path}"}
            
            # Create directory
            os.makedirs(safe_path, exist_ok=parents)
            
            self.increment_usage()
            
            return {
                "success": True,
                "directory_path": directory_path,
                "created": True
            }
            
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return {"success": False, "error": str(e)}
