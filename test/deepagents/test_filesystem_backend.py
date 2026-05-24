"""Test SecureFilesystemBackend Implementation

Tests the DeepAgents BackendProtocol implementation with encryption.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import tempfile
from safe_claw.core.deepagents.backend import (
    SecureFilesystemBackend,
    FilesystemBackendFactory,
    FilesystemBackendConfig,
    FileInfo,
    FileData,
    GrepMatch,
    LsResult,
    ReadResult,
    WriteResult,
    EditResult,
    GrepResult,
    GlobResult
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_filesystem_backend_creation():
    """Test filesystem backend creation"""
    print("\n=== Testing Filesystem Backend Creation ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=True,
            allow_write=True,
            allow_delete=False
        )
        
        backend = SecureFilesystemBackend(config)
        assert backend.base_path.exists()
        print("✅ Filesystem backend created successfully")
        print(f"🔧 Base path: {backend.base_path}")
        print(f"🔧 Encryption enabled: {config.encrypt_files}")
    
    print("\n✅ Filesystem backend creation test passed\n")


def test_ls_operation():
    """Test ls operation"""
    print("\n=== Testing LS Operation ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=False,  # Disable for this test
            allow_write=True
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Create some test files
        (backend.base_path / "test1.txt").write_text("content1")
        (backend.base_path / "test2.txt").write_text("content2")
        (backend.base_path / "subdir").mkdir()
        
        # Test ls on root
        result = backend.ls("/")
        assert result.error is None
        assert result.entries is not None
        assert len(result.entries) == 3  # 2 files + 1 directory
        print(f"✅ LS returned {len(result.entries)} entries")
        
        # Test ls on non-existent path
        result = backend.ls("/nonexistent")
        assert result.error is not None
        print("✅ LS correctly returns error for non-existent path")
    
    print("\n✅ LS operation test passed\n")


def test_write_and_read_operations():
    """Test write and read operations with encryption"""
    print("\n=== Testing Write and Read Operations ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=True,  # Enable encryption
            allow_write=True
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Test write
        test_content = "Hello, World! This is a test file."
        write_result = backend.write("/test.txt", test_content)
        if write_result.error:
            print(f"❌ Write failed with error: {write_result.error}")
        assert write_result.error is None, f"Write failed: {write_result.error}"
        assert write_result.path == "/test.txt"
        print("✅ Write operation successful")
        
        # Test write duplicate (should fail)
        write_result = backend.write("/test.txt", "duplicate")
        assert write_result.error is not None
        print("✅ Write duplicate correctly rejected")
        
        # Test read
        read_result = backend.read("/test.txt")
        assert read_result.error is None
        assert read_result.file_data is not None
        assert read_result.file_data.content == test_content
        print("✅ Read operation successful with decryption")
        
        # Verify file is encrypted on disk
        file_content = (backend.base_path / "test.txt").read_text()
        assert test_content not in file_content
        print("✅ File is encrypted on disk")
    
    print("\n✅ Write and read operations test passed\n")


def test_edit_operation():
    """Test edit operation"""
    print("\n=== Testing Edit Operation ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=True,
            allow_write=True
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Create initial file
        initial_content = "Hello, World! Hello again!"
        backend.write("/test.txt", initial_content)
        
        # Test edit (single occurrence)
        edit_result = backend.edit("/test.txt", "Hello", "Hi")
        assert edit_result.error is None
        assert edit_result.occurrences == 1
        print("✅ Edit single occurrence successful")
        
        # Verify edit
        read_result = backend.read("/test.txt")
        assert read_result.file_data.content == "Hi, World! Hello again!"
        print("✅ Edit content verified")
        
        # Test edit (replace all)
        edit_result = backend.edit("/test.txt", "Hello", "Hi", replace_all=True)
        assert edit_result.error is None
        assert edit_result.occurrences == 1
        print("✅ Edit replace all successful")
        
        # Verify replace all
        read_result = backend.read("/test.txt")
        assert read_result.file_data.content == "Hi, World! Hi again!"
        print("✅ Replace all content verified")
    
    print("\n✅ Edit operation test passed\n")


def test_grep_operation():
    """Test grep operation"""
    print("\n=== Testing Grep Operation ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=False,  # Disable for easier testing
            allow_write=True
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Create test files
        (backend.base_path / "file1.txt").write_text("line1\nline2\nHello World\nline3")
        (backend.base_path / "file2.txt").write_text("Hello\nWorld\nHello World")
        
        # Test grep
        grep_result = backend.grep("Hello")
        assert grep_result.error is None
        assert grep_result.matches is not None
        assert len(grep_result.matches) == 3  # 2 in file1, 1 in file2
        print(f"✅ Grep found {len(grep_result.matches)} matches")
        
        # Test grep with path
        grep_result = backend.grep("World", path="/file1.txt")
        assert grep_result.error is None
        assert len(grep_result.matches) == 1
        print("✅ Grep with path successful")
    
    print("\n✅ Grep operation test passed\n")


def test_glob_operation():
    """Test glob operation"""
    print("\n=== Testing Glob Operation ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=False,
            allow_write=True
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Create test files
        (backend.base_path / "test1.txt").write_text("content1")
        (backend.base_path / "test2.txt").write_text("content2")
        (backend.base_path / "other.py").write_text("code")
        
        # Test glob
        glob_result = backend.glob("*.txt")
        assert glob_result.error is None
        assert glob_result.matches is not None
        assert len(glob_result.matches) == 2
        print(f"✅ Glob found {len(glob_result.matches)} .txt files")
        
        # Test glob with pattern
        glob_result = backend.glob("test*.txt")
        assert len(glob_result.matches) == 2
        print("✅ Glob with pattern successful")
    
    print("\n✅ Glob operation test passed\n")


def test_security_features():
    """Test security features"""
    print("\n=== Testing Security Features ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem"),
            encrypt_files=True,
            allow_write=True,
            allowed_extensions=[".txt"]  # Only allow .txt files
        )
        
        backend = SecureFilesystemBackend(config)
        
        # Test extension filtering
        write_result = backend.write("/test.py", "code")
        assert write_result.error is not None
        assert "extension not allowed" in write_result.error.lower()
        print("✅ Extension filtering works")
        
        # Test allowed extension
        write_result = backend.write("/test.txt", "content")
        assert write_result.error is None
        print("✅ Allowed extension accepted")
        
        # Test path traversal prevention
        write_result = backend.write("../../../etc/passwd", "malicious")
        assert write_result.error is not None
        assert "traversal" in write_result.error.lower()
        print("✅ Path traversal prevention works")
        
        # Test write disabled
        config_no_write = FilesystemBackendConfig(
            base_path=str(Path(tmpdir) / "filesystem2"),
            encrypt_files=True,
            allow_write=False
        )
        backend_no_write = SecureFilesystemBackend(config_no_write)
        
        write_result = backend_no_write.write("/test.txt", "content")
        assert write_result.error is not None
        assert "not allowed" in write_result.error.lower()
        print("✅ Write permission control works")
    
    print("\n✅ Security features test passed\n")


def run_all_tests():
    """Run all filesystem backend tests"""
    print("\n" + "="*60)
    print("SAFECLAW SECURE FILESYSTEM BACKEND TEST SUITE")
    print("="*60)
    
    try:
        test_filesystem_backend_creation()
        test_ls_operation()
        test_write_and_read_operations()
        test_edit_operation()
        test_grep_operation()
        test_glob_operation()
        test_security_features()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
