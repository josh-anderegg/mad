#!/bin/bash
TMP_DIR="$1"
finished_file="$2"
shift 2
files=()
for file in "$@"; do 
  file=$(basename $file)
  name="${file%.jp2}"
  gdal_translate "$TMP_DIR/${name}.jp2" "$TMP_DIR/${name}.tif" > /dev/null
  files+=("$TMP_DIR/${name}.tif")
done

gdalbuildvrt -separate -resolution highest "$TMP_DIR/combined.vrt" "${files[@]}" > /dev/null
gdal_translate -ot UInt16 "$TMP_DIR/combined.vrt" "$TMP_DIR/finished.tif" > /dev/null
gdal_translate -of JP2OpenJPEG -r cubic "$TMP_DIR/finished.tif" "$finished_file" > /dev/null
rm -rf "$TMP_DIR"
