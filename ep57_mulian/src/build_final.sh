#!/usr/bin/env bash
# Final assembly: render chunks -> concat -> two-pass x264 sized under 100 MB, two audio versions at -15 LUFS / -1.5 dBTP.
set -euo pipefail
cd "$(dirname "$0")"
WORK=${WORK:-/tmp/claude-0/work}
OUT=${OUT:-$WORK/final}
NAME=${NAME:-目连救母与盂兰盆}
mkdir -p "$OUT" "$WORK/video"
. "$WORK/venv/bin/activate"

loudnorm() {   # $1 in.wav  $2 out.wav : two-pass EBU R128 to -15 LUFS, TP -1.5
  local js
  js=$(ffmpeg -hide_banner -i "$1" -af loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  local mi mtp mlra mth off
  mi=$(echo "$js" | python -c 'import json,sys;print(json.load(sys.stdin)["input_i"])')
  mtp=$(echo "$js" | python -c 'import json,sys;print(json.load(sys.stdin)["input_tp"])')
  mlra=$(echo "$js" | python -c 'import json,sys;print(json.load(sys.stdin)["input_lra"])')
  mth=$(echo "$js" | python -c 'import json,sys;print(json.load(sys.stdin)["input_thresh"])')
  off=$(echo "$js" | python -c 'import json,sys;print(json.load(sys.stdin)["target_offset"])')
  ffmpeg -v error -y -i "$1" -af "loudnorm=I=-15:TP=-1.5:LRA=11:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true,aresample=48000" -c:a pcm_s16le "$2"
}

if [ "${SKIP_AUDIO:-0}" != 1 ]; then
  python music.py
  python mix.py
  loudnorm "$WORK/audio/mix_music.wav" "$WORK/audio/final_music.wav"
  loudnorm "$WORK/audio/mix_nomusic.wav" "$WORK/audio/final_nomusic.wav"
fi

if [ "${SKIP_VIDEO:-0}" != 1 ]; then
  N=4
  for i in $(seq 0 $((N-1))); do python render.py chunk $i $N > "$WORK/video/log_$i.txt" 2>&1 & done
  wait
  : > "$WORK/video/list.txt"
  for i in $(seq 0 $((N-1))); do printf "file '%s'\n" "$WORK/video/chunk_$(printf %02d $i).mp4" >> "$WORK/video/list.txt"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$WORK/video/list.txt" -c copy "$WORK/video/master.mp4"
fi

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/video/master.mp4")
# budget: 95 MB total, 128 kbps audio
VB=$(python -c "print(int(95*8*1024*1024/float('$DUR')/1000 - 128 - 8))")
echo "duration $DUR s, video bitrate ${VB}k"
cd "$WORK/video"
ffmpeg -v error -y -i master.mp4 -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*2))k -bufsize $((VB*4))k \
  -pix_fmt yuv420p -r 25 -g 50 -pass 1 -passlogfile x264pass -an -f mp4 /dev/null
for v in music nomusic; do
  if [ $v = music ]; then F="$OUT/${NAME}.mp4"; else F="$OUT/${NAME}_无配乐版.mp4"; fi
  ffmpeg -v error -y -i master.mp4 -i "$WORK/audio/final_$v.wav" -map 0:v -map 1:a \
    -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*2))k -bufsize $((VB*4))k -pix_fmt yuv420p -r 25 -g 50 \
    -pass 2 -passlogfile x264pass -af aresample=async=1 -c:a aac -b:a 128k -ar 48000 -movflags +faststart -shortest "$F"
  echo "== $F"
  ls -la "$F"
  ffprobe -v error -show_entries stream=codec_type,duration,r_frame_rate,width,height -of compact "$F"
done
