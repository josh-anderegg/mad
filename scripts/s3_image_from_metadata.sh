#!/bin/sh
metadata=$1
name="${metadata%.json}"
# Possible early return in case we already have the data downloaded for a tile
finished_file="${name}.tif"
if [ -f "$finished_file" ]; then
    echo "Skipping $name — as .tif already exists"
    exit 0
fi

TMP_DIR=$(mktemp -d "./tmp.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

best_file=$(
  jq -r '
    [ .[]
      | select(
          .cloud_coverage < 20 and
          .no_data < 10
        )
    ]
    | sort_by(.cloud_coverage)
    | .[0].metadata_key
  ' "$metadata"
)

if [ -z "$best_file" ]; then
    echo "No suitable image found for $name"
    exit 1
fi

files=(
    "R10m/B02.jp2"
    "R10m/B03.jp2"
    "R10m/B04.jp2"
    "R20m/B05.jp2"
    "R20m/B06.jp2"
    "R20m/B07.jp2"
    "R10m/B08.jp2"
    "R20m/B8A.jp2"
    "R60m/B09.jp2"
    "R20m/B11.jp2"
    "R20m/B12.jp2"
    "R10m/AOT.jp2"
)

image_key=$(echo "$best_file" | sed 's/metadata.xml//')

for file in "${files[@]}"; do
    s3_path="https://sentinel-s2-l2a.s3.amazonaws.com/${image_key}${file}"
    local_path="$TMP_DIR/$(basename "$file")"
    if [ ! -f "$local_path" ]; then
        wget -nv --tries=3 --timeout=10 "$s3_path" -O "$local_path"
    fi
done

gdal_translate "$TMP_DIR/B02.jp2" "$TMP_DIR/B02.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B03.jp2" "$TMP_DIR/B03.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B04.jp2" "$TMP_DIR/B04.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B05.jp2" "$TMP_DIR/B05.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B06.jp2" "$TMP_DIR/B06.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B07.jp2" "$TMP_DIR/B07.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B08.jp2" "$TMP_DIR/B08.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B8A.jp2" "$TMP_DIR/B8A.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B09.jp2" "$TMP_DIR/B09.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B11.jp2" "$TMP_DIR/B11.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/B12.jp2" "$TMP_DIR/B12.tif" > /dev/null 2>&1
gdal_translate "$TMP_DIR/AOT.jp2" "$TMP_DIR/AOT.tif" > /dev/null 2>&1

gdalbuildvrt -separate "$TMP_DIR/combined.vrt" "$TMP_DIR/B04.tif" "$TMP_DIR/B03.tif" "$TMP_DIR/B02.tif" "$TMP_DIR/B05.tif"  "$TMP_DIR/B06.tif"  "$TMP_DIR/B07.tif"  "$TMP_DIR/B08.tif"  "$TMP_DIR/B8A.tif"  "$TMP_DIR/B09.tif" "$TMP_DIR/B11.tif"  "$TMP_DIR/B12.tif"  "$TMP_DIR/AOT.tif" > /dev/null 
# Add band descriptions to VRT
BAND_DESC=("B4: (Red)" "B3: (Green)" "B2: (Blue)" "B5: (Red Edge 1)" "B6: (Red Edge 2)" "B7: (Red Edge 3)" "B8: (Near Infrared)" "B8A: (Narrow Near Infrared)" "B9: (Water vapor)" "B11: (SWIR 1)" "B12: (SWIR 2)" "AOT: (Aerorosol Optical Thickness)")
i=1
for band in "${BAND_DESC[@]}"; do
  # Insert <Description> into each band of VRT
  sed -i "/<VRTRasterBand.*band=\"${i}\"/a\\
  <Description>${band}</Description>" "$TMP_DIR/combined.vrt"
  i=$((i+1))
done

gdal_translate "$TMP_DIR/combined.vrt" "$finished_file"  > /dev/null
