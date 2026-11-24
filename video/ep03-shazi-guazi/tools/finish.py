"""Concat rendered segments, final H.264 encode, loudness-normalised AAC, mux. Usage: finish.py <render dir> <mix.wav> <out.mp4> [crf]"""
import sys, subprocess, json, re, os
rd, mix, out = sys.argv[1:4]; crf = sys.argv[4] if len(sys.argv) > 4 else '19'
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', mix, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S).group(0))
af = f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
print('measured', m['input_i'], 'LUFS, TP', m['input_tp'])
os.makedirs(os.path.dirname(out), exist_ok=True)
cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{rd}/list.txt', '-i', mix,
       '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-maxrate', '3200k', '-bufsize', '6400k', '-pix_fmt', 'yuv420p', '-r', '30', '-profile:v', 'high', '-level', '4.2',
       '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
       '-af', af, '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', '-shortest', out]
subprocess.run(cmd, check=True)
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate', '-of', 'json', out], capture_output=True, text=True)
print(p.stdout)
