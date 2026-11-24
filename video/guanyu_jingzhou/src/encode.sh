#!/bin/bash
# 拼接分段 + 音频，两遍编码到目标码率（保证 < 100MB）
set -e
cd /home/user/work/vid
DUR=$(python3 -c "from timeline import TL; print(TL().total)" 2>/dev/null | tail -1)
VB=$(python3 -c "print(int(min(2600, 93*8*1000/float('$DUR') - 176)))")
echo "dur=$DUR vb=${VB}k"
ffmpeg -y -loglevel error -f concat -safe 0 -i out/list.txt -c copy out/inter.mp4
COMMON="-c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*17/10))k -bufsize $((VB*3))k -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 -g 60 -bf 2 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -x264-params aq-mode=3:aq-strength=0.9:psy-rd=1.0,0.15"
ffmpeg -y -loglevel error -i out/inter.mp4 $COMMON -pass 1 -passlogfile out/p2 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i out/inter.mp4 -i audio.wav $COMMON -pass 2 -passlogfile out/p2 -c:a aac -b:a 160k -ar 48000 -movflags +faststart -shortest "$1"
ls -la "$1"; ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt -of default=nw=1 "$1"
