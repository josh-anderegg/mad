#!/bin/bash

find outputs -type f -name '*.json' -exec jq -r '
  .best_ceofficients[] | to_entries[] | "\(.key) \(.value)"
' {} + \
| awk '
  function abs(x) { return x < 0 ? -x : x }
  {
    count[$1] += 1
    sum[$1] += $2
    mod[$1] += abs($2)
  }
  END {
    printf "%-15s %10s %15s %20s\n", "Coefficient", "Count", "Average", "Abs Sum"
    for (key in count) {
      printf "%-15s %10d %15.6f %20.6f\n", key, count[key], sum[key]/count[key], mod[key]/count[key]
    }
  }
' | sort -k2,2nr