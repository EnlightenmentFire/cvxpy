#!/bin/bash
# Unattended: finish narration -> re-synthesise edited lines -> voice post -> QC report -> picture master.
# The background music / final mix is NOT done here (waits for the music spec).
set -u
B=/home/user/wude_build
R=/home/user/cvxpy
PY=/home/user/venv/bin/python
LOG=$B/pipeline.log
echo "[$(date +%T)] waiting for first TTS pass" >> $LOG
while ! grep -q "ALL DONE" $B/tts_full.log; do sleep 60; done
echo "[$(date +%T)] first pass done; re-synthesising edited lines" >> $LOG
cd $R && python3 wude_video/src/script_parser.py wude_video/script/wude.script $B/script.json >> $LOG 2>&1
$PY wude_video/src/tts_batch.py $B/script.json $B/tts_raw >> $B/tts_full2.log 2>&1
echo "[$(date +%T)] voice post" >> $LOG
$PY wude_video/src/voice_post.py $B/tts_raw $B/voice_post >> $LOG 2>&1
$PY - >> $LOG 2>&1 <<'EOF'
import json, glob
rows = []
for f in sorted(glob.glob('/home/user/wude_build/tts_raw/*.json')):
    m = json.load(open(f, encoding='utf-8'))
    if m.get('flagged') or m['ser'] > 0.08 or not (85 <= m['f0'] <= 105):
        rows.append(f"{m['id']}\tf0={m['f0']:.1f}\tser={m['ser']:.3f}\t{m['text']}\t| ASR: {m['asr']}")
open('/home/user/wude_build/tts_qc_flags.txt', 'w', encoding='utf-8').write("\n".join(rows) + "\n")
print("QC flags:", len(rows))
EOF
echo "[$(date +%T)] rendering picture master" >> $LOG
cd $B && DURATIONS=$B/voice_post/durations.json CRF=16 $PY $R/wude_video/src/render.py video $B/picture_master.mp4 >> $LOG 2>&1
echo "[$(date +%T)] PICTURE DONE" >> $LOG
