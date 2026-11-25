#!/usr/bin/env bash
# Re-render one line's frames, splice them frame-accurately, rebuild audio, final encode + checks.
# usage: patch_finalize.sh <narration_dir> <line_id> <new_line.wav> <out.mp4>
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
NAR="$1"; LID="$2"; NEWWAV="$3"; OUT="$4"
SP=/tmp/claude-0/-home-user-cvxpy/f0c8e50d-dc80-5fad-820f-299cfe1179c7/scratchpad
WORK="$SP/final"
cd "$SRC"

echo "[1/6] swap narration line $LID (duration kept, timeline unchanged)"
[ -f "$NAR/${LID}_old.wav" ] || cp "$NAR/$LID.wav" "$NAR/${LID}_old.wav"
cp "$NEWWAV" "$NAR/$LID.wav"
read F0 F1 < <(python3 -c "
import json, timeline as T
tl = T.build('$NAR')
json.dump(tl, open('$WORK/timeline.json', 'w'), ensure_ascii=False)
ln = [l for l in tl['lines'] if l['id'] == '$LID'][0]
import math
print(int(math.floor(ln['start'] * 30)) - 3, int(math.ceil((ln['start'] + ln['dur']) * 30)) + 3)
" 2>/dev/null | tail -1)
echo "frames $F0..$F1"

echo "[2/6] re-render frames for $LID"
T0=$(python3 -c "print($F0/30)"); T1=$(python3 -c "print($F1/30)")
NPROC=4 python3 render.py "$NAR" "$WORK/patch.mp4" "$T0" "$T1" 2>&1 | grep -v -E "re_|Building|Loading|Dumping|Prefix|cost" | tail -2
NP=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$WORK/patch.mp4")
echo "patch frames: $NP (expected $((F1 - F0)))"

echo "[3/6] soundtrack"
python3 mix.py "$NAR" "$WORK/audio.wav" 2>&1 | grep -v -E "re_|Building|Loading|Dumping|Prefix|cost" | tail -1

echo "[4/6] splice + 2-pass encode"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/video.mp4")
VBR=$(python3 -c "d=float('$DUR'); print(int((94e6*8/d - 96e3) * 0.99 / 1000))")
echo "duration ${DUR}s -> video ${VBR} kb/s"
FC="[0:v]trim=end_frame=${F0},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=${F1},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,fps=30[v]"
cd "$WORK"
ffmpeg -y -loglevel error -i video.mp4 -i patch.mp4 -filter_complex "$FC" -map "[v]" -c:v libx264 -preset slow -tune film -b:v ${VBR}k -pass 1 -passlogfile p2 -an -f null /dev/null
ffmpeg -y -loglevel error -i video.mp4 -i patch.mp4 -i audio.wav -filter_complex "$FC" -map "[v]" -map 2:a \
  -c:v libx264 -preset slow -tune film -b:v ${VBR}k -maxrate $((VBR * 25 / 10))k -bufsize $((VBR * 5))k -pass 2 -passlogfile p2 \
  -pix_fmt yuv420p -profile:v high -level 4.1 -r 30 -c:a aac -b:a 96k -ar 48000 -movflags +faststart -shortest "$OUT"
ls -la "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"

echo "[5/6] whole-film ASR"
ffmpeg -y -loglevel error -i "$OUT" -vn -ac 1 -ar 48000 "$WORK/final_audio.wav"
( source "$SP/qwen312/bin/activate" && HF_HUB_OFFLINE=1 python "$SRC/asr_film.py" "$WORK/final_audio.wav" "$WORK/timeline.json" "$WORK/asr_film.txt" ) 2>&1 | grep -v -i warn | head -40

echo "[6/6] QA frames"
python3 - <<EOF
import cv2, numpy as np, json, subprocess
tl = json.load(open('$WORK/timeline.json'))
ts = list(np.linspace(2, tl['total'] - 2, 21)) + [$F0 / 30 + 2.0, $F0 / 30 + 6.0, $F0 / 30 + 10.0]
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
