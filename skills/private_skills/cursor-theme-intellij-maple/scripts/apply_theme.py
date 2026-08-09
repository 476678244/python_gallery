#!/usr/bin/env python3
"""Apply the "IntelliJ Light (Maple)" look-and-feel to Cursor and/or Obsidian.

One skill, two ends:
  * Cursor   — installs the bundled color-theme extension, merges managed editor
               settings, and (optionally) installs the JetBrains icon theme.
  * Obsidian — installs the bundled CSS theme into a vault and merges the managed
               appearance settings (theme, accent, fonts).

All operations are idempotent: re-running only overwrites the keys/files this
skill manages.

Usage:
    python scripts/apply_theme.py                       # Cursor only (safe default)
    python scripts/apply_theme.py --vault /path/to/vault   # Cursor + that vault
    python scripts/apply_theme.py --no-cursor --vault X    # Obsidian only
    python scripts/apply_theme.py --list-vaults            # discover Obsidian vaults
    python scripts/apply_theme.py --dry-run --vault X      # preview, write nothing
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
CURSOR_EXTENSION_FOLDER = "intellij-light-maple-1.0.0"
OBSIDIAN_THEME_NAME = "IntelliJ Light (Maple)"
SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets"


# --------------------------------------------------------------------------- #
# Path resolution
# --------------------------------------------------------------------------- #
def cursor_settings_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", home)) / "Cursor" / "User" / "settings.json"
    return home / ".config" / "Cursor" / "User" / "settings.json"


def cursor_extensions_dir() -> Path:
    return Path.home() / ".cursor" / "extensions"


def obsidian_config_file() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", home)) / "obsidian" / "obsidian.json"
    return home / ".config" / "obsidian" / "obsidian.json"


def discover_vaults() -> list[Path]:
    cfg = obsidian_config_file()
    if not cfg.exists():
        return []
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [Path(v["path"]) for v in data.get("vaults", {}).values() if "path" in v]


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def load_jsonc(path: Path) -> dict:
    """Parse JSON that may contain // and /* */ comments + trailing commas."""
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
            f"[apply_theme] Cannot parse JSON\n"
            f"  Path: {path}\n"
            f"  Error: {exc}\n"
            f"  Fix: resolve the JSON syntax error manually, then re-run."
        ) from exc


def merge_json_settings(path: Path, fragment: dict, indent: int, dry_run: bool) -> None:
    current = load_jsonc(path) if path.exists() else {}
    if not path.exists():
        print(f"[settings] creating new file: {path}")
    for key, value in fragment.items():
        if key == "files.exclude" and isinstance(current.get(key), dict):
            current[key] = {**current[key], **value}
        else:
            current[key] = value
    rendered = json.dumps(current, indent=indent, ensure_ascii=False) + "\n"
    print(f"[settings] {path}")
    if dry_run:
        print(rendered)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def copy_tree(src: Path, dest: Path, dry_run: bool) -> None:
    print(f"[copy] {src}  ->  {dest}")
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


# --------------------------------------------------------------------------- #
# Cursor
# --------------------------------------------------------------------------- #
def apply_cursor(extensions_dir: Path, settings_path: Path, install_icon: bool, dry_run: bool) -> None:
    print("\n=== Cursor ===")
    src = ASSETS / "extension"
    if not (src / "package.json").exists():
        raise FileNotFoundError(
            f"[apply_theme] Bundled Cursor extension assets missing\n"
            f"  Expected: {src / 'package.json'}"
        )
    dest = extensions_dir / CURSOR_EXTENSION_FOLDER
    copy_tree(src, dest, dry_run)
    if not dry_run:
        register_cursor_extension(extensions_dir, dest)

    fragment = json.loads((ASSETS / "settings.fragment.json").read_text(encoding="utf-8"))
    merge_json_settings(settings_path, fragment, indent=4, dry_run=dry_run)

    if install_icon:
        install_icon_theme(dry_run)


def register_cursor_extension(extensions_dir: Path, dest: Path) -> None:
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
        "relativeLocation": CURSOR_EXTENSION_FOLDER,
    }
    items = []
    if index.exists():
        try:
            items = json.loads(index.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    items = [it for it in items if it.get("relativeLocation") != CURSOR_EXTENSION_FOLDER]
    items.append(entry)
    index.write_text(json.dumps(items), encoding="utf-8")
    print(f"[extension] registered in {index}")


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


# --------------------------------------------------------------------------- #
# Obsidian
# --------------------------------------------------------------------------- #
def apply_obsidian(vault: Path, dry_run: bool) -> None:
    print(f"\n=== Obsidian vault: {vault} ===")
    dot = vault / ".obsidian"
    if not dot.exists():
        raise FileNotFoundError(
            f"[apply_theme] Not an Obsidian vault (no .obsidian dir)\n"
            f"  Path: {vault}\n"
            f"  Fix: pass a real vault root via --vault, or run --list-vaults."
        )
    src = ASSETS / "obsidian" / "themes" / OBSIDIAN_THEME_NAME
    if not (src / "theme.css").exists():
        raise FileNotFoundError(
            f"[apply_theme] Bundled Obsidian theme assets missing\n"
            f"  Expected: {src / 'theme.css'}"
        )
    copy_tree(src, dot / "themes" / OBSIDIAN_THEME_NAME, dry_run)

    fragment = json.loads((ASSETS / "obsidian" / "appearance.fragment.json").read_text(encoding="utf-8"))
    merge_json_settings(dot / "appearance.json", fragment, indent=2, dry_run=dry_run)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Apply IntelliJ Light (Maple) to Cursor and/or Obsidian.")
    parser.add_argument("--no-cursor", action="store_true", help="skip applying to Cursor")
    parser.add_argument("--no-icon", action="store_true", help="skip JetBrains icon-theme install (Cursor)")
    parser.add_argument("--vault", type=Path, action="append", default=[],
                        help="Obsidian vault root to apply to (repeatable)")
    parser.add_argument("--all-vaults", action="store_true",
                        help="apply to every Obsidian vault discovered in obsidian.json")
    parser.add_argument("--list-vaults", action="store_true", help="list discovered Obsidian vaults and exit")
    parser.add_argument("--cursor-settings", type=Path, default=cursor_settings_path())
    parser.add_argument("--cursor-extensions-dir", type=Path, default=cursor_extensions_dir())
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing")
    args = parser.parse_args()

    if args.list_vaults:
        vaults = discover_vaults()
        if not vaults:
            print("No Obsidian vaults found in obsidian.json.")
        for v in vaults:
            print(v)
        return

    print("=== IntelliJ Light (Maple) :: apply ===")

    if not args.no_cursor:
        apply_cursor(args.cursor_extensions_dir, args.cursor_settings,
                     install_icon=not args.no_icon, dry_run=args.dry_run)

    vaults = list(args.vault)
    if args.all_vaults:
        vaults = discover_vaults()
    for vault in vaults:
        apply_obsidian(vault, args.dry_run)

    print("\nDone.")
    print("  Cursor:   run 'Developer: Reload Window' (Cmd/Ctrl+Shift+P).")
    if vaults:
        print("  Obsidian: run 'Reload app without saving' (Cmd/Ctrl+P) in each vault.")
    if args.dry_run:
        print("(dry-run: nothing was written)")


if __name__ == "__main__":
    main()
