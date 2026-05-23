#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

################################
# 参数处理：支持默认当前目录
################################
if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [source_dir]"
  exit 1
fi

SRC_DIR="${1:-.}"

DEBUG="${DEBUG:-0}"

DEST_DIR="/Users/nicole/Music/我喜欢的单曲"
MANUAL_DIR="/Users/nicole/Music/待人工处理"
ALBUM_NAME="我喜欢的单曲"

################################
# 基础检查
################################
[[ -d "$SRC_DIR" ]] || { echo "Source directory not found: $SRC_DIR"; exit 1; }

command -v metaflac >/dev/null || {
  echo "metaflac not found (brew install flac)"
  exit 1
}

mkdir -p "$DEST_DIR" "$MANUAL_DIR"

echo "Scanning FLAC files from:"
echo "  $SRC_DIR"
echo
echo "Writing normalized files to:"
echo "  $DEST_DIR"
echo
echo "Manual review directory:"
echo "  $MANUAL_DIR"
echo
echo "Setting ALBUM tag to:"
echo "  $ALBUM_NAME"
echo

################################
# 工具函数
################################

trim() {
  sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

dbg() {
  [[ "$DEBUG" == "1" ]] || return 0
  echo "[DEBUG] $*" >&2
}

dbg_kv() {
  [[ "$DEBUG" == "1" ]] || return 0
  local k="$1"
  local v="$2"
  echo "[DEBUG] $k=<$v>" >&2
}

read_tag() {
  local file="$1" tag="$2"
  metaflac --show-tag="$tag" "$file" 2>/dev/null | sed "s/^$tag=//" || true
}

# 去重但保留顺序（A; A → A）
dedup_tag() {
  echo "$1" | awk -F'; *' '
    {
      for (i=1; i<=NF; i++) {
        if (!seen[$i]++) {
          out = out (out ? "; " : "") $i
        }
      }
    }
    END { print out }
  '
}

# 是否存在多个不同值（语义冲突）
has_conflict() {
  local uniq
  uniq=$(echo "$1" | awk -F'; *' '{for(i=1;i<=NF;i++) a[$i]++} END{print length(a)}')
  [[ "$uniq" -gt 1 ]]
}

# 从文件名解析 Artist - Title
parse_from_filename() {
  local name="${1%.flac}"
  dbg "parse_from_filename: name=<$name>"
  if [[ "$name" =~ ^(.+)[[:space:]]-[[:space:]](.+)$ ]]; then
    artist="$(echo "${BASH_REMATCH[1]}" | trim)"
    title="$(echo "${BASH_REMATCH[2]}" | trim)"
    dbg_kv "parsed_artist" "$artist"
    dbg_kv "parsed_title" "$title"
    return 0
  fi
  return 1
}

send_to_manual() {
  local src="$1"
  local base
  base="$(basename "$src")"
  [[ -e "$MANUAL_DIR/$base" ]] || cp "$src" "$MANUAL_DIR/"
  echo "[MANUAL] $base"
}

################################
# 主流程
################################
copied=0
manual=0
skipped=0

while IFS= read -r -d '' src; do
  base="$(basename "$src")"

  dbg "--------------------------------"
  dbg "src=<$src>"
  dbg "base=<$base>"

  RAW_TITLE="$(read_tag "$src" TITLE | paste -sd'; ' -)"
  RAW_ARTIST="$(read_tag "$src" ARTIST | paste -sd'; ' -)"

  dbg_kv "RAW_TITLE" "$RAW_TITLE"
  dbg_kv "RAW_ARTIST" "$RAW_ARTIST"

  # 冲突检测
  if has_conflict "$RAW_TITLE" || has_conflict "$RAW_ARTIST"; then
    dbg "conflict_detected=1"
    send_to_manual "$src"
    ((++manual))
    continue
  fi

  dbg "conflict_detected=0"

  title="$(dedup_tag "$RAW_TITLE" | trim)"
  artist="$(dedup_tag "$RAW_ARTIST" | trim)"

  dbg_kv "dedup_title" "$title"
  dbg_kv "dedup_artist" "$artist"

  # 标签缺失 → 文件名兜底
  if [[ -z "$title" || -z "$artist" ]]; then
    dbg "missing_tag_fallback=1"
    if ! parse_from_filename "$base"; then
      dbg "filename_parse_failed=1"
      send_to_manual "$src"
      ((++manual))
      continue
    fi
    dbg "filename_parse_failed=0"
  fi

  dbg_kv "final_title" "$title"
  dbg_kv "final_artist" "$artist"

  safe_artist="${artist//\//_}"
  safe_title="${title//\//_}"
  dest="$DEST_DIR/$safe_artist - $safe_title.flac"

  dbg_kv "dest" "$dest"

  if [[ -e "$dest" ]]; then
    echo "[SKIP] Exists: $(basename "$dest")"
    ((++skipped))
    continue
  fi

  dbg "copying_to_dest=1"

  cp "$src" "$dest"

  dbg "metaflac_tagging=1"
  metaflac \
    --remove-tag=TITLE \
    --remove-tag=ARTIST \
    --remove-tag=ALBUM \
    --set-tag="TITLE=$title" \
    --set-tag="ARTIST=$artist" \
    --set-tag="ALBUM=$ALBUM_NAME" \
    "$dest" >/dev/null
  dbg "metaflac_tagging=0"

  echo "[COPY] $(basename "$dest")"
  ((++copied))

done < <(find "$SRC_DIR" -type f -iname "*.flac" -print0)

################################
# 汇总
################################
echo
echo "Done."
echo "  Copied & normalized : $copied files"
echo "  Sent to manual pool : $manual files"
echo "  Skipped (exists)    : $skipped files"
