#!/bin/sh
name=$1
working_dir=$2
metadata_file=${working_dir}/${name}.json
shift 2

TMP_DIR=$(mktemp -d)
LOG_FILE="${working_dir}${name}_downloading.tlog"
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_IMAGES=8

echo "[$input]:Image Download" > "$LOG_FILE"

# # Possible early return in case we already have the data downloaded for a tile
finished_file="${name}.jp2"

if jq -e 'length == 0' "$metadata_file" > /dev/null; then
    echo "Skipping $name — metadata file is empty" >> "$LOG_FILE"
    exit 1
fi

read sensing_time metadata_key < <(
  jq -r '
    [ .[]
      | select(
          .cloud_coverage < 20 and
          .snow < 20 and
          .no_data < 10
        )
    ]
    | sort_by(.cloud_coverage + .snow)
    | .[0] 
    | [.sensing_time, .metadata_key]
    | @tsv
  ' "$metadata_file"
)

if [ -z "$metadata_key" ] || [ "$metadata_key" = "null" ]; then
    echo "No suitable image found for $name" >> "$LOG_FILE"
    exit 1
fi

closest=$(
  jq -r --arg ref "$sensing_time" '
    def to_epoch:
      sub("\\..*Z$"; "")
      | strptime("%Y-%m-%dT%H:%M:%S")
      | mktime;

    def to_day:
      sub("\\..*Z$"; "")
      | strptime("%Y-%m-%dT%H:%M:%S")
      | strftime("%Y-%m-%d");

    [ .[] 
      | { key: .metadata_key, t: (.sensing_time | to_epoch), clouds: .cloud_coverage, day: .sensing_time | to_day }
      | select(.cloud_coverage < 40 )
    ]
    | ( $ref | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | mktime ) as $ref_epoch
    | unique_by(.day)
    | sort_by( ( .t - $ref_epoch ) | abs )
    | .[:8]
    | .[].key
  ' "$metadata_file"
)

scl_files=()
scene_ids=()
i=0
for scene in $closest; do

  scl_file="$TMP_DIR/SCL.jp2"

  # Download SCL
  $PACKAGE_DIR/s3_bands_download.sh "$TMP_DIR" "$scene" "R20m/SCL.jp2"

  # Reclassify unwanted classes
  clean_scl="$TMP_DIR/SCL_${i}.tif"
  gdal_calc.py -A "$scl_file" \
    --outfile="$clean_scl" \
    --calc="((A==2)+(A==4)+(A==5)+(A==6)+(A==7))" \
   --type=Byte --format=GTiff --overwrite --quiet \
   --NoDataValue=None   

  # Resample to match TCI
  resampled_scl="$TMP_DIR/resampled_${i}.tif"
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
echo "Done" >> "$LOG_FILE"
rm -rf $TMP_DIR
