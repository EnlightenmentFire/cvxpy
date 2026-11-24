#!/bin/sh
# 合成成片：母版画面 + 混好的音轨 → 两遍编码到目标体积（默认 92MB，视频号上限 100MB）→ H.264/AAC mp4
# 响度归一到 -16 LUFS。用法：sh tools/mux.sh [母版] [音轨] [输出] [目标MB]
set -e
cd "$(dirname "$0")/.."
V=${1:-build/video.mp4}; A=${2:-build/audio.wav}; O=${3:-out/sunzi_ep01.mp4}; MB=${4:-92}
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
ABR=160
VBR=$(python3 -c "print(int($MB*8*1024*1024/$DUR/1000 - $ABR - 12))")
echo "duration=$DUR video=${VBR}k audio=${ABR}k"
X="-c:v libx264 -preset slow -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pix_fmt yuv420p -profile:v high -x264-params aq-mode=3:aq-strength=1.1:deblock=-1,-1 -color_primaries bt709 -color_trc bt709 -colorspace bt709"
ffmpeg -y -loglevel error -i "$V" $X -pass 1 -passlogfile build/x264pass -an -f null /dev/null
ffmpeg -y -loglevel error -i "$V" -i "$A" -map 0:v -map 1:a $X -pass 2 -passlogfile build/x264pass \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a ${ABR}k -shortest -movflags +faststart "$O"
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$O"
