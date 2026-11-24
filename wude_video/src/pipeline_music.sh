#!/bin/bash
# Starts after the narration TTS has finished (memory: never run MusicGen next to the TTS model).
# MusicGen versions -> automatic pick (least intrusive) -> continuation of the long-running layers.
set -u
B=/home/user/wude_build
R=/home/user/cvxpy/wude_video
PY=/home/user/venv/bin/python
LOG=$B/music_pipeline.log
echo "[$(date +%T)] waiting for TTS to finish" >> $LOG
while ! grep -q "ALL DONE" $B/tts_full.log; do sleep 30; done
while pgrep -f tts_batch.py > /dev/null; do sleep 10; done
echo "[$(date +%T)] MusicGen versions" >> $LOG
MG_BATCH=4 THREADS=4 $PY $R/src/music_gen.py versions >> $LOG 2>&1
echo "[$(date +%T)] scoring" >> $LOG
$PY $R/src/music_score.py $B/music/clips $B/music/selection.json >> $LOG 2>&1
echo "[$(date +%T)] extending long-running layers" >> $LOG
MG_BATCH=3 THREADS=4 $PY $R/src/music_gen.py extend $B/music/selection.json base:3 push_tension:2 push_warm:2 >> $LOG 2>&1
echo "[$(date +%T)] MUSIC DONE" >> $LOG
