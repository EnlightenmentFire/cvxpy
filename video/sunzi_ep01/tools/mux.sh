#!/bin/sh
# 合成成片：无声画面 + 混好的音轨 → 响度归一（-16 LUFS）→ H.264/AAC mp4（视频号：1080x1920、30fps、<100MB）
set -e
cd "$(dirname "$0")/.."
V=${1:-build/video.mp4}; A=${2:-build/audio.wav}; O=${3:-out/sunzi_ep01_draft.mp4}
ffmpeg -y -loglevel error -i "$V" -i "$A" -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k -shortest -movflags +faststart "$O"
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$O"
