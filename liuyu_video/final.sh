#!/bin/bash
# 成片：选配乐 → 混音 → 质检 → 渲染 → 封装检查
set -e
PY=/home/user/work/venv/bin/python
NARR=/home/user/work/qnarr_full
MIXD=/home/user/work/mix_final
OUT=/home/user/cvxpy/liuyu_video/out/final
cd /home/user/cvxpy/liuyu_video
mkdir -p "$MIXD" "$OUT"
[ -f "$MIXD/layers.json" ] || $PY choose_layers.py /home/user/work/ace_layers "$MIXD/layers.json"
$PY mix2.py "$NARR" "$MIXD/layers.json" "$MIXD"
$PY final_check.py "$MIXD" "$NARR" | tail -25
$PY render.py "$NARR/meta.json" "$OUT/京口起兵.mp4" --audio "$MIXD/mix.wav" --final --vbit "${VBIT:-1650k}"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$OUT/京口起兵.mp4"
