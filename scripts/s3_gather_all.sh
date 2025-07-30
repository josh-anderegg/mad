#!/bin/bash

INPUT_FILE="../data/grids/mgrs.txt"
SCRIPT_TO_RUN="./s3_gather.sh"
OUTPUT_DIR="../data/s3-images"

xargs -a "$INPUT_FILE" -n 1 -I{} "$SCRIPT_TO_RUN" {} "$OUTPUT_DIR"
echo "All tasks completed."
