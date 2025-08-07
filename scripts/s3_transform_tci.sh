#!/bin/bash

TMP_DIR="$1"
finished_file="$2"
finished_file="${finished_file%.tif}.jp2"
# Step 1: Convert .jp2 to .tif and resample all bands to 10m
# gdal_translate "$TMP_DIR/TCI.jp2" "$finished_file" > /dev/null

mv "$TMP_DIR/TCI.jp2" "$finished_file"

rm -rf "$TMP_DIR"

