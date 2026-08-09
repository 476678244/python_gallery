"""SecureFilesystemBackend download_files / upload_files (DeepAgents protocol)."""

from pathlib import Path

from safe_claw.core.deepagents.backend import (
    FilesystemBackendConfig,
    SecureFilesystemBackend,
)


def test_download_files_success_and_missing(tmp_path: Path):
    cfg = FilesystemBackendConfig(
        base_path=str(tmp_path / "fs"),
        encrypt_files=False,
        allow_write=True,
        allow_edit=True,
    )
    be = SecureFilesystemBackend(cfg)
    (be.base_path / "a.txt").write_text("hello ppt", encoding="utf-8")

    out = be.download_files(["a.txt", "missing.txt", "/a.txt"])
    by_path = {r.path: r for r in out}
    assert by_path["a.txt"].error is None
    assert by_path["a.txt"].content == b"hello ppt"
    assert by_path["missing.txt"].error == "file_not_found"
    # leading slash still resolves under base
    assert by_path["/a.txt"].error is None
    assert by_path["/a.txt"].content == b"hello ppt"


def test_download_files_rejects_path_traversal(tmp_path: Path):
    cfg = FilesystemBackendConfig(
        base_path=str(tmp_path / "fs"),
        encrypt_files=False,
        allow_write=True,
    )
    be = SecureFilesystemBackend(cfg)
    out = be.download_files(["../outside.txt"])
    assert len(out) == 1
    assert out[0].error == "invalid_path"
    assert out[0].content is None


def test_upload_files_create_only(tmp_path: Path):
    cfg = FilesystemBackendConfig(
        base_path=str(tmp_path / "fs"),
        encrypt_files=False,
        allow_write=True,
        allow_edit=False,
    )
    be = SecureFilesystemBackend(cfg)
    r1 = be.upload_files([("new.bin", b"abc")])
    assert r1[0].error is None
    assert (be.base_path / "new.bin").read_bytes() == b"abc"

    r2 = be.upload_files([("new.bin", b"xyz")])
    assert r2[0].error == "permission_denied"
    assert (be.base_path / "new.bin").read_bytes() == b"abc"
