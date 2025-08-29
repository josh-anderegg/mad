#!/bin/sh
metadata=$1
name="${metadata%.json}"
working_dir=$(dirname "$metadata")

TMP_DIR=$(mktemp -d)
LOG_FILE="${name}.tlog"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[$input]:Image Download" > "$LOG_FILE"

# # Possible early return in case we already have the data downloaded for a tile
finished_file="${name}_tci.jp2"
if [ -f "$finished_file" ]; then
    echo "Skipping $name — as .tif already exists" >> "$LOG_FILE"
    exit 0
fi

if jq -e 'length == 0' "$metadata" > /dev/null; then
    echo "Skipping $name — metadata file is empty" >> "$LOG_FILE"
    exit 1
fi

best_file=$(
  jq -r '
    [ .[]
      | select(
          .no_data < 10
        )
    ]
    | sort_by(.cloud_coverage)
    | .[0].metadata_key
  ' "$metadata"
)

if [ -z "$best_file" ] || [ "$best_file" = "null" ]; then
    echo "No suitable image found for $name" >> "$LOG_FILE"
    exit 1
fi

image_key=$(echo "$best_file" | sed 's/metadata.xml//')
$SCRIPT_DIR/s3_download_tci.sh "." "$image_key" "$name.jp2" 2>> "$LOG_FILE"

# nohup needed here as the parent shell ends and the child shell should persist
# WARNING: May cause issues if downloads are significantly fast than the transform
# nohup "$SCRIPT_DIR/s3_transform_tci.sh" "$TMP_DIR" "$finished_file" > /dev/null 2>> "$LOG_FILE" &
