#!/bin/bash
# 全片构建：配音后处理 → ASR → 混音 → 4 进程渲染 → 拼接 → 两遍编码（<100MB）→ 校验 → 封面/导出
set -e
cd "$(dirname "$0")"
PY=/tmp/claude-0/work/venv/bin/python
WK=/tmp/claude-0/work
OUT=${OUT:-/home/user/cvxpy/exports/50_no_center}
SLUG="没有中心的智慧"
TEMPO=${TEMPO:-1.0} $PY voice_post.py
$PY - <<'P'
import timeline, re
lines, sc, total = timeline.build()
n = sum(timeline.nchars(l["say"]) for l in lines)
print(f"rate incl. pauses: {n / (lines[-1]['end'] - lines[0]['start']) * 60:.0f} chars/min; total {total:.1f}s")
P
ASR_T=4 ASR_OUT=$WK/asr.json $PY asr_check.py 2>&1 | grep -E "!!|TOTAL" | tee $WK/asr_summary.txt
$PY mix.py $WK/mix
rm -rf $WK/segs; mkdir -p $WK/segs
for i in 0 1 2 3; do $PY render.py --seg $i 4 $WK/segs > $WK/segs/log_$i.txt 2>&1 & done; wait
for i in 0 1 2 3; do echo "file seg_0$i.mp4"; done > $WK/segs/list.txt
DUR=$($PY -c "import timeline;print(timeline.build()[2])")
VB=$($PY -c "print(int((95*8*1024*1024/$DUR - 128000)/1000))")
echo "video bitrate ${VB}k"
cd $WK
ffmpeg -v error -y -f concat -safe 0 -i segs/list.txt -c:v libx264 -preset slow -b:v ${VB}k -pass 1 -passlogfile x264p -r 25 -an -f mp4 /dev/null
for v in main nomusic; do
  A=mix/mix.wav; [ $v = nomusic ] && A=mix/mix_nomusic.wav
  ffmpeg -v error -y -f concat -safe 0 -i segs/list.txt -i $A -map 0:v -map 1:a -c:v libx264 -preset slow -b:v ${VB}k -pass 2 -passlogfile x264p \
    -r 25 -pix_fmt yuv420p -c:a aac -b:a 128k -ar 48000 -af aresample=async=1 -movflags +faststart -shortest final_$v.mp4
done
ls -la final_*.mp4
ffprobe -v error -show_entries stream=codec_type,duration,r_frame_rate,width,height -of compact final_main.mp4
