#!/usr/bin/env bash
# Rebuild episode 55 end to end.
#   bash build.sh                 -> Yunyang voice via edge-tts (needs network)
#   bash build.sh /path/to/wavs   -> use externally generated line_NNNN.wav (e.g. Tocqueville voice)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); EP=$(dirname "$HERE"); cd "$EP"
grep -v '^##' script.txt | sed '/^$/d' > lines.txt
if [ $# -ge 1 ]; then python "$HERE/assemble_voice.py" lines.txt "$1" voice; else python "$HERE/voice_yunyang.py" lines.txt voice; fi
mkdir -p out audio
python "$HERE/render.py" script.txt voice out/video.mp4 --workers "${WORKERS:-4}"
python "$HERE/mix.py" voice out/video_plan.json audio
python "$HERE/cover.py" out
for v in music nomusic; do
  ffmpeg -v error -y -i out/video.mp4 -i audio/mix_$v.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -ar 48000 \
    -af aresample=async=1 -shortest -movflags +faststart out/final_$v.mp4
done
for v in music nomusic; do
  ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 out/final_$v.mp4
done
