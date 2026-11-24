#!/bin/bash
# 帧序列 + 混音 → 1080x1920 30fps H.264 mp4（两遍编码，控制在 100MB 以内）
cd "$(dirname "$0")"
BR=${BR:-1750k}; OUT=${1:-out/yubi_1080x1920.mp4}
VF="scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p"
COMMON="-framerate 30 -i cache/frames/f%06d.jpg"
ffmpeg -y -loglevel error $COMMON -vf "$VF" -c:v libx264 -preset slow -b:v $BR -pass 1 -passlogfile cache/x264 -an -f mp4 /dev/null && \
ffmpeg -y -loglevel error $COMMON -i audio/mix.wav -vf "$VF" -c:v libx264 -preset slow -b:v $BR -maxrate 3500k -bufsize 7000k -pass 2 -passlogfile cache/x264 \
  -profile:v high -level 4.2 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 160k -ar 48000 -shortest -movflags +faststart "$OUT" && ls -la "$OUT" && ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$OUT"
