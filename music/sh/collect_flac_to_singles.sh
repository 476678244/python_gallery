#!/usr/bin/env bash

# ====== 可配置项 ======
SRC_DIR="${1:-/Users/nicole/Music/网易云音乐}"
DEST_DIR="/Users/nicole/Music/单曲"
# ======================

echo "Scanning FLAC files from:"
echo "  $SRC_DIR"
echo "Copying to:"
echo "  $DEST_DIR"
echo

mkdir -p "$DEST_DIR"

count=0

while IFS= read -r flac; do
    base="$(basename "$flac")"
    dest="$DEST_DIR/$base"

    # 若同名文件已存在，自动追加编号
    if [[ -e "$dest" ]]; then
        i=1
        name="${base%.*}"
        ext="${base##*.}"
        while [[ -e "$DEST_DIR/${name}_${i}.${ext}" ]]; do
            ((i++))
        done
        dest="$DEST_DIR/${name}_${i}.${ext}"
    fi

    cp "$flac" "$dest"
    echo "[COPY] $flac -> $dest"
    ((count++))

done < <(find "$SRC_DIR" -type f -iname "*.flac")

echo
echo "Done. Copied $count FLAC files."
