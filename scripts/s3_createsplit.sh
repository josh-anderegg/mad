#!/bin/bash

DATA_DIR="$1"
TRAIN_RATIO=0.7
VAL_RATIO=0.15
TEST_RATIO=0.15

TOTAL=$(echo "$TRAIN_RATIO + $VAL_RATIO + $TEST_RATIO" | bc)
TOTAL_INT=$(echo "$TOTAL == 1.0" | bc)

if [ "$TOTAL_INT" -ne 1 ]; then
  echo "Ratios must sum to 1.0"
  exit 1
fi

# Get shuffled list of .json files
files=($(find "$DATA_DIR" -maxdepth 1 -type f -name '*.json' | shuf))
total_files=${#files[@]}

train_count=$(printf "%.0f" "$(echo "$total_files * $TRAIN_RATIO" | bc)")
val_count=$(printf "%.0f" "$(echo "$total_files * $VAL_RATIO" | bc)")
test_count=$((total_files - train_count - val_count))

# Split files
train_files=("${files[@]:0:train_count}")
val_files=("${files[@]:train_count:val_count}")
test_files=("${files[@]:train_count+val_count}")

# Write to output file
for f in "${train_files[@]}"; do
  filename="$(basename "$f")"
  echo "${filename%.json}_tci.jp2" >> "$DATA_DIR/train.txt"
done

for f in "${val_files[@]}"; do
  filename="$(basename "$f")"
  echo "${filename%.json}_tci.jp2" >> "$DATA_DIR/val.txt"
done

for f in "${test_files[@]}"; do
  filename="$(basename "$f")"
  echo "${filename%.json}_tci.jp2" >> "$DATA_DIR/test.txt"
done

echo "Split created"
