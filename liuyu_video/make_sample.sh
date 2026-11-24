#!/bin/bash
# 1 分钟样音 + 样片：bash make_sample.sh NARR_DIR OUT_DIR
set -e
NARR=$1; OUT=$2; PY=/home/user/work/venv/bin/python
cd /home/user/cvxpy/liuyu_video
mkdir -p "$OUT"
# 样音截止到第一章"魏书"那句后 1.2 秒
T1=$($PY -c "
import sys; sys.path.insert(0,'.')
from mix import merged_meta
from timeline import Timeline
p,_ = merged_meta('$NARR'); T = Timeline(p); print(round(T.end('s1d') + 1.2, 2))")
echo "sample end: $T1 s"
$PY mix.py "$NARR" "$OUT/mix_full_tmp.wav" 0 "$T1"
ffmpeg -hide_banner -loglevel error -y -i "$OUT/mix_full_tmp.wav" -af "afade=t=out:st=$(python3 -c "print($T1-1.0)"):d=1.0" -c:a aac -b:a 192k "$OUT/样音_1分钟_配乐.m4a"
# 纯人声版（50Hz 高通，-18 dBFS RMS）
$PY - <<PY
import sys; sys.path.insert(0,'.')
import numpy as np, soundfile as sf
from mix import merged_meta, build_voice
from timeline import Timeline
p, have = merged_meta('$NARR'); T = Timeline(p)
v = build_voice(T, '$NARR', have)[: int($T1 * 48000)]
sf.write('$OUT/voice_tmp.wav', v, 48000)
PY
ffmpeg -hide_banner -loglevel error -y -i "$OUT/voice_tmp.wav" -c:a aac -b:a 192k "$OUT/样音_1分钟_纯人声.m4a"
$PY render.py "$NARR/meta_merged.json" "$OUT/样片_1分钟.mp4" 0 "$T1" --audio "$OUT/mix_full_tmp.wav" --crf 18
rm -f "$OUT/voice_tmp.wav"
ls -la "$OUT"
