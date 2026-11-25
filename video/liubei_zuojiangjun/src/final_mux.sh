#!/bin/bash
# 拼接分段画面 → 两遍 x264（目标码率按 <100MB 计算）→ 混入音轨（aresample=async=1）→ 核对音视频时长差。
# 用法：bash final_mux.sh <输出目录> <成片名>
set -e
WORK=${WORK:-/tmp/claude-0/work}
OUT=$1; NAME=$2
mkdir -p "$OUT"
cd "$WORK/seg"
ls seg_*.mp4 | sort | sed "s/^/file '/;s/$/'/" > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy "$WORK/video_cat.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/video_cat.mp4")
# 总码率预算：96 MB；音频 128k
VBR=$(python3 -c "print(int((96*8*1024*1024/$DUR - 128000)/1000))")
VBR=$(( VBR > 1400 ? 1400 : VBR ))
echo "duration $DUR s, video bitrate ${VBR}k"
cd "$WORK"
ffmpeg -y -loglevel error -i video_cat.mp4 -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k \
  -pix_fmt yuv420p -r 25 -g 50 -pass 1 -passlogfile "$WORK/x264" -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i video_cat.mp4 -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k \
  -pix_fmt yuv420p -r 25 -g 50 -pass 2 -passlogfile "$WORK/x264" -an video_2p.mp4
for v in "mix:${NAME}" "mix_nomusic:${NAME}_无配乐版"; do
  src=${v%%:*}; dst=${v#*:}
  ffmpeg -y -loglevel error -i video_2p.mp4 -i "audio/${src}.wav" -map 0:v -map 1:a -c:v copy \
    -af aresample=async=1 -c:a aac -b:a 128k -ar 48000 -shortest -movflags +faststart "$OUT/${dst}.mp4"
  VD=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT/${dst}.mp4")
  AD=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$OUT/${dst}.mp4")
  SZ=$(stat -c %s "$OUT/${dst}.mp4")
  echo "${dst}.mp4  video ${VD}s  audio ${AD}s  diff $(python3 -c "print(round(abs($VD-$AD),3))")s  size $(python3 -c "print(round($SZ/1e6,1))") MB"
done
