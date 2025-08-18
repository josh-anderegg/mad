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
            .snow < 3 and
            .cloud_coverage < 20
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata"
)

summer=$(
  jq -r '
    [ .[]
      | select(
          (.sensing_time | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | .[1] + 1) as $month
          | $month >= 6 and $month <= 8 and
            .snow < 3 and
            .cloud_coverage < 20
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata"
)

fall=$(
  jq -r '
    [ .[]
      | select(
          (.sensing_time | sub("\\..*Z$"; "") | strptime("%Y-%m-%dT%H:%M:%S") | .[1] + 1) as $month
          | $month >= 9 and $month <= 11 and
            .snow < 3 and
            .cloud_coverage < 20
        )
    ]
    | sort_by(.cloud_coverage)
    | .[].metadata_key
  ' "$metadata"
)
echo "spring"
echo "$spring"
echo "summer"
echo "$summer"
echo "fall"
echo "$fall"
# if [ -z "$" ] || [ "$best_file" = "null" ]; then
#     echo "No suitable image found for $name" >> "$LOG_FILE"
#     exit 1
# fi

image_key=$(echo "$best_file" | sed 's/metadata.xml//')
$SCRIPT_DIR/s3_download_tci.sh "$TMP_DIR" "$image_key" 2>> "$LOG_FILE"

# nohup needed here as the parent shell ends and the child shell should persist
# WARNING: May cause issues if downloads are significantly fast than the transform
nohup "$SCRIPT_DIR/s3_transform_tci.sh" "$TMP_DIR" "$finished_file" > /dev/null 2>> "$LOG_FILE" &
