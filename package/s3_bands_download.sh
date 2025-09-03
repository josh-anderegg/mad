#!/bin/bash
download_dir="$1"
image_key="$2"
shift 2

files=(
  $@
)

for file in "${files[@]}"; do
  s3_path="https://sentinel-s2-l2a.s3.amazonaws.com/${image_key}${file}"
  local_path="$download_dir/$(basename "$file")"
  if ! wget -q --tries=10 --timeout=10 "$s3_path" -O "$local_path"; then
    echo "Download failed for $s3_path" >&2
    exit 1
  fi
done
