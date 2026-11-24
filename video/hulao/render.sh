#!/bin/bash
# 分 4 路并行抓帧：./render.sh [起始帧] [结束帧]
cd "$(dirname "$0")"
TOTAL=$(python3 -c "import json;print(int(json.load(open('src/timeline.json'))['total']*30)+1)")
F0=${1:-0}; F1=${2:-$TOTAL}; NJ=${NJ:-4}
mkdir -p cache/frames
STEP=$(( (F1 - F0 + NJ - 1) / NJ ))
for j in $(seq 0 $((NJ-1))); do
  a=$((F0 + j*STEP)); b=$((a + STEP)); [ $b -gt $F1 ] && b=$F1
  node src/shoot.js range $a $b cache/frames > cache/render_$j.log 2>&1 &
done
wait
echo "frames done $F0-$F1"
