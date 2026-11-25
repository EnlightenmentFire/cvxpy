#!/bin/bash
# 用法: encode.sh frames_dir mix.wav out.mp4
set -e
ffmpeg -y -loglevel error -framerate 30 -i "$1/f%05d.png" -i "$2" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -tune film -profile:v high -level 4.2 -g 60 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart -r 30 "$3"
