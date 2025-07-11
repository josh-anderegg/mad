#!/bin/bash
# Script for 
process_file() {
    file="$1"
    [ -e "$file" ] || exit 0

    base=$(basename "$file" .tif)
    temp_warped="../data/temp/${base}.tif"
    jpg="../data/final_jpgs/${base}.jpg"

    gdalwarp -t_srs EPSG:3857 "$file" "$temp_warped" > /dev/null 2>&1
    gdal_translate -b 1 -b 2 -b 3 -ot Byte -scale -of JPEG -outsize 512 512 "$warped" "$jpg" > /dev/null 2>&1
    rm "$tmp_warp"
}

export -f process_file

find ../data/images -name '*.tif' -print0 | xargs -0 -n 1 -P 12 bash -c 'process_file "$0"'