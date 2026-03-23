"""File utility functions for SafeClaw"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FileOperations:
    """Safe file operations utility class"""
    
    @staticmethod
    def ensure_safe_path(base_path: str, file_path: str) -> str:
        """Ensure file path is within safe directory"""
        base = Path(base_path).resolve()
        target = Path(file_path)
        
        # If relative path, make it relative to base
        if not target.is_absolute():
            target = (base / target).resolve()
        
        # Check if target is within base
        try:
            target.relative_to(base)
            return str(target)
        except ValueError:
            raise ValueError(f"Path {file_path} is outside safe directory {base_path}")
    
    @staticmethod
    def is_safe_file_path(file_path: str, safe_directories: List[str] = None) -> bool:
        """Check if file path is safe"""
        if safe_directories is None:
            safe_directories = [os.getcwd()]
        
        file_path = os.path.abspath(file_path)
        
        for safe_dir in safe_directories:
            safe_dir = os.path.abspath(safe_dir)
            if file_path.startswith(safe_dir + os.sep) or file_path == safe_dir:
                return True
        
        return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            path = Path(file_path)
            stat = path.stat()
            
            # Get file type
            mime_type, encoding = mimetypes.guess_type(str(path))
            
            # Calculate file hash
            file_hash = None
            if path.is_file() and stat.st_size < 10 * 1024 * 1024:  # Only hash files < 10MB
                file_hash = FileOperations.calculate_file_hash(str(path))
            
            return {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "size_human": FileOperations.format_file_size(stat.st_size),
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "is_symlink": path.is_symlink(),
                "mime_type": mime_type,
                "encoding": encoding,
                "hash": file_hash,
                "permissions": oct(stat.st_mode)[-3:],
                "extension": path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
        """Calculate file hash"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def list_directory(directory: str, recursive: bool = False, 
                      show_hidden: bool = False, pattern: str = "*") -> List[Dict[str, Any]]:
        """List directory contents with detailed information"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return [{"error": f"Directory not found: {directory}"}]
            
            files = []
            
            if recursive:
                pattern_path = f"**/{pattern}"
                items = path.glob(pattern_path)
            else:
                items = path.glob(pattern)
            
            for item in items:
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                file_info = FileOperations.get_file_info(str(item))
                files.append(file_info)
            
            # Sort by name (directories first, then files)
            files.sort(key=lambda x: (not x.get("is_directory", False), x.get("name", "")))
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return [{"error": str(e)}]
    
    @staticmethod
    def create_directory(directory: str, parents: bool = True) -> Dict[str, Any]:
        """Create directory"""
        try:
            path = Path(directory)
            path.mkdir(parents=parents, exist_ok=True)
            
            return {
                "success": True,
                "directory": str(path),
                "created": True
            }
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_path(path: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete file or directory"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return {"success": False, "error": f"Path not found: {path}"}
            
            if path_obj.is_file():
                path_obj.unlink()
                deleted_type = "file"
            elif path_obj.is_dir():
                if recursive:
                    shutil.rmtree(path_obj)
                else:
                    try:
                        path_obj.rmdir()
                    except OSError as e:
                        return {"success": False, "error": f"Directory not empty: {e}"}
                deleted_type = "directory"
            else:
                return {"success": False, "error": f"Unknown path type: {path}"}
            
            return {
                "success": True,
                "path": path,
                "type": deleted_type,
                "recursive": recursive
            }
            
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def copy_file(source: str, destination: str) -> Dict[str, Any]:
        """Copy file"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {"success": False, "error": f"Source not found: {source}"}
            
            if not source_path.is_file():
                return {"success": False, "error": f"Source is not a file: {source}"}
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "size": source_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def move_file(source: str, destination: str) -> Dict[str, Any]:
        """Move file"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {"success": False, "error": f"Source not found: {source}"}
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(dest_path))
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path)
            }
            
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def read_file_safe(file_path: str, max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        """Safely read file with size limit"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            
            file_size = path.stat().st_size
            if file_size > max_size:
                return {"success": False, "error": f"File too large: {file_size} bytes (max: {max_size})"}
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            encoding_used = None
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {"success": False, "error": "Could not decode file with any supported encoding"}
            
            return {
                "success": True,
                "content": content,
                "encoding": encoding_used,
                "size": file_size
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def write_file_safe(file_path: str, content: str, encoding: str = 'utf-8', 
                       backup: bool = True) -> Dict[str, Any]:
        """Safely write file with optional backup"""
        try:
            path = Path(file_path)
            
            # Create backup if file exists
            backup_path = None
            if backup and path.exists():
                backup_path = path.with_suffix(f"{path.suffix}.backup")
                shutil.copy2(path, backup_path)
            
            # Create parent directory
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            result = {
                "success": True,
                "file_path": str(path),
                "bytes_written": len(content.encode(encoding)),
                "encoding": encoding
            }
            
            if backup_path:
                result["backup_path"] = str(backup_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def find_files(directory: str, pattern: str = "*", max_results: int = 1000) -> List[str]:
        """Find files matching pattern"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return []
            
            files = []
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))
                    if len(files) >= max_results:
                        break
            
            return files
            
        except Exception as e:
            logger.error(f"Error finding files in {directory}: {e}")
            return []
    
    @staticmethod
    def get_directory_size(directory: str) -> Dict[str, Any]:
        """Get directory size information"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return {"error": f"Directory not found: {directory}"}
            
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    dir_count += 1
            
            return {
                "total_size": total_size,
                "total_size_human": FileOperations.format_file_size(total_size),
                "file_count": file_count,
                "directory_count": dir_count,
                "path": str(path)
            }
            
        except Exception as e:
            logger.error(f"Error getting directory size for {directory}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """Check if file is likely a text file"""
        try:
            path = Path(file_path)
            
            # Check extension
            text_extensions = {
                '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
                '.md', '.rst', '.log', '.csv', '.ini', '.cfg', '.conf', '.sh', '.bat'
            }
            
            if path.suffix.lower() in text_extensions:
                return True
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type and mime_type.startswith('text/'):
                return True
            
            # Try to read a small portion
            if path.stat().st_size > 0:
                with open(path, 'rb') as f:
                    sample = f.read(1024)
                    try:
                        sample.decode('utf-8')
                        return True
                    except UnicodeDecodeError:
                        pass
            
            return False
            
        except Exception:
            return False
