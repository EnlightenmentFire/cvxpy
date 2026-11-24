#!/usr/bin/env bash
# Final assembly: processed narration -> video frames -> music arrangement -> spec mix -> checks -> encode.
# Usage: run_final.sh <voice_dir> <robot.wav> <music_takes_dir> <work_dir> <out_dir> [music_vol]
set -euo pipefail
VOICE=$1; ROBOT=$2; TAKES=$3; WORK=$4; OUT=$5; VOL=${6:-0.5}
HERE=$(cd "$(dirname "$0")" && pwd)
source /home/user/.venvs/tts/bin/activate
mkdir -p "$WORK" "$OUT"

echo "== 1. video frames"
rm -rf "$WORK/video_parts" "$WORK/video.mp4"
python "$HERE/render/video.py" --voice "$VOICE" --robot "$ROBOT" --out "$WORK/video.mp4" --workers 4

echo "== 2. music arrangement"
python "$HERE/audio/music_build.py" "$VOICE" "$ROBOT" "$TAKES/choices.json" "$TAKES" "$WORK/music.wav"

echo "== 3. spec mix (sidechain, EQ, loudnorm)"
python "$HERE/audio/final_mix.py" "$VOICE" "$ROBOT" "$WORK/music.wav" "$WORK" "$VOL"

echo "== 4. encode"
python "$HERE/render/encode.py" "$WORK/video.mp4" "$WORK/mix.wav" "$OUT/ai_knowledge_jackrabbits_1080x1920.mp4" 92
python - <<EOF
import sys
sys.path.insert(0, "$HERE/render")
import encode
mb = encode.swap_audio("$OUT/ai_knowledge_jackrabbits_1080x1920.mp4", "$WORK/mix_nomusic.wav",
                       "$OUT/ai_knowledge_jackrabbits_1080x1920_nomusic.mp4")
print("no-music version", round(mb, 1), "MB")
EOF
ls -la "$OUT"
