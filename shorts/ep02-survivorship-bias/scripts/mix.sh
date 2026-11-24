#!/bin/bash
END=$(python -c "import json;print(json.load(open('voice/timeline_final.json'))['end'])")
# usage: mix.sh music_gain out.wav  —— 按《配乐规范》参考链路；另存一条压低后的纯音乐用于测量
G=$1; OUT=$2
ffmpeg -loglevel error -y -i voice/voice.wav -i music/music.wav -filter_complex \
"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur=${END},asplit=3[v][sc][v2];[1:a]volume=$G,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=0.12[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=10:release=300,asplit=2[duck][dm];[v][duck]amix=inputs=2:duration=longest:normalize=0[mx]" \
-map "[mx]" -ar 48000 mix_raw.wav -map "[dm]" -ar 48000 music/ducked.wav -map "[v2]" -ar 48000 voice/voice_st.wav
