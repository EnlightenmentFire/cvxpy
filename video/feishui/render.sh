#!/bin/bash
# 分 N 路并行抓帧：./render.sh [起始帧] [结束帧]；已存在的帧会跳过（可断点续跑）
cd "$(dirname "$0")"
FPS=25
TOTAL=$(python3 -c "import json,math;print(math.ceil(json.load(open('src/timeline.json'))['total']*$FPS))")
F0=${1:-0}; F1=${2:-$TOTAL}; NJ=${NJ:-4}
mkdir -p cache/frames cache/logs
STEP=$(( (F1 - F0 + NJ - 1) / NJ ))
for j in $(seq 0 $((NJ-1))); do
  a=$((F0 + j*STEP)); b=$((a + STEP)); [ $b -gt $F1 ] && b=$F1
  node src/shoot.js range $a $b cache/frames > cache/logs/render_$j.log 2>&1 &
done
wait
echo "frames done $F0-$F1 ($(ls cache/frames | wc -l) files)"
