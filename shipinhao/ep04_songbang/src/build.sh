#!/bin/bash
# 一键构建：旁白 → 时间轴 → 混音 → 逐帧渲染 → 编码
# 用法: bash src/build.sh [voice=zm_011] [speed=1.08] [out=out/松绑_五十五个厂长的一封信.mp4]
#       FROM=186 DUR=29 bash src/build.sh ...   只做一段预览（秒）
set -e
cd "$(dirname "$0")/.."
VOICE=${1:-zm_011}; SPEED=${2:-1.08}; OUT=${3:-out/松绑_五十五个厂长的一封信.mp4}
PY=${PY:-/opt/ttsenv/bin/python}; FR=${FR:-/tmp/songbang_frames}; FPS=30; J=${J:-4}
if [ -z "$SKIP_TTS" ]; then $PY src/tts.py --voice $VOICE --speed $SPEED --out audio/narration | tail -1; fi
python3 src/mk_timeline.py
if [ -z "$SKIP_MIX" ]; then $PY src/audio_mix.py | tail -1; fi
TOTAL=$(python3 -c "import json;print(json.load(open('audio/narration.json'))['total'])")
FROM=${FROM:-0}; DUR=${DUR:-$TOTAL}
S=$(python3 -c "print(int($FROM*$FPS))"); E=$(python3 -c "import math;print(min(math.ceil($TOTAL*$FPS), int(($FROM+$DUR)*$FPS)))")
rm -rf "$FR"; mkdir -p "$FR" out
STEP=$(( (E-S+J-1)/J ))
for i in $(seq 0 $((J-1))); do a=$((S+i*STEP)); b=$((a+STEP)); [ $b -gt $E ] && b=$E; node src/render.cjs "$FR" $a $b > /tmp/render_$i.log 2>&1 & done; wait
echo "frames: $(ls "$FR" | wc -l) / $((E-S))"
# 码率：整片不超过 95MB
VB=$(python3 -c "d=($E-$S)/$FPS; print(int(min(2600, 95*8*1024/max(d,60) - 140)))")
LUFS=$(ffmpeg -hide_banner -ss $FROM -t $DUR -i audio/mix.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
GAIN=$(python3 -c "print(round(min(8, -16.0 - ($LUFS)),2))")
VF="vignette=angle=PI/5.2:eval=init,noise=alls=6:allf=t,format=yuv420p"
X="-c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*18/10))k -bufsize $((VB*36/10))k -profile:v high -g 60 -colorspace bt709 -color_primaries bt709 -color_trc bt709"
ffmpeg -v error -y -framerate $FPS -start_number $S -i "$FR/%06d.jpg" -vf "$VF" $X -pass 1 -passlogfile /tmp/sb_pass -an -f mp4 /dev/null
ffmpeg -v error -y -framerate $FPS -start_number $S -i "$FR/%06d.jpg" -ss $FROM -t $DUR -i audio/mix.wav -vf "$VF" $X -pass 2 -passlogfile /tmp/sb_pass \
  -af "volume=${GAIN}dB,alimiter=limit=0.89:attack=5:release=80" -c:a aac -b:a 128k -ar 48000 -movflags +faststart -shortest "$OUT"
echo "video ${VB}k  gain ${GAIN}dB  →  $OUT"; ls -la "$OUT" | awk '{printf "%.1f MB\n", $5/1048576}'
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height,r_frame_rate -of compact "$OUT"
