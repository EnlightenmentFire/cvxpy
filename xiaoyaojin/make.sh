#!/usr/bin/env bash
# 一键出片：timeline → 并行渲染 → 混音与响度 → 两遍编码（体积 < 100MB）
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
AUD="${1:?audio dir}"
WORK="${2:?work dir}"
OUT="$HERE/out"
LUFS="${LUFS:--16}"
OUTNAME="${OUTNAME:-xiaoyaojin_1080x1920}"
mkdir -p "$WORK" "$OUT"
cd "$HERE"

python3 render.py timeline "$AUD"
DUR=$(python3 -c "import json;print(json.load(open('timeline.json'))['total'])")
echo "duration $DUR"

# 1) 并行渲染 4 段
N=4
for k in $(seq 0 $((N-1))); do
  python3 render.py chunk $k $N "$WORK/chunk_$k.mp4" > "$WORK/chunk_$k.log" 2>&1 &
  PIDS[$k]=$!
done
for k in $(seq 0 $((N-1))); do wait ${PIDS[$k]} || { echo "chunk $k FAILED"; tail -5 "$WORK/chunk_$k.log"; exit 1; }; done
# 帧数校验：总帧数必须等于时间线帧数，否则音画会错位
python3 - "$WORK" $N <<'EOF'
import json, math, subprocess, sys
W, N = sys.argv[1], int(sys.argv[2])
nf = math.ceil(json.load(open('timeline.json'))['total'] * 25)
got = sum(int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_packets', '-show_entries', 'stream=nb_read_packets',
          '-of', 'csv=p=0', f'{W}/chunk_{k}.mp4']).decode().strip()) for k in range(N))
print('frames', got, 'expected', nf)
sys.exit(0 if got == nf else 1)
EOF
: > "$WORK/list.txt"
for k in $(seq 0 $((N-1))); do echo "file '$WORK/chunk_$k.mp4'" >> "$WORK/list.txt"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/video_hq.mp4"

# 2) 混音（旁白 + 少量音效，无配乐），响度 -16 LUFS 双遍
python3 mix.py "$WORK/mix.wav"
AF="highpass=f=70,equalizer=f=180:t=q:w=1:g=1.5,equalizer=f=7000:t=q:w=2:g=-1"
ffmpeg -y -hide_banner -i "$WORK/mix.wav" -af "$AF,loudnorm=I=$LUFS:TP=-1.5:LRA=11:print_format=json" -f null - 2> "$WORK/ln.txt"
read MI MTP MLRA MTH OFF < <(python3 - "$WORK/ln.txt" <<'EOF'
import json,sys,re
t=open(sys.argv[1]).read(); j=json.loads(t[t.rindex('{'):t.rindex('}')+1])
print(j['input_i'],j['input_tp'],j['input_lra'],j['input_thresh'],j['target_offset'])
EOF
)
ffmpeg -y -loglevel error -i "$WORK/mix.wav" -af "$AF,loudnorm=I=$LUFS:TP=-1.5:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=48000" \
  -c:a aac -b:a 128k "$WORK/audio.m4a"

# 3) 两遍编码：总目标 92MB
VK=$(python3 -c "d=$DUR; print(int((92*8*1000*1000/1.048576**0)/d/1000 - 135))")
echo "video kbps $VK"
cd "$WORK"
ffmpeg -y -loglevel error -i video_hq.mp4 -c:v libx264 -preset slow -tune animation -b:v ${VK}k -maxrate $((VK*3))k -bufsize $((VK*4))k \
  -pix_fmt yuv420p -g 250 -pass 1 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i video_hq.mp4 -i audio.m4a -map 0:v -map 1:a -c:v libx264 -preset slow -tune animation -b:v ${VK}k \
  -maxrate $((VK*3))k -bufsize $((VK*4))k -pix_fmt yuv420p -g 250 -pass 2 -c:a copy -movflags +faststart \
  -metadata title="八百人冲阵之前，那封信写了什么？" "$OUT/$OUTNAME.mp4"
ls -l "$OUT/$OUTNAME.mp4"
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate "$OUT/$OUTNAME.mp4"
