#!/bin/sh
metadata=$1
name="${metadata%.json}"
working_dir=$(dirname "$metadata")

TMP_DIR=$(mktemp -d)
LOG_FILE="${name}.tlog"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[$input]:Image Download" > "$LOG_FILE"

# # Possible early return in case we already have the data downloaded for a tile
finished_file="${name}_tci.tif"

if jq -e 'length == 0' "$metadata" > /dev/null; then
    echo "Skipping $name — metadata file is empty" >> "$LOG_FILE"
    exit 1
fi

spring=$(
  jq -r '
    [ .[]
      | select(
          (.sensing_time | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | .[1] + 1) as $month
          | $month >= 3 and $month <= 5 and
            .snow < 40 and
            .cloud_coverage < 20
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata" | sed 's/metadata.xml//'
)

summer=$(
  jq -r '
    [ .[]
      | select(
          (.sensing_time | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | .[1] + 1) as $month
          | $month >= 6 and $month <= 8 and
            .snow < 20 and
            .cloud_coverage < 20 and
            .no_data < 50
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata" | sed 's/metadata.xml//'
)

fall=$(
  jq -r '
    [ .[]
      | select(
          (.sensing_time | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | .[1] + 1) as $month
          | $month >= 9 and $month <= 11 and
            .snow < 10 and
            .cloud_coverage < 20 and
            .no_data < 50
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata" | sed 's/metadata.xml//'
)

scl_files=()
scene_ids=()
MAX_IMAGES=8
i=0
for scene in $summer; do
  if [ "$i" -ge "$MAX_IMAGES" ]; then
    break
  fi

  scl_file="$(basename "$name")_scl_${i}.jp2"

  # Download SCL
  $SCRIPT_DIR/s3_download_scl.sh "$TMP_DIR" "$scene" "$scl_file"

  # Reclassify unwanted classes
  clean_scl="$TMP_DIR/clean_${scl_file%.jp2}.tif"
  gdal_calc.py -A "$TMP_DIR/$scl_file" \
    --outfile="$clean_scl" \
    --calc="((A==2)+(A==4)+(A==5)+(A==6)+(A==7))" \
   --type=Byte --format=GTiff --overwrite --quiet \
   --NoDataValue=None   

  # Resample to match TCI
  resampled_scl="$TMP_DIR/resampled_${scl_file%.jp2}.tif"
  gdalwarp -tr 10 10 -r nearest -overwrite "$clean_scl" "$resampled_scl"

  # Append only the file that actually exists
  scl_files+=("$resampled_scl")
  scene_ids+=("$scene")

  ((i++))
done

img_files=()
j=0
for scene in "${scene_ids[@]}"; do
  img_file="$(basename "$name")_tci_${j}.jp2"
  $SCRIPT_DIR/s3_download_tci.sh "$TMP_DIR" "$scene" "$img_file" 
  img_files+=("$TMP_DIR/$img_file")
  ((j++))
done

out_img="${name}_tci_merged.tif"
cur_scl="${name}_scl_merged.tif"

base_img="$TMP_DIR/base.tif"

gdalwarp "${img_files[0]}" "$base_img" \
  -of GTiff \
  -dstnodata 0 \
  -co INTERLEAVE=PIXEL \
  -co COMPRESS=DEFLATE \
  -co TILED=YES

# Step 2: Mask all subsequent images with their SCL
for idx in $(seq 0 $((${#img_files[@]}-1))); do
  img="${img_files[$idx]}"
  scl="${scl_files[$idx]}"
  out_masked="$TMP_DIR/masked_${idx}.tif"

  echo "Masking: $img with SCL: $scl"

  gdal_calc.py -A "$img" -B "$scl" \
    --outfile="$out_masked" \
    --calc="where(B==0, nan, A)" \
    --allBands=A \
    --type=Byte --quiet --overwrite \
    --NoDataValue=0 \
    --format=GTiff --creation-option="INTERLEAVE=PIXEL"

  masked_files+=("$out_masked")
done

reversed_files=($(printf "%s\n" "${masked_files[@]}" | tac))

gdal_merge.py -o "$out_img" -n 0 -a_nodata 0 -of GTiff "$base_img" "${reversed_files[@]}"
echo "Final merged SCL: $out_scl"
echo "Final merged TCI: $out_img"
echo "Done" >> "$LOG_FILE"
rm -rf $TMP_DIR
