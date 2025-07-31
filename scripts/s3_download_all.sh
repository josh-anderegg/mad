#!/bin/bash

mkdir -p "../data/s2-images"
# Download all the metadata for the grid
xargs -a "../data/grids/tiles.txt" -P 12 -I{} "./s3_get_metadata.sh" {} "../data/s2-images"
cd "../data/s2-images"
find . -maxdepth 1 -name '*.json' -exec ./s3_image_from_metadata.sh {} \;

echo "All images downloaded!"
