#!/bin/bash
# Run after narration synthesis: post -> ASR -> timeline -> music -> mix -> picture -> encode -> docs.
set -e
PY=/tmp/claude-0/venv/bin/python
W=/tmp/claude-0/work
SRC=$(cd "$(dirname "$0")" && pwd)
OUT=$W/final; mkdir -p $OUT
cd $SRC
TEMPO_N=1.06 TEMPO_Q=1.0 $PY voice_post.py
$PY render.py timeline $W/tts/proc/durations.json $OUT/timeline.json
$PY music.py $OUT/timeline.json $OUT/music.wav
$PY sfx_mix.py $OUT/timeline.json $OUT/music.wav $OUT
NPROC=4 $PY render.py video $OUT/timeline.json $OUT/video_silent.mp4
$PY final_encode.py $OUT/video_silent.mp4 $OUT/mix_music.wav $OUT/mix_nomusic.wav "$OUT/王安石变法为什么失败_1080x1920.mp4" "$OUT/王安石变法为什么失败_1080x1920_无配乐.mp4"
echo PIPELINE DONE
