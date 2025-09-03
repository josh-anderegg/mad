#!/bin/bash
TMP_DIR="$1"
finished_file="$2"
files=()

for file in "$3"; do 
  file=$(basename $file)
  name="${file%.jp2}"
  gdal_translate "$TMP_DIR/${name}.jp2" "$TMP_DIR/${name}.tif" > /dev/null
  files+="$TMP_DIR/${name}.tif"
done

gdalbuildvrt -separate "$TMP_DIR/combined.vrt" "${files[@]}" > /dev/null 

gdal_translate "$TMP_DIR/combined.vrt" "$finished_file"  > /dev/null

rm -rf "$TMP_DIR"

