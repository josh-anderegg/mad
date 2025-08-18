#!/bin/bash
download_dir="$1"
image_key="$2"
name="$3"

files=(
  "R20m/SCL.jp2"
)

for file in "${files[@]}"; do
  s3_path="https://sentinel-s2-l2a.s3.amazonaws.com/${image_key}${file}"
  local_path="$download_dir/$name"

  if [ ! -f "$local_path" ]; then
      echo "Downloading $s3_path ..."
      if ! wget -O "$local_path" --tries=10 --timeout=10 --retry-connrefused --waitretry=5 -d "$s3_path" &> "$download_dir/${name}_wget.log"; then
          echo "Download failed for $s3_path" >&2
          echo "See log file: $download_dir/${name}_wget.log" >&2
          exit 1
      fi
  fi
done
