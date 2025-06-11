#!/bin/bash

find outputs -type f -name '*.json' -exec jq -r '
  .best_ceofficients[] | to_entries[] | "\(.key) \(.value)"
' {} + \
| awk '
  {
    count[$1] += 1
    sum[$1] += $2
  }
  END {
    printf "%-10s %10s %15s\n", "Coefficient", "Count", "Average"
    for (key in count) {
      printf "%-10s %10d %15.6f\n", key, count[key], sum[key]/count[key]
    }
  }
' | sort -k2,2nr