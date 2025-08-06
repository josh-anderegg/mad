#!/bin/bash
for i in $(seq -f "%04g" 0 80); do
  img=~/Documents/mad/package/output_img/tile_$i.jpg
  txt=~/Documents/mad/package/output_img/tile_$i.txt
  echo "$img"
  echo "$txt"
  python scripts/visualize_label.py "$img" "$txt"
done
