#!/bin/bash
TMP_DIR="$1"
finished_file="$2"
gdal_translate "$TMP_DIR/B02.jp2" "$TMP_DIR/B02.tif" > /dev/null
gdal_translate "$TMP_DIR/B03.jp2" "$TMP_DIR/B03.tif" > /dev/null 
gdal_translate "$TMP_DIR/B04.jp2" "$TMP_DIR/B04.tif" > /dev/null 
gdal_translate "$TMP_DIR/B05.jp2" "$TMP_DIR/B05.tif" > /dev/null 
gdal_translate "$TMP_DIR/B06.jp2" "$TMP_DIR/B06.tif" > /dev/null 
gdal_translate "$TMP_DIR/B07.jp2" "$TMP_DIR/B07.tif" > /dev/null 
gdal_translate "$TMP_DIR/B08.jp2" "$TMP_DIR/B08.tif" > /dev/null 
gdal_translate "$TMP_DIR/B8A.jp2" "$TMP_DIR/B8A.tif" > /dev/null 
gdal_translate "$TMP_DIR/B09.jp2" "$TMP_DIR/B09.tif" > /dev/null 
gdal_translate "$TMP_DIR/B11.jp2" "$TMP_DIR/B11.tif" > /dev/null 
gdal_translate "$TMP_DIR/B12.jp2" "$TMP_DIR/B12.tif" > /dev/null 
gdal_translate "$TMP_DIR/AOT.jp2" "$TMP_DIR/AOT.tif" > /dev/null 

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

rm -rf "$TMP_DIR"

