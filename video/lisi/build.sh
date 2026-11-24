#!/usr/bin/env bash
# 一键重建：旁白 → 时间线 → 配乐混音 → 逐帧渲染 → 合成 mp4
# 依赖：python(kokoro, misaki[zh], torch-cpu, soundfile, scipy)、node + playwright(chromium)、ffmpeg、npm i
set -euo pipefail
cd "$(dirname "$0")"
VOICE="${VOICE:-zm_029}"; WORKERS="${WORKERS:-4}"; OUT="${OUT:-out/lisi_v1.mp4}"
[ "${SKIP_TTS:-0}" = 1 ] || python src/tts.py --voice "$VOICE"
python src/build_timeline.py "$VOICE"
python src/music.py
TOTAL=$(python -c "import json;print(json.load(open('build/timeline.json'))['total'])")
FRAMES=$(python -c "print(int(round($TOTAL*30)))")
rm -rf build/chunks && mkdir -p build/chunks out
PER=$(( (FRAMES + WORKERS - 1) / WORKERS )); : > build/chunks/list.txt
for i in $(seq 0 $((WORKERS-1))); do
  A=$((i*PER)); B=$(( (i+1)*PER )); [ $B -gt $FRAMES ] && B=$FRAMES
  node src/render.cjs $A $B build/chunks/c$i.mp4 & echo "file 'c$i.mp4'" >> build/chunks/list.txt
done; wait
# 轻颗粒 + 两遍编码，控制在 100MB 内（视频约 1.75 Mbps + 音频 192k）
VB="${VB:-$(python -c "print(int(min(1750, 94e6*8/$TOTAL/1000 - 170)))")k}"; echo "video bitrate $VB"; VF="noise=c0s=6:c0f=t+u,format=yuv420p"
ffmpeg -y -loglevel error -f concat -safe 0 -i build/chunks/list.txt -vf "$VF" -c:v libx264 -preset slow -b:v $VB -pass 1 -passlogfile build/x264 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -f concat -safe 0 -i build/chunks/list.txt -i build/mix.wav -vf "$VF" -c:v libx264 -preset slow -b:v $VB -maxrate 4M -bufsize 8M -pass 2 -passlogfile build/x264 \
  -profile:v high -level 4.2 -r 30 -c:a aac -b:a 160k -ar 48000 -movflags +faststart -shortest "$OUT"
ls -la "$OUT"; ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$OUT"
