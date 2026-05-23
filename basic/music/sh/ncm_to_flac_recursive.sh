#!/usr/bin/env bash

set -euo pipefail

ROOT="/Users/nicole/Music/网易云音乐"

# 如果 ncmdump 已加入 PATH
#NCMDUMP="ncmdump"

# 如果没有加入 PATH，请用这一行替换上面那行
NCMDUMP="/Users/nicole/workspace/github/ncmdump/build/ncmdump"

echo "Scanning: $ROOT"
echo

find "$ROOT" -type f -name "*.ncm" | while read -r ncm_file; do
    dir="$(dirname "$ncm_file")"
    base="$(basename "$ncm_file" .ncm)"

    # 可能的输出文件
    flac="$dir/$base.flac"
    mp3="$dir/$base.mp3"

    # 已经转换过就跳过
    if [[ -f "$flac" || -f "$mp3" ]]; then
        echo "[SKIP] already converted: $ncm_file"
        continue
    fi

    echo "[CONVERT] $ncm_file"
    (
        cd "$dir"
        "$NCMDUMP" "$ncm_file"
    )
done

echo
echo "Done."

