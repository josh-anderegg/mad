#!/bin/sh
input=$1
fst=${input:0:2}
mid=${input:2:1}
lst=${input:3:2}
S3_PATH="s3://sentinel-s2-l2a/tiles/$fst/$mid/$lst/2019"
TMP_DIR=$(mktemp -d)
candidate_file="$TMP_DIR/candidates.txt"

# List all metadata.xml files (full S3 keys)
aws s3 ls "$S3_PATH" --recursive --no-sign-request | grep metadata.xml | awk '{print $4}' > "$TMP_DIR/metadata_files.txt"

get_quality_metrics() {
  local metadata_s3_key=$1
  local local_file="$TMP_DIR/$(basename "$metadata_s3_key")"

  curl -s "https://sentinel-s2-l2a.s3.amazonaws.com/$metadata_s3_key" -o "$local_file"

  cloud_coverage=$(xmllint --xpath "string(//CLOUDY_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  no_data=$(xmllint --xpath "string(//NODATA_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  snow=$(xmllint --xpath "string(//SNOW_ICE_PERCENTAGE)" "$local_file" 2>/dev/null)
  degraded_msi=$(xmllint --xpath "string(//DEGRADED_MSI_DATA_PERCENTAGE)" "$local_file" 2>/dev/null)
  degraded_saturation=$(xmllint --xpath "string(//SATURATED_DEFECTIVE_PIXEL_PERCENTAGE)" "$local_file" 2>/dev/null)
  darkness=$(xmllint --xpath "string(//DARK_FEATURES_PERCENTAGE)" "$local_file" 2>/dev/null)

  # Default values
  cloud_coverage=${cloud_coverage:-100}
  no_data=${no_data:-100}
  snow=${snow:-100}
  degraded_msi=${degraded_msi:-100}
  degraded_saturation=${degraded_saturation:-100}
  darkness=${darkness:-100}

  rm "$local_file"
  echo "$cloud_coverage $no_data $snow $degraded_msi $degraded_saturation $darkness"
}

while read -r metadata_key; do
  read -r cloud_cov no_data_pct snow_pct degraded_msi degraded_saturation darkness <<< "$(get_quality_metrics "$metadata_key")"

  # Apply filters
  awk -v c1="$cloud_cov" 'BEGIN {exit !(c1 < 20)}' || continue
  awk -v nd="$no_data_pct" 'BEGIN {exit !(nd < 5)}' || continue
  awk -v s="$snow_pct" 'BEGIN {exit !(s < 2)}' || continue
  awk -v d="$degraded_msi" 'BEGIN {exit !(d == 0)}' || continue
  awk -v d="$degraded_saturation" 'BEGIN {exit !(d < 0.1)}' || continue
  awk -v d="$darkness" 'BEGIN {exit !(d < 1)}' || continue
  echo "$metadata_key" >> "$candidate_file"
done < "$TMP_DIR/metadata_files.txt"
count=0
while read -r metadata_key && [ "$count" -lt 5 ]; do
  image_key=$(echo "$metadata_key" | sed 's/metadata.xml//')

  aws s3 cp "s3://sentinel-s2-l2a/$image_key" ./"$input_$count" --recursive --no-sign-request

  count=$((count + 1))
done < "$candidate_file"

rm -r "$TMP_DIR"
