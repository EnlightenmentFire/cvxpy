#!/usr/bin/env bash
# Full build: timeline -> video frames -> soundtrack -> 2-pass encode under 100 MB -> checks.
# usage: build_final.sh <narration_dir> <out.mp4>
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
NAR="$1"
OUT="$2"
SP=/tmp/claude-0/-home-user-cvxpy/f0c8e50d-dc80-5fad-820f-299cfe1179c7/scratchpad
WORK="$SP/final"
mkdir -p "$WORK"
cd "$SRC"

echo "[1/6] timeline"
python3 -c "
import json, timeline as T
tl = T.build('$NAR')
json.dump(tl, open('$WORK/timeline.json', 'w'), ensure_ascii=False)
print('total', round(tl['total'], 1), 's')
"

echo "[2/6] video"
NPROC=${NPROC:-4} python3 render.py "$NAR" "$WORK/video.mp4"

echo "[3/6] soundtrack"
python3 mix.py "$NAR" "$WORK/audio.wav"

echo "[4/6] encode (2-pass, size-targeted)"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/video.mp4")
# 94 MB total budget, 96 kb/s AAC, 1% container overhead
VBR=$(python3 -c "d=float('$DUR'); print(int((94e6*8/d - 96e3) * 0.99 / 1000))")
echo "duration ${DUR}s -> video ${VBR} kb/s"
cd "$WORK"
ffmpeg -y -loglevel error -i video.mp4 -c:v libx264 -preset slow -tune film -b:v ${VBR}k -pass 1 -passlogfile p1 -an -f null /dev/null
ffmpeg -y -loglevel error -i video.mp4 -i audio.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -tune film -b:v ${VBR}k -maxrate $((VBR * 25 / 10))k -bufsize $((VBR * 5))k -pass 2 -passlogfile p1 \
  -pix_fmt yuv420p -profile:v high -level 4.1 -r 30 \
  -c:a aac -b:a 96k -ar 48000 -movflags +faststart -shortest "$OUT"
ls -la "$OUT"

echo "[5/6] whole-film ASR"
ffmpeg -y -loglevel error -i "$OUT" -vn -ac 1 -ar 48000 "$WORK/final_audio.wav"
( source "$SP/qwen312/bin/activate" && HF_HUB_OFFLINE=1 python "$SRC/asr_film.py" "$WORK/final_audio.wav" "$WORK/timeline.json" "$WORK/asr_film.txt" ) | head -40

echo "[6/6] QA frames"
python3 - <<EOF
import cv2, numpy as np, json, subprocess
tl = json.load(open('$WORK/timeline.json'))
ts = np.linspace(2, tl['total'] - 2, 24)
imgs = []
for t in ts:
    p = '$WORK/qa_%06.1f.png' % t
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t:.2f}', '-i', '$OUT', '-frames:v', '1', p], check=True)
    im = cv2.imread(p); imgs.append(cv2.resize(im, (270, 480), interpolation=cv2.INTER_AREA))
rows = [np.concatenate(imgs[i:i + 8], 1) for i in range(0, 24, 8)]
cv2.imwrite('$WORK/qa_sheet.jpg', np.concatenate(rows, 0), [cv2.IMWRITE_JPEG_QUALITY, 85])
print('qa sheet written')
EOF
echo done
