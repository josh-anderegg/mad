#!/bin/bash
download_dir="$1"
image_key="$2"
name="$3"

files=(
  "R10m/TCI.jp2"
)

for file in "${files[@]}"; do
  s3_path="https://sentinel-s2-l2a.s3.amazonaws.com/${image_key}${file}"
  local_path="$download_dir/$name"
  if [ ! -f "$local_path" ]; then
          if ! wget --tries=10 --timeout=10 "$s3_path" -O "$local_path"; then
              echo "Download failed for $s3_path" >&2
              exit 1
          fi
  fi
done
