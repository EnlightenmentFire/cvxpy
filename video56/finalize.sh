#!/usr/bin/env bash
# 渲染 + 合成成片（有配乐版、无配乐版）+ 同步核对。
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${WORK:-/tmp/claude-0/work}
N=${N:-4}
PY=${PY:-/tmp/claude-0/work/venv/bin/python}
cd "$HERE"

if [ "${SKIP_RENDER:-0}" != 1 ]; then
  for i in $(seq 0 $((N-1))); do
    $PY render.py seg $i $N > "$WORK/render_$i.log" 2>&1 &
  done
  wait
fi
: > "$WORK/segs.txt"
for i in $(seq 0 $((N-1))); do printf "file '%s/seg_%02d.mp4'\n" "$WORK" $i >> "$WORK/segs.txt"; done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/segs.txt" -c copy "$WORK/video_nosound.mp4"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/mix_music.wav")
# 目标 < 100 MB：总码率按 95 MB 算
VBR=$($PY -c "print(int(95*8*1024*1024/float('$DUR')/1000 - 140))")
echo "duration $DUR s, video bitrate ${VBR}k"

enc() {  # $1 audio wav, $2 out mp4
  cd "$WORK"
  ffmpeg -v error -y -i video_nosound.mp4 -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*3))k -bufsize $((VBR*4))k \
    -pass 1 -passlogfile "$WORK/x264" -r 25 -fps_mode cfr -an -f null /dev/null
  ffmpeg -v error -y -i video_nosound.mp4 -i "$1" -map 0:v:0 -map 1:a:0 \
    -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*3))k -bufsize $((VBR*4))k -pass 2 -passlogfile "$WORK/x264" \
    -r 25 -fps_mode cfr -pix_fmt yuv420p -profile:v high -movflags +faststart \
    -af aresample=async=1 -c:a aac -b:a 128k -ar 48000 -t "$DUR" "$2"
  cd "$HERE"
}
enc "$WORK/mix_music.wav" "$WORK/final_music.mp4"
enc "$WORK/mix_dry.wav" "$WORK/final_dry.mp4"

for f in final_music final_dry; do
  V=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$WORK/$f.mp4")
  A=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$WORK/$f.mp4")
  S=$(stat -c %s "$WORK/$f.mp4")
  R=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate,avg_frame_rate,width,height -of csv=p=0 "$WORK/$f.mp4")
  L=$(ffmpeg -hide_banner -nostats -i "$WORK/$f.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' ' | tr '\n' ' ')
  echo "$f: video ${V}s audio ${A}s diff $($PY -c "print(round(abs($V-$A),3))")s size $((S/1024/1024))MiB ($S B) $R | $L"
done
