"""Safe mode FS gate: allow_edit=False blocks edit."""

from pathlib import Path

from safe_claw.core.deepagents.backend import (
    FilesystemBackendConfig,
    SecureFilesystemBackend,
)


def test_edit_blocked_when_allow_edit_false(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    backend = SecureFilesystemBackend(
        FilesystemBackendConfig(
            base_path=str(tmp_path),
            encrypt_files=False,
            allow_write=True,
            allow_edit=False,
            allow_delete=False,
        )
    )
    result = backend.edit("a.txt", "hello", "world")
    assert result.error
    assert "allow_edit" in result.error or "Edit" in result.error
    assert f.read_text() == "hello"


def test_create_write_ok_when_edit_false(tmp_path: Path):
    backend = SecureFilesystemBackend(
        FilesystemBackendConfig(
            base_path=str(tmp_path),
            encrypt_files=False,
            allow_write=True,
            allow_edit=False,
            allow_delete=False,
        )
    )
    result = backend.write("new.txt", "x")
    assert not result.error
    assert (tmp_path / "new.txt").read_text() == "x"
    # overwrite via write already fails (create-only)
    result2 = backend.write("new.txt", "y")
    assert result2.error
    assert (tmp_path / "new.txt").read_text() == "x"
