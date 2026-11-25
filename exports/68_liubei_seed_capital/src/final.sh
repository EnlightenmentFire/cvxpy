#!/bin/bash
# final assembly: concat video segments, loudnorm audio, 2-pass x264 < 100MB, both versions
set -e
O=/home/user/work/out; D=/home/user/work/deliver
cd $O
ls seg_*.mp4 | sort | sed "s/^/file '/;s/$/'/" > segs.txt
ffmpeg -v error -y -f concat -safe 0 -i segs.txt -c copy video.mp4
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 video.mp4)
for kind in music nomusic; do
  IN=mix_$kind.wav
  J=$(ffmpeg -hide_banner -i $IN -af loudnorm=I=-15:TP=-1.8:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  mi=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'])")
  mtp=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_tp'])")
  mlra=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_lra'])")
  mth=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_thresh'])")
  off=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['target_offset'])")
  ffmpeg -v error -y -i $IN -af "loudnorm=I=-15:TP=-1.8:LRA=11:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true,aresample=48000" -t $VD -c:a pcm_s16le audio_$kind.wav
done
DUR=$VD
VB=$(python3 -c "print(int(94e6*8/$DUR/1000 - 128))")
echo "duration $DUR video kbps $VB"
ffmpeg -v error -y -i video.mp4 -c:v libx264 -preset slow -b:v ${VB}k -pass 1 -passlogfile x264pass -fps_mode cfr -r 25 -pix_fmt yuv420p -an -f mp4 /dev/null
ffmpeg -v error -y -i video.mp4 -c:v libx264 -preset slow -b:v ${VB}k -pass 2 -passlogfile x264pass -fps_mode cfr -r 25 -pix_fmt yuv420p -an v_final.mp4
for kind in music nomusic; do
  NAME="68_刘备的第一笔起家资本"; [ $kind = nomusic ] && NAME="68_刘备的第一笔起家资本_无配乐"
  ffmpeg -v error -y -i v_final.mp4 -i audio_$kind.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -ar 48000 -af aresample=async=1 -movflags +faststart -shortest "$D/$NAME.mp4"
done
ls -la $D/*.mp4
