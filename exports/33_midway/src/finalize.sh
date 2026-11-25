#!/bin/bash
# Mux rendered video with final mixes; 2-pass x264 to stay < 100 MB; constant 25 fps; aresample async.
set -e
W=/tmp/claude-0/work; OUT=$W/out; mkdir -p $OUT
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/video_noaudio.mp4)
# video bitrate budget: 96 MB total minus 128k audio
VB=$(python3 -c "d=$DUR; print(int((96e6*8/d - 130e3)/1000))")
echo "dur=$DUR vbit=${VB}k"
cd $W
ffmpeg -v error -y -i video_noaudio.mp4 -c:v libx264 -preset slow -b:v ${VB}k -pass 1 -passlogfile $W/x264 -r 25 -an -f mp4 /dev/null
for v in music nomusic; do
  ffmpeg -v error -y -i video_noaudio.mp4 -i audio/mix_$v.wav -map 0:v -map 1:a \
    -c:v libx264 -preset slow -b:v ${VB}k -pass 2 -passlogfile $W/x264 -r 25 -vsync cfr -pix_fmt yuv420p -profile:v high \
    -af "aresample=async=1" -c:a aac -b:a 128k -ar 48000 -ac 2 -shortest -movflags +faststart $OUT/final_$v.mp4
done
ls -la $OUT
