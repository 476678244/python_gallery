#!/usr/bin/env python3
"""Apply the "IntelliJ Light (Maple)" Cursor look-and-feel.

Installs the bundled color-theme extension, merges the managed editor settings
into the user's settings.json, and (optionally) installs the JetBrains icon
theme. Idempotent: re-running only overwrites the keys this skill manages.

Usage:
    python scripts/apply_theme.py            # apply everything
    python scripts/apply_theme.py --dry-run  # show what would change
    python scripts/apply_theme.py --no-icon  # skip JetBrains icon-theme install
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ICON_EXTENSION_ID = "chadalen.vscode-jetbrains-icon-theme"
EXTENSION_FOLDER = "intellij-light-maple-1.0.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets"


def default_settings_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", home)) / "Cursor" / "User" / "settings.json"
    return home / ".config" / "Cursor" / "User" / "settings.json"


def default_extensions_dir() -> Path:
    return Path.home() / ".cursor" / "extensions"


def load_jsonc(path: Path) -> dict:
    """Parse a settings.json that may contain // and /* */ comments + trailing commas."""
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    no_line = re.sub(r"(^|[^:])//[^\n]*", lambda m: m.group(1), no_block)
    no_trailing = re.sub(r",(\s*[}\]])", r"\1", no_line)
    try:
        return json.loads(no_trailing)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"[apply_theme] Cannot parse existing settings.json\n"
            f"  Path: {path}\n"
            f"  Error: {exc}\n"
            f"  Fix: resolve the JSON syntax error manually, then re-run."
        ) from exc


def install_extension(extensions_dir: Path, dry_run: bool) -> Path:
    src = ASSETS / "extension"
    if not (src / "package.json").exists():
        raise FileNotFoundError(
            f"[apply_theme] Bundled extension assets missing\n"
            f"  Expected: {src / 'package.json'}\n"
            f"  Fix: ensure the skill 'assets/extension' directory is intact."
        )
    dest = extensions_dir / EXTENSION_FOLDER
    print(f"[extension] {src}  ->  {dest}")
    if dry_run:
        return dest
    extensions_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    register_extension(extensions_dir, dest)
    return dest


def register_extension(extensions_dir: Path, dest: Path) -> None:
    """Add the local extension to extensions.json so Cursor discovers it."""
    index = extensions_dir / "extensions.json"
    entry = {
        "identifier": {"id": "local.intellij-light-maple"},
        "version": "1.0.0",
        "location": {
            "$mid": 1,
            "fsPath": str(dest),
            "external": dest.as_uri(),
            "path": str(dest),
            "scheme": "file",
        },
        "relativeLocation": EXTENSION_FOLDER,
    }
    items = []
    if index.exists():
        try:
            items = json.loads(index.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    items = [it for it in items if it.get("relativeLocation") != EXTENSION_FOLDER]
    items.append(entry)
    index.write_text(json.dumps(items), encoding="utf-8")
    print(f"[extension] registered in {index}")


def merge_settings(settings_path: Path, dry_run: bool) -> None:
    fragment = json.loads((ASSETS / "settings.fragment.json").read_text(encoding="utf-8"))
    if settings_path.exists():
        current = load_jsonc(settings_path)
    else:
        current = {}
        print(f"[settings] creating new file: {settings_path}")

    for key, value in fragment.items():
        if key == "files.exclude" and isinstance(current.get(key), dict):
            current[key] = {**current[key], **value}
        else:
            current[key] = value

    rendered = json.dumps(current, indent=4, ensure_ascii=False) + "\n"
    print(f"[settings] {settings_path}")
    if dry_run:
        print(rendered)
        return
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(rendered, encoding="utf-8")


def install_icon_theme(dry_run: bool) -> None:
    cursor = shutil.which("cursor")
    if not cursor:
        print(
            "[icon] 'cursor' CLI not found on PATH; skipping auto-install.\n"
            f"       Install manually:  cursor --install-extension {ICON_EXTENSION_ID}"
        )
        return
    print(f"[icon] {cursor} --install-extension {ICON_EXTENSION_ID}")
    if dry_run:
        return
    result = subprocess.run(
        [cursor, "--install-extension", ICON_EXTENSION_ID],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    if result.returncode != 0:
        print(
            f"[icon] install failed (exit {result.returncode}).\n"
            f"       {result.stderr.strip()}\n"
            f"       Retry manually:  cursor --install-extension {ICON_EXTENSION_ID}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply IntelliJ Light (Maple) Cursor theme.")
    parser.add_argument("--settings", type=Path, default=default_settings_path())
    parser.add_argument("--extensions-dir", type=Path, default=default_extensions_dir())
    parser.add_argument("--no-icon", action="store_true", help="skip JetBrains icon-theme install")
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing")
    args = parser.parse_args()

    print("=== IntelliJ Light (Maple) :: apply ===")
    install_extension(args.extensions_dir, args.dry_run)
    merge_settings(args.settings, args.dry_run)
    if not args.no_icon:
        install_icon_theme(args.dry_run)

    print("\nDone. In Cursor run 'Developer: Reload Window' (Cmd/Ctrl+Shift+P) to apply.")
    if args.dry_run:
        print("(dry-run: nothing was written)")


if __name__ == "__main__":
    main()
