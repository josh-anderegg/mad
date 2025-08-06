#!/bin/sh
dir="$1"
min_size=$((740 * 1024 * 1024))  # 740MB

for file in "$dir"/*.tif; do
  [ -e "$file" ] || continue
  size=$(stat -c%s "$file")

  if [ "$size" -lt "$min_size" ];  then
    base=$(basename "$file" .tif)
    json="$dir/$base.json"
    ./s3_image_from_metadata.sh "$json"
  fi
done
