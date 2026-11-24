#!/bin/bash
# build/frames + build/mix.wav -> out/黄仁勋01_先认错再活下来.mp4
set -e
cd "$(dirname "$0")/../build"
mkdir -p ../out
ffmpeg -y -loglevel error -framerate 30 -i frames/%06d.jpg -i mix.wav \
  -vf "noise=alls=4:allf=t,format=yuv420p" -c:v libx264 -preset slow -crf 19 -maxrate 2200k -bufsize 4400k -r 30 \
  -c:a aac -b:a 160k -af "loudnorm=I=-16:TP=-1.5:LRA=11" -movflags +faststart -shortest "../out/huang01.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 ../out/huang01.mp4
