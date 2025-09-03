#!/bin/sh
name=$1
working_dir=$2
shift 2

TMP_DIR=$(mktemp -d)
LOG_FILE="${working_dir}/${name}_downloading.tlog"
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[$name]:Image Download" > "$LOG_FILE"

finished_file="${working_dir}/${name}.tif"

if jq -e 'length == 0' "${working_dir}${name}.json" > /dev/null; then
    echo "Skipping $name — metadata file is empty" >> "$LOG_FILE"
    exit 1
fi

best_file=$(
  jq -r '
    [ .[]
      | select(
          .cloud_coverage < 20 and
          .snow < 20 and
          .no_data < 10
        )
    ]
    | sort_by(.cloud_coverage + .snow)
    | .[0].metadata_key
  ' "${working_dir}/${name}.json"
)

if [ -z "$best_file" ] || [ "$best_file" = "null" ]; then
    echo "No suitable image found for $name" >> "$LOG_FILE"
    exit 1
fi

image_key=$(echo "$best_file" | sed 's/metadata.xml//')
$PACKAGE_DIR/s3_bands_download.sh "$TMP_DIR" "$image_key" $@ 2>> "$LOG_FILE"

# nohup needed here as the parent shell ends and the child shell should persist
# WARNING: May cause issues if downloads are significantly fast than the transform
# nohup disowns the process essentially and let's it run independently from the parent shell.
# As a consequence this process is not stopped automatically! BEWARE!!
nohup "$PACKAGE_DIR/s3_bands_to_image.sh" "$TMP_DIR" "$finished_file" $@ > /dev/null 2>> "$LOG_FILE" &
