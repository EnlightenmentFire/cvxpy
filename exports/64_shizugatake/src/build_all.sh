#!/bin/bash
# Full build after all TTS lines exist. usage: bash build_all.sh <tempo>
set -e
cd "$(dirname "$0")"
. /tmp/claude-0/work/venv/bin/activate
WK=/tmp/claude-0/work
EXP=$(cd .. && pwd)
TEMPO=${1:-1.15}
python voice_post.py "$TEMPO"
python timeline.py | head -1
python make_docs.py "$EXP"
rm -rf $WK/segs; mkdir -p $WK/segs
for i in 0 1 2 3; do python render.py seg $i 4 > $WK/segs/log_$i.txt 2>&1 & done
python audio.py
wait
ls $WK/segs/seg_0*.mp4 | sed 's/^/file /' > $WK/segs/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $WK/segs/list.txt -c copy $WK/video_noaudio.mp4
python final_mux.py $WK/out "${VB:-820k}"
