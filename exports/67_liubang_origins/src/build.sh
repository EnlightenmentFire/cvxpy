set -e
. ../.venv/bin/activate
python render.py voice/timeline.json video video_noaudio.mp4 4 > render.log 2>&1
python music.py voice/timeline.json voice/narration.wav audio
VD=$(ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 video_noaudio.mp4)
mux(){ ffmpeg -y -v error -i video_noaudio.mp4 -i voice/narration.wav -i audio/music.wav -i audio/sfx.wav -filter_complex "[1:a]aformat=channel_layouts=stereo[v];$1,loudnorm=I=-14.8:TP=-2.5:LRA=11,alimiter=limit=0.68:level=disabled,volume=0.75dB,aresample=48000:async=1,atrim=0:$VD[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 128k -ar 48000 -t $VD -movflags +faststart $2; }
mux "[v][2:a][3:a]amix=inputs=3:normalize=0" final.mp4
mux "[v][3:a]amix=inputs=2:normalize=0" final_nomusic.mp4
for f in final.mp4 final_nomusic.mp4; do echo $f $(stat -c %s $f); ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 $f; ffmpeg -nostats -i $f -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" ; done
echo BUILD_OK
