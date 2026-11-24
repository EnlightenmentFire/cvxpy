#!/bin/bash
# 全片渲染：3 路并行逐帧截图 -> 拼接 -> 加颗粒、压码率、混音轨 -> out/宝钢与君津.mp4
set -e
cd "$(dirname "$0")"
WORK=${WORK:-/tmp/baosteel_render}; mkdir -p "$WORK" out
N=$(python3 -c "import json;print(round(json.load(open('render/timeline.json'))['dur']*30))")
J=${J:-3}; STEP=$(( (N + J - 1) / J )); pids=()
for i in $(seq 0 $((J-1))); do
  a=$((i*STEP)); b=$(( (i+1)*STEP )); [ $b -gt $N ] && b=$N
  node render/render.js frames $a $b "$WORK/seg_$i.mp4" 14 > "$WORK/seg_$i.log" 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
: > "$WORK/list.txt"; for i in $(seq 0 $((J-1))); do echo "file '$WORK/seg_$i.mp4'" >> "$WORK/list.txt"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/raw.mp4"
ffmpeg -y -loglevel error -i "$WORK/raw.mp4" -i audio/out/mix.wav \
  -vf "noise=alls=4:allf=t,format=yuv420p" -c:v libx264 -preset slow -profile:v high -level 4.2 -crf ${CRF:-21} -maxrate 2400k -bufsize 4800k -r 30 \
  -c:a aac -b:a 160k -ar 48000 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -movflags +faststart "out/宝钢与君津_改革开放01.mp4"
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,nb_frames -of default=nw=1 "out/宝钢与君津_改革开放01.mp4"
