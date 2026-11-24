#!/bin/bash
# After MUSIC DONE and PICTURE DONE: arrange + mix per spec -> QC -> encode (<100 MB) -> docs.
set -u
B=/home/user/wude_build
R=/home/user/cvxpy/wude_video
PY=/home/user/venv/bin/python
LOG=$B/final_pipeline.log
A=$B/final_audio
echo "[$(date +%T)] waiting for music and picture" >> $LOG
while ! { grep -q "MUSIC DONE" $B/music_pipeline.log 2>/dev/null && grep -q "PICTURE DONE" $B/pipeline.log; }; do sleep 30; done
cd $B
echo "[$(date +%T)] arrange + mix" >> $LOG
$PY $R/src/make_final_audio.py $B/music/selection.json $A >> $LOG 2>&1 || { echo "FINAL FAILED (mix)" >> $LOG; exit 1; }
echo "[$(date +%T)] QC" >> $LOG
$PY $R/src/qc_audio.py $A >> $LOG 2>&1 || echo "QC step failed (continuing)" >> $LOG
FLIP=$($PY - <<'EOF'
import sys, json
sys.path.insert(0, '/home/user/cvxpy/wude_video/src')
from timeline import Timeline
tl = Timeline(json.load(open('/home/user/wude_build/script.json', encoding='utf-8')),
              json.load(open('/home/user/wude_build/voice_post/durations.json')))
print(round(tl.wk_flip[0], 2))
EOF
)
echo "[$(date +%T)] encode (flip at $FLIP s)" >> $LOG
$PY $R/src/encode_final.py $B/picture_master.mp4 $A/mix.wav $A/mix_nomusic.wav $B/final $FLIP >> $LOG 2>&1 || { echo "FINAL FAILED (encode)" >> $LOG; exit 1; }
$PY $R/src/make_music_doc.py $A >> $LOG 2>&1 || echo "doc step failed" >> $LOG
echo "[$(date +%T)] FINAL DONE" >> $LOG
