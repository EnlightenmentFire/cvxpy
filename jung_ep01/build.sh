#!/usr/bin/env bash
# 一键重建：旁白 → 底乐混音 → 逐帧渲染 → 成片压制。需要 ffmpeg、node+playwright、python(kokoro, misaki[zh], soundfile, scipy)。
# 字体放在 assets/fonts/（Noto Serif SC、Noto Sans SC 的 SubsetOTF 各字重，EB Garamond 可变字体，均 OFL）。
set -euo pipefail
cd "$(dirname "$0")"
VOICE=${VOICE:-zf_006}; SPEED=${SPEED:-1.0}
python tts.py --voice "$VOICE" --speed "$SPEED"
python music.py
node render.js video 4
# 成片：轻微胶片颗粒（顺带抹掉深色渐变的色带），两遍编码把体积压在 100MB 以内
BR=${BR:-1900k}
VF="noise=c0s=4:c0f=t+u,format=yuv420p"
ffmpeg -y -loglevel error -i build/video_silent.mp4 -vf "$VF" -c:v libx264 -preset slow -b:v $BR -maxrate 3500k -bufsize 7000k -profile:v high -level 4.2 -r 30 -g 60 -pass 1 -passlogfile build/x264pass -an -f null /dev/null
ffmpeg -y -loglevel error -i build/video_silent.mp4 -i build/mix.wav -vf "$VF" -c:v libx264 -preset slow -b:v $BR -maxrate 3500k -bufsize 7000k -pass 2 -passlogfile build/x264pass \
  -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 -g 60 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest "out/荣格精读01_你说的内向不是荣格说的内向.mp4"
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "out/荣格精读01_你说的内向不是荣格说的内向.mp4"
