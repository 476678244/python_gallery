#!/usr/bin/env bash
set -euo pipefail

############################
# 配置区
############################

SRC_DIR="${1:-$(pwd)}"
DST_DIR="$HOME/Music/我喜欢的单曲"
MANUAL_DIR="$HOME/Music/待人工处理"
ALBUM_NAME="我喜欢的单曲"

############################
# 基础检查
############################

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Source directory not found: $SRC_DIR"
  exit 1
fi

command -v metaflac >/dev/null || {
  echo "metaflac not found (brew install flac)"
  exit 1
}

mkdir -p "$DST_DIR" "$MANUAL_DIR"

echo "Scanning FLAC files from:"
echo "  $SRC_DIR"
echo
echo "Writing normalized files to:"
echo "  $DST_DIR"
echo
echo "Manual review directory:"
echo "  $MANUAL_DIR"
echo
echo "Setting ALBUM tag to:"
echo "  $ALBUM_NAME"
echo

############################
# 工具函数
############################

# 去重但保留顺序
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

# 是否存在语义冲突（>1 个不同值）
has_conflict() {
  local uniq
  uniq=$(echo "$1" | awk -F'; *' '{for(i=1;i<=NF;i++) a[$i]++} END{print length(a)}')
  [[ "$uniq" -gt 1 ]]
}

############################
# 主流程
############################

find "$SRC_DIR" -type f -name "*.flac" | while read -r src; do
  filename="$(basename "$src")"
  dst="$DST_DIR/$filename"

  RAW_TITLE=$(metaflac --show-tag=TITLE "$src" | sed 's/^TITLE=//' | paste -sd'; ' -)
  RAW_ARTIST=$(metaflac --show-tag=ARTIST "$src" | sed 's/^ARTIST=//' | paste -sd'; ' -)

  # 冲突检测 → 人工处理
  if has_conflict "$RAW_TITLE" || has_conflict "$RAW_ARTIST"; then
    echo "[MANUAL] $filename (conflicting TITLE or ARTIST)"
    cp -n "$src" "$MANUAL_DIR/"
    continue
  fi

  TITLE=$(dedup_tag "$RAW_TITLE")
  ARTIST=$(dedup_tag "$RAW_ARTIST")

  echo "[COPY] $filename"

  cp -n "$src" "$dst"

  metaflac \
    --remove-tag=TITLE \
    --remove-tag=ARTIST \
    --remove-tag=ALBUM \
    --set-tag="TITLE=$TITLE" \
    --set-tag="ARTIST=$ARTIST" \
    --set-tag="ALBUM=$ALBUM_NAME" \
    "$dst"

done
