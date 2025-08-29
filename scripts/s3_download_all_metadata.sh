#!/bin/bash

# Download all the metadata for the grid
xargs -a "data/grids/all_kenya.txt" -P 24 -I{} "./scripts/s3_get_metadata.sh" {} "data/s2-images-kenya-all"
# find "/run/media/cynik/Elements/s2-images" -type f -name '*.json' | parallel -j8 --bar ./s3_image_from_metadata.sh {}

echo "All images downloaded!"
exit
final_log="../data/s2-images/combined_$(date +'%Y%m%d_%H%M%S').log"
cat ../data/s2-images/*.tlog > "$final_log"
rm -rf "../data/s2-images/*.tlog"
