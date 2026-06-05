#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def trim(s: str) -> str:
    return s.strip()


def dbg(enabled: bool, msg: str) -> None:
    if not enabled:
        return
    print(f"[DEBUG] {msg}", file=sys.stderr)


def dbg_kv(enabled: bool, k: str, v: str) -> None:
    if not enabled:
        return
    print(f"[DEBUG] {k}=<{v}>", file=sys.stderr)


def read_tag(file_path: Path, tag: str) -> str:
    try:
        proc = subprocess.run(
            ["metaflac", f"--show-tag={tag}", str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""

    values: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith(f"{tag}="):
            values.append(line[len(tag) + 1 :])
    return "; ".join(values)


def split_semicolon_values(s: str) -> list[str]:
    s = trim(s)
    if not s:
        return []
    parts = re.split(r";\s*", s)
    return [p for p in (trim(x) for x in parts) if p]


def dedup_tag(s: str) -> str:
    out: list[str] = []
    seen: set[str] = set()
    for part in split_semicolon_values(s):
        if part in seen:
            continue
        seen.add(part)
        out.append(part)
    return "; ".join(out)


def has_conflict(s: str) -> bool:
    parts = split_semicolon_values(s)
    return len(set(parts)) > 1


def parse_from_filename(base_name: str, debug_enabled: bool) -> tuple[str, str] | None:
    name = re.sub(r"\.flac$", "", base_name, flags=re.IGNORECASE)
    dbg(debug_enabled, f"parse_from_filename: name=<{name}>")
    m = re.match(r"^(.+?)\s-\s(.+)$", name)
    if not m:
        return None
    artist = trim(m.group(1))
    title = trim(m.group(2))
    dbg_kv(debug_enabled, "parsed_artist", artist)
    dbg_kv(debug_enabled, "parsed_title", title)
    return artist, title


def send_to_manual(src: Path, manual_dir: Path) -> None:
    base = src.name
    dest = manual_dir / base
    if not dest.exists():
        shutil.copy2(src, manual_dir)
    print(f"[MANUAL] {base}")


def require_metaflac() -> None:
    if shutil.which("metaflac") is None:
        print("metaflac not found (brew install flac)")
        raise SystemExit(1)


def iter_flac_files(src_dir: Path):
    for p in src_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".flac":
            yield p


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source_dir", nargs="?")
    parser.add_argument("-h", "--help", action="help")
    args = parser.parse_args(argv)

    # Set default source directory if not provided
    src_dir = Path(args.source_dir) if args.source_dir else Path("/Users/nicole/Music/单曲")

    debug_enabled = os.environ.get("DEBUG", "0") == "1"

    dest_dir = Path("/Users/nicole/Music/我喜欢的单曲")
    manual_dir = Path("/Users/nicole/Music/待人工处理")
    album_name = "我喜欢的单曲"

    if not src_dir.is_dir():
        print(f"Source directory not found: {src_dir}")
        return 1

    require_metaflac()

    dest_dir.mkdir(parents=True, exist_ok=True)
    manual_dir.mkdir(parents=True, exist_ok=True)

    print("Scanning FLAC files from:")
    print(f"  {src_dir}")
    print()
    print("Writing normalized files to:")
    print(f"  {dest_dir}")
    print()
    print("Manual review directory:")
    print(f"  {manual_dir}")
    print()
    print("Setting ALBUM tag to:")
    print(f"  {album_name}")
    print()

    copied = 0
    manual = 0
    skipped = 0

    for src in iter_flac_files(src_dir):
        base = src.name

        dbg(debug_enabled, "--------------------------------")
        dbg(debug_enabled, f"src=<{src}>")
        dbg(debug_enabled, f"base=<{base}>")

        raw_title = read_tag(src, "TITLE")
        raw_artist = read_tag(src, "ARTIST")

        dbg_kv(debug_enabled, "RAW_TITLE", raw_title)
        dbg_kv(debug_enabled, "RAW_ARTIST", raw_artist)

        if has_conflict(raw_title) or has_conflict(raw_artist):
            dbg(debug_enabled, "conflict_detected=1")
            send_to_manual(src, manual_dir)
            manual += 1
            continue

        dbg(debug_enabled, "conflict_detected=0")

        title = trim(dedup_tag(raw_title))
        artist = trim(dedup_tag(raw_artist))

        dbg_kv(debug_enabled, "dedup_title", title)
        dbg_kv(debug_enabled, "dedup_artist", artist)

        if not title or not artist:
            dbg(debug_enabled, "missing_tag_fallback=1")
            parsed = parse_from_filename(base, debug_enabled)
            if parsed is None:
                dbg(debug_enabled, "filename_parse_failed=1")
                send_to_manual(src, manual_dir)
                manual += 1
                continue
            dbg(debug_enabled, "filename_parse_failed=0")
            artist, title = parsed

        dbg_kv(debug_enabled, "final_title", title)
        dbg_kv(debug_enabled, "final_artist", artist)

        safe_artist = artist.replace("/", "_")
        safe_title = title.replace("/", "_")
        dest = dest_dir / f"{safe_artist} - {safe_title}.flac"

        dbg_kv(debug_enabled, "dest", str(dest))

        if dest.exists():
            print(f"[SKIP] Exists: {dest.name}")
            skipped += 1
            continue

        dbg(debug_enabled, "copying_to_dest=1")
        shutil.copy2(src, dest)

        dbg(debug_enabled, "metaflac_tagging=1")
        subprocess.run(
            [
                "metaflac",
                "--remove-tag=TITLE",
                "--remove-tag=ARTIST",
                "--remove-tag=ALBUM",
                f"--set-tag=TITLE={title}",
                f"--set-tag=ARTIST={artist}",
                f"--set-tag=ALBUM={album_name}",
                str(dest),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        dbg(debug_enabled, "metaflac_tagging=0")

        print(f"[COPY] {dest.name}")
        copied += 1

    print()
    print("Done.")
    print(f"  Copied & normalized : {copied} files")
    print(f"  Sent to manual pool : {manual} files")
    print(f"  Skipped (exists)    : {skipped} files")

    return 0


if __name__ == "__main__":
    # Enable debug output by default
    os.environ["DEBUG"] = "1"
    raise SystemExit(main(sys.argv[1:]))
