#!/usr/bin/env bash
# Full render: picture (parallel Playwright workers) -> audio loudnorm -> mux (2-pass x264, <100MB) -> checks.
set -euo pipefail
cd "$(dirname "$0")"
WORK=/tmp/claude-0/work; OUTD=${OUTD:-$WORK/final}; mkdir -p $OUTD $WORK/parts
FPS=25; WORKERS=${WORKERS:-4}; VBR=${VBR:-820k}
TOTAL=$(python3 -c "import json;print(json.load(open('$WORK/timeline.json'))['total'])")
NF=$(python3 -c "import math;print(math.ceil($TOTAL*$FPS))")
echo "total ${TOTAL}s frames $NF"
if [ "${SKIP_PICTURE:-0}" != 1 ]; then
  rm -f $WORK/parts/*.mp4
  CH=$(( (NF + WORKERS - 1) / WORKERS )); pids=()
  for i in $(seq 0 $((WORKERS-1))); do a=$((i*CH)); b=$(( (i+1)*CH < NF ? (i+1)*CH : NF ));
    node render/shoot.js frames $WORK/parts/p$i.mp4 $a $b $FPS > $WORK/parts/p$i.log 2>&1 & pids+=($!); done
  for p in "${pids[@]}"; do wait $p; done
  : > $WORK/parts/list.txt; for i in $(seq 0 $((WORKERS-1))); do echo "file '$WORK/parts/p$i.mp4'" >> $WORK/parts/list.txt; done
  ffmpeg -y -v error -f concat -safe 0 -i $WORK/parts/list.txt -c copy $WORK/picture.mp4
fi
# audio: two-pass loudnorm to -15 LUFS / -1.5 dBTP, then AAC
for v in music nomusic; do
  J=$(ffmpeg -hide_banner -i $WORK/audio/mix_$v.wav -af loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  mi=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
  read I TP LRA TH OFF <<< "$mi"
  ffmpeg -y -v error -i $WORK/audio/mix_$v.wav -af "loudnorm=I=-15:TP=-1.5:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,aresample=48000" -ar 48000 $WORK/audio/final_$v.wav
done
# mux: 2-pass x264 ABR (constant 25 fps), AAC 128k, aresample async
for v in music nomusic; do
  if [ $v = music ]; then NAME="全军撤退时谁留下来断后"; else NAME="全军撤退时谁留下来断后_无配乐版"; fi
  if [ $v = music ]; then
    ffmpeg -y -v error -i $WORK/picture.mp4 -c:v libx264 -preset slow -b:v $VBR -maxrate 2200k -bufsize 4400k -pass 1 -passlogfile $WORK/x264 -r $FPS -pix_fmt yuv420p -an -f mp4 /dev/null
    ffmpeg -y -v error -i $WORK/picture.mp4 -c:v libx264 -preset slow -b:v $VBR -maxrate 2200k -bufsize 4400k -pass 2 -passlogfile $WORK/x264 -r $FPS -pix_fmt yuv420p -an $WORK/video_only.mp4
  fi
  ffmpeg -y -v error -i $WORK/video_only.mp4 -i $WORK/audio/final_$v.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -af aresample=async=1 -shortest -movflags +faststart "$OUTD/$NAME.mp4"
done
ls -la $OUTD
