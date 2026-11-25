#!/bin/bash
# 帧序列 + 混音 → 1080x1920 25fps H.264 + AAC 128k（两遍编码，<100MB）。恒定帧率；音频 aresample=async=1。
# 用法：./encode.sh <mix.wav> <out.mp4>
cd "$(dirname "$0")"
MIX=$1; OUT=$2; BR=${BR:-780k}
VF="scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p"
IN="-framerate 25 -start_number 0 -i cache/frames/f%06d.jpg"
if [ ! -f cache/x264-0.log ] || [ "${REPASS:-0}" = 1 ]; then
  ffmpeg -y -loglevel error $IN -vf "$VF" -r 25 -c:v libx264 -preset ${PRESET:-medium} -b:v $BR -pass 1 -passlogfile cache/x264 -an -f mp4 /dev/null || exit 1
fi
ffmpeg -y -loglevel error $IN -i "$MIX" -map 0:v -map 1:a -vf "$VF" -r 25 -fps_mode cfr \
  -c:v libx264 -preset ${PRESET:-medium} -b:v $BR -maxrate 1600k -bufsize 3200k -pass 2 -passlogfile cache/x264 \
  -profile:v high -level 4.1 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -af "aresample=async=1:first_pts=0" -c:a aac -b:a 128k -ar 48000 -ac 2 -shortest -movflags +faststart "$OUT" || exit 1
ls -la "$OUT"
ffprobe -v error -show_entries stream=codec_type,duration,r_frame_rate,nb_frames:format=duration,size -of compact "$OUT"
