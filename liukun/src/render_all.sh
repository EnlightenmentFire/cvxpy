#!/bin/bash
# 全片渲染：4 路并行出帧 -> 拼接 -> 两遍 x264 + AAC，目标 < 100MB
set -e
cd "$(dirname "$0")"
TOTAL=$(python3 -c "import json;print(json.load(open('../audio/timeline.json'))['total'])")
N=4; mkdir -p ../out/parts
for i in $(seq 0 $((N-1))); do
  A=$(python3 -c "import math;print(math.floor($TOTAL*30*$i/$N)/30)"); B=$(python3 -c "import math;print(math.floor($TOTAL*30*($i+1)/$N)/30)")
  node render.cjs range $A $B ../out/parts/p$i.mp4 > ../out/parts/p$i.log 2>&1 &
done
wait
for i in $(seq 0 $((N-1))); do echo "file 'p$i.mp4'"; done > ../out/parts/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i ../out/parts/list.txt -c copy ../out/video_raw.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ../out/video_raw.mp4)
VBR=$(python3 -c "print(int(min(2600, (92*8192/$DUR) - 140)))")
echo "duration $DUR  video bitrate ${VBR}k"
X="-c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pix_fmt yuv420p -profile:v high -level 4.2 -r 30 -g 60 -x264-params aq-mode=3:aq-strength=1.1:deblock=-1,-1 -color_primaries bt709 -color_trc bt709 -colorspace bt709"
ffmpeg -y -loglevel error -i ../out/video_raw.mp4 $X -pass 1 -passlogfile ../out/parts/x264 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i ../out/video_raw.mp4 -i ../out/audio_mix.wav $X -pass 2 -passlogfile ../out/parts/x264 -af "loudnorm=I=-16:TP=-2:LRA=11,alimiter=limit=0.8:level=false" -ar 48000 -c:a aac -b:a 128k -movflags +faststart -shortest "../out/刘琨-一座没有后方的孤城.mp4"
ls -la ../out/*.mp4
