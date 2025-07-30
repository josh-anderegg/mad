#!/bin/sh
input=$1
output=$2

# Possible early return in case we already have the data downloaded for a tile
finished_file="${output}/${input}"
if [ -d "$finished_file" ]; then
    echo "Skipping $input — output folder exists."
    exit 0
fi

fst=${input:0:2}
mid=${input:2:1}
lst=${input:3:2}
S3_PATH="s3://sentinel-s2-l2a/tiles/$fst/$mid/$lst/2019"
TMP_DIR=$(mktemp -d "${output}/tmp.XXXXXX")
candidate_file="$TMP_DIR/candidates.txt"

# List all metadata.xml files (full S3 keys)
aws s3 ls "$S3_PATH" --recursive --no-sign-request | grep metadata.xml | awk '{print $4}' > "$TMP_DIR/metadata_files.txt"

get_quality_metrics() {
  local metadata_s3_key=$1
  local nr=$2
  local local_file="${output}/${input}/metadata_${nr}.xml"
  if [ ! -f "$local_file" ]; then
    wget -nv "https://sentinel-s2-l2a.s3.amazonaws.com/$metadata_s3_key" -O "$local_file"
  fi
  read cloud_coverage no_data snow degraded_msi degraded_saturation darkness < <(
    xmllint --xpath \
    "concat(
      string(//CLOUDY_PIXEL_PERCENTAGE), ' ',
      string(//NODATA_PIXEL_PERCENTAGE), ' ',
      string(//SNOW_ICE_PERCENTAGE), ' ',
      string(//DEGRADED_MSI_DATA_PERCENTAGE), ' ',
      string(//SATURATED_DEFECTIVE_PIXEL_PERCENTAGE), ' ',
      string(//DARK_FEATURES_PERCENTAGE)
    )" "$local_file" 2>/dev/null
  )
  # cloud_coverage=$(xmllint --xpath "string(//CLOUDY_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  # no_data=$(xmllint --xpath "string(//NODATA_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  # snow=$(xmllint --xpath "string(//SNOW_ICE_PERCENTAGE)" "$local_file" 2>/dev/null)
  # degraded_msi=$(xmllint --xpath "string(//DEGRADED_MSI_DATA_PERCENTAGE)" "$local_file" 2>/dev/null)
  # degraded_saturation=$(xmllint --xpath "string(//SATURATED_DEFECTIVE_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  # darkness=$(xmllint --xpath "string(//DARK_FEATURES_PERCENTAGE)" "$local_file" 2>/dev/null)

  # Default values
  cloud_coverage=${cloud_coverage:-100}
  no_data=${no_data:-100}
  snow=${snow:-100}
  degraded_msi=${degraded_msi:-100}
  degraded_saturation=${degraded_saturation:-100}
  darkness=${darkness:-100}

  echo "$cloud_coverage $no_data $snow $degraded_msi $degraded_saturation $darkness"
}

nr=0
while read -r metadata_key; do
  read -r cloud_cov no_data_pct snow_pct degraded_msi degraded_saturation darkness <<< "$(get_quality_metrics "$metadata_key" "$nr")"
  nr=$((nr + 1))

  # Apply filters
  awk -v c1="$cloud_cov" 'BEGIN {exit !(c1 < 20)}' || continue
  awk -v nd="$no_data_pct" 'BEGIN {exit !(nd < 5)}' || continue
  awk -v s="$snow_pct" 'BEGIN {exit !(s < 2)}' || continue
  awk -v d="$degraded_msi" 'BEGIN {exit !(d == 0)}' || continue
  awk -v d="$degraded_saturation" 'BEGIN {exit !(d < 0.1)}' || continue
  awk -v d="$darkness" 'BEGIN {exit !(d < 1)}' || continue
  echo "$metadata_key $nr" >> "$candidate_file"
done < "$TMP_DIR/metadata_files.txt"

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

count=0
while read -r metadata_key nr && [ "$count" -lt 3 ]; do
  image_key=$(echo "$metadata_key" | sed 's/metadata.xml//')

  dest="${output}/${input}/${nr}"

  for file in "${files[@]}"; do
    s3_path="https://sentinel-s2-l2a.s3.amazonaws.com/${image_key}${file}"
    local_path="${dest}/$(basename "$file")"
    if [ ! -f "$local_path" ]; then
      wget -nv "$s3_path" -O "$local_path" 
    fi
  done
  # aws s3 cp "s3://sentinel-s2-l2a/$image_key"  --recursive --no-sign-request

  count=$((count + 1))
done < "$candidate_file"

rm -rf "$TMP_DIR"
