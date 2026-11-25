#!/bin/bash
# gain to -15 LUFS + peak limiter, verify on the encoded AAC; video stream copied
set -e
O=/home/user/work/out; D=/home/user/work/deliver
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $O/video.mp4)
meas() { ffmpeg -hide_banner -i "$1" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | awk '{print $2}' | tr '\n' ' '; }
for kind in music nomusic; do
  NAME="68_刘备的第一笔起家资本"; [ $kind = nomusic ] && NAME="68_刘备的第一笔起家资本_无配乐"
  I0=$(meas $O/mix_$kind.wav | awk '{print $1}')
  G=$(python3 -c "print(-15.0 - ($I0) + ${EXTRA:-0.25})")
  ffmpeg -v error -y -i $O/mix_$kind.wav -af "aresample=192000,volume=${G}dB,alimiter=limit=-2.3dB:attack=0.5:release=40:level=disabled:asc=1,aresample=48000" -t $VD -c:a pcm_s16le $O/audio_$kind.wav
  ffmpeg -v error -y -i $O/v_final.mp4 -i $O/audio_$kind.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -ar 48000 -af aresample=async=1 -movflags +faststart -shortest "$D/$NAME.mp4"
  echo "$kind in=$I0 gain=$G out(I TP)=$(meas "$D/$NAME.mp4")"
done
