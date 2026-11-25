#!/usr/bin/env bash
# 并行渲染 4 段并校验帧数（恒定 25fps）
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; WORK="${1:?work dir}"; mkdir -p "$WORK"; cd "$HERE"
N=4
for k in $(seq 0 $((N-1))); do python3 render2.py chunk $k $N "$WORK/chunk_$k.mp4" > "$WORK/chunk_$k.log" 2>&1 & PIDS[$k]=$!; done
for k in $(seq 0 $((N-1))); do wait ${PIDS[$k]} || { echo "chunk $k FAILED"; tail -5 "$WORK/chunk_$k.log"; exit 1; }; done
NF=$(python3 render2.py nframes 2>/dev/null | tail -1)
GOT=0; : > "$WORK/list.txt"
for k in $(seq 0 $((N-1))); do
  n=$(ffprobe -v error -count_packets -select_streams v -show_entries stream=nb_read_packets -of csv=p=0 "$WORK/chunk_$k.mp4"); GOT=$((GOT+n))
  echo "file '$WORK/chunk_$k.mp4'" >> "$WORK/list.txt"
done
echo "frames $GOT expected $NF"; [ "$GOT" -eq "$NF" ] || { echo FRAME_MISMATCH; exit 1; }
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/video_hq.mp4"
echo RENDER_OK
