#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SRC_DIR="$(pwd)"
DEST_DIR="/Users/nicole/Music/我喜欢的单曲"
MANUAL_DIR="/Users/nicole/Music/待人工处理"
ALBUM_NAME="我喜欢的单曲"

mkdir -p "$DEST_DIR" "$MANUAL_DIR"

echo "Scanning FLAC files from:"
echo "  $SRC_DIR"
echo
echo "Writing normalized files to:"
echo "  $DEST_DIR"
echo
echo "Setting ALBUM tag to:"
echo "  $ALBUM_NAME"
echo

copied=0
manual=0

command -v metaflac >/dev/null 2>&1 || {
  echo "ERROR: metaflac not found (brew install flac)"
  exit 1
}

trim() {
  sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

read_tag() {
  local file="$1"
  local tag="$2"
  metaflac --show-tag="$tag" "$file" 2>/dev/null | sed "s/^$tag=//" || true
}

parse_from_filename() {
  local name="${1%.flac}"

  if [[ "$name" =~ ^(.+)[[:space:]]-[[:space:]](.+)$ ]]; then
    artist="$(echo "${BASH_REMATCH[1]}" | trim)"
    title="$(echo "${BASH_REMATCH[2]}" | trim)"
    return 0
  fi
  return 1
}

copy_to_manual() {
  local src="$1"
  local base
  base="$(basename "$src")"

  if [[ ! -e "$MANUAL_DIR/$base" ]]; then
    cp "$src" "$MANUAL_DIR/"
  fi

  echo "[SKIP→MANUAL] $base"
  ((++manual))
}

while IFS= read -r -d '' src; do
  base="$(basename "$src")"

  artist="$(read_tag "$src" "ARTIST" | trim)"
  title="$(read_tag "$src" "TITLE" | trim)"

  if [[ -z "$artist" || -z "$title" ]]; then
    if ! parse_from_filename "$base"; then
      copy_to_manual "$src"
      continue
    fi
  fi

  safe_artist="${artist//\//_}"
  safe_title="${title//\//_}"
  dest="$DEST_DIR/$safe_artist - $safe_title.flac"

  if [[ -e "$dest" ]]; then
    echo "[SKIP] Exists: $(basename "$dest")"
    continue
  fi

  cp "$src" "$dest"

  metaflac \
    --remove-tag=ALBUM \
    --set-tag="ALBUM=$ALBUM_NAME" \
    --set-tag="ARTIST=$artist" \
    --set-tag="TITLE=$title" \
    "$dest" >/dev/null 2>&1

  echo "[COPY] $(basename "$dest")"
  ((++copied))

done < <(find "$SRC_DIR" -type f -iname "*.flac" -print0)

echo
echo "Done."
echo "  Copied & normalized : $copied files"
echo "  Sent to manual pool : $manual files"
