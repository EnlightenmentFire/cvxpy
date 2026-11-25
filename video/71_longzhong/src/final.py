# -*- coding: utf-8 -*-
"""成片：两遍 x264（恒定 25 fps）+ AAC 128k；音频 aresample=async=1；有配乐版与无配乐版共用同一视频流。
最后 ffprobe 核对音视频流时长差 ≤0.1 s、文件 <100MB。
usage: python final.py OUTDIR
"""
import sys, os, subprocess, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import TL, FPS
W = os.environ.get('WORK', '/home/user/work')
V = f'{W}/vid/out/video.mp4'
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
T = TL()
nf = int(math.ceil(T.total * FPS)); dur = nf / FPS
target_mb = 93.0
vb = int((target_mb * 8 * 1024 * 1024 / dur - 128_000 - 8_000) / 1000)
print('dur', round(dur, 2), 'video kbps', vb)
common = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vb}k', '-maxrate', f'{int(vb * 1.8)}k', '-bufsize', f'{vb * 3}k',
          '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-fps_mode', 'cfr', '-g', '50',
          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
          '-x264-params', 'aq-mode=3:aq-strength=0.9:psy-rd=1.0,0.10:deblock=1,1']
pl = f'{W}/vid/out/x264pass'
run = lambda a: subprocess.run(a, check=True)
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', V, *common, '-pass', '1', '-passlogfile', pl, '-an', '-f', 'mp4', '/dev/null'])
vonly = f'{W}/vid/out/video_final.mp4'
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', V, *common, '-pass', '2', '-passlogfile', pl, '-an', '-t', f'{dur:.3f}', vonly])
names = {'mix': '隆中对与三顾茅庐.mp4', 'mix_nomusic': '隆中对与三顾茅庐_无配乐版.mp4'}
rep = {}
for a, nm in names.items():
    o = os.path.join(out, nm)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vonly, '-i', f'{W}/audio/{a}.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-af', 'aresample=async=1:first_pts=0', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2', '-t', f'{dur:.3f}',
         '-movflags', '+faststart', o])
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,duration,r_frame_rate,width,height,nb_frames',
                                    '-show_entries', 'format=size,duration', '-of', 'json', o], capture_output=True, text=True).stdout)
    st = {s['codec_type']: s for s in pr['streams']}
    dv, da = float(st['video']['duration']), float(st['audio']['duration'])
    size = int(pr['format']['size'])
    rep[nm] = dict(video_s=dv, audio_s=da, diff=round(abs(dv - da), 3), size_mb=round(size / 1e6, 2), size_mib=round(size / 2 ** 20, 2),
                   fps=st['video']['r_frame_rate'], wh=f"{st['video']['width']}x{st['video']['height']}", frames=st['video'].get('nb_frames'))
    lo = subprocess.run(['ffmpeg', '-hide_banner', '-i', o, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summ = lo[lo.rindex('Summary:'):]
    rep[nm]['loudness'] = ' '.join(l.strip() for l in summ.splitlines() if l.strip().startswith(('I:', 'Peak:')))
    assert rep[nm]['diff'] <= 0.1, rep[nm]
    assert size < 100e6, rep[nm]
json.dump(rep, open(os.path.join(out, 'final_check.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1))
