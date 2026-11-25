#!/bin/bash
# 拼接分段 + 音频：恒定 25fps，aresample=async=1，两遍编码控制在 100MB 以内。用法：encode.sh 音频.wav 输出.mp4
set -e
cd /tmp/claude-0/work/vid
AUD=$1; OUTF=$2
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/inter.mp4 2>/dev/null || echo 0)
if [ ! -f out/inter.mp4 ]; then ffmpeg -y -loglevel error -f concat -safe 0 -i out/list.txt -c copy out/inter.mp4; DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/inter.mp4); fi
VB=$(python3 -c "print(int(min(4000, 92*8*1000/float('$DUR') - 140)))")
echo "dur=$DUR vb=${VB}k"
COMMON="-c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*2))k -bufsize $((VB*4))k -profile:v high -level 4.1 -pix_fmt yuv420p -r 25 -fps_mode cfr -g 50 -bf 2 -colorspace bt709 -color_primaries bt709 -color_trc bt709"
if [ ! -f out/pass.log-0.log ] || [ ! -f out/pass_done ]; then
  ffmpeg -y -loglevel error -i out/inter.mp4 $COMMON -pass 1 -passlogfile out/pass.log -an -f mp4 /dev/null && touch out/pass_done
fi
ffmpeg -y -loglevel error -i out/inter.mp4 -i "$AUD" -map 0:v -map 1:a $COMMON -pass 2 -passlogfile out/pass.log -af aresample=async=1 -c:a aac -b:a 128k -ar 48000 -movflags +faststart -t $DUR "$OUTF"
ls -la "$OUTF"; ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_type,duration,r_frame_rate,width,height -of compact "$OUTF"
