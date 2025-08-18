#!/bin/bash

mkdir -p "../data/s2-images"
# Download all the metadata for the grid
# xargs -a "tiles.txt" -P 12 -I{} "./s3_get_metadata.sh" {} "/run/media/cynik/Elements/s2-images"
# find "/run/media/cynik/Elements/s2-images" -type f -name '*.json' | parallel -j 8 --compress --bar --group ./s3_image_from_metadata.sh {}
find "../data/s2-images/" -type f -name '*.json' \
  | xargs -I {} sh -c './s3_tci_from_metadata.sh "{}"'
echo "All images downloaded!"
final_log="../data/s2-images/combined_$(date +'%Y%m%d_%H%M%S').log"
cat ../data/s2-images/*.tlog > "$final_log"
rm -rf "../data/s2-images/*.tlog"
