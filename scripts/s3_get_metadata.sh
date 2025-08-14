#!/bin/sh
input=$1
output=$2
mkdir -p "${output}"

# Possible early return in case we already have the data downloaded for a tile
finished_file="${output}/${input}_sources.json"

LOG_FILE="${output}/${input}.tlog"
echo "[$input]" > "$LOG_FILE"
if [ -f "$finished_file" ] && [ $(stat -c%s "$finished_file") -gt 1024 ]; then
    echo "Metadata already collected for this file." >> "$LOG_FILE"
    exit 0
fi

fst=$((10#${input:0:2}))
mid=${input:2:1}
lst=${input:3:2}
S3_PATH="s3://sentinel-s2-l2a/tiles/$fst/$mid/$lst/2019"
TMP_DIR=$(mktemp -d "${output}/tmp.XXXXXX")

trap 'rm -rf "$TMP_DIR"' EXIT

# List all metadata.xml files (full S3 keys)
aws_ls=$(aws s3 ls "$S3_PATH" --recursive --no-sign-request 2>> "$LOG_FILE")
echo "$aws_ls" | grep metadata.xml | awk '{print $4}' > "$TMP_DIR/metadata_files.txt"

if [ ! -s "$TMP_DIR/metadata_files.txt" ]; then
    echo "No metadata.xml returned from aws!" >> "$LOG_FILE"
    exit 1
fi

nr=0
json_array="["
while read -r metadata_key; do
    local_file="$TMP_DIR/metadata_${nr}.xml"
    if [ ! -f "$local_file" ]; then
        wget -nv "https://sentinel-s2-l2a.s3.amazonaws.com/$metadata_key" -O "$local_file"
    fi

    read cloud_coverage no_data snow degraded_msi degraded_saturation darkness vegetation not_vegetated water unclassified \
        medium_clouds high_clouds thin_cirrus cloud_shadow sensing_time <<< $(
        xmllint --xpath \
            "concat(
                string(//CLOUDY_PIXEL_PERCENTAGE), ' ',
                string(//NODATA_PIXEL_PERCENTAGE), ' ',
                string(//SNOW_ICE_PERCENTAGE), ' ',
                string(//DEGRADED_MSI_DATA_PERCENTAGE), ' ',
                string(//SATURATED_DEFECTIVE_PIXEL_PERCENTAGE), ' ',
                string(//DARK_FEATURES_PERCENTAGE), ' ',
                string(//VEGETATION_PERCENTAGE), ' ',
                string(//NOT_VEGETATED_PERCENTAGE), ' ',
                string(//WATER_PERCENTAGE), ' ',
                string(//UNCLASSIFIED_PERCENTAGE), ' ',
                string(//MEDIUM_PROBA_CLOUDS_PERCENTAGE), ' ',
                string(//HIGH_PROBA_CLOUDS_PERCENTAGE), ' ',
                string(//THIN_CIRRUS_PERCENTAGE), ' ',
                string(//CLOUD_SHADOW_PERCENTAGE), ' ',
                string(//SENSING_TIME)
        )" "$local_file" 2>> "$LOG_FILE"
    )

    # Default fallback values
    cloud_coverage=${cloud_coverage:-100}
    no_data=${no_data:-100}
    snow=${snow:-100}
    degraded_msi=${degraded_msi:-100}
    degraded_saturation=${degraded_saturation:-100}
    darkness=${darkness:-100}
    vegetation=${vegetation:-100}
    not_vegetated=${not_vegetated:-100}
    water=${water:-100}
    unclassified=${unclassified:-100}
    medium_clouds=${medium_clouds:-100}
    high_clouds=${high_clouds:-100}
    thin_cirrus=${thin_cirrus:-100}
    cloud_shadow=${cloud_shadow:-100}
    sensing_time=${sensing_time:-"unknown"}

    # Append object to JSON array
    json_array+=$(jq -nc \
            --arg key "$metadata_key" \
            --argjson cloud "$cloud_coverage" \
            --argjson nodata "$no_data" \
            --argjson snow "$snow" \
            --argjson degraded "$degraded_msi" \
            --argjson saturated "$degraded_saturation" \
            --argjson dark "$darkness" \
            --argjson vegetation "$vegetation" \
            --argjson not_vegetated "$not_vegetated" \
            --argjson water "$water" \
            --argjson unclassified "$unclassified" \
            --argjson medium_clouds "$medium_clouds" \
            --argjson high_clouds "$high_clouds" \
            --argjson cirrus "$thin_cirrus" \
            --argjson shadow "$cloud_shadow" \
            --arg time "$sensing_time" \
            '{
            metadata_key: $key,
            cloud_coverage: $cloud,
            no_data: $nodata,
            snow: $snow,
            degraded_msi: $degraded,
            saturated_defective: $saturated,
            dark_features: $dark,
            vegetation: $vegetation,
            not_vegetated: $not_vegetated,
            water: $water,
            unclassified: $unclassified,
            medium_proba_clouds: $medium_clouds,
            high_proba_clouds: $high_clouds,
            thin_cirrus: $cirrus,
            cloud_shadow: $shadow,
            sensing_time: $time
    }')

    nr=$((nr + 1))
    json_array+=","
done < "$TMP_DIR/metadata_files.txt"

# Remove trailing comma and close JSON array
json_array="${json_array%,}]"
echo "$json_array" > "$finished_file"
