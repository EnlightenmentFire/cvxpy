"""并行渲染全片画面，再与混好的声音合成 MP4。

用法: python render_all.py <work> <timeline.json> <audio.wav> <out.mp4> [workers]
目标文件大小用环境变量 LC_TARGET_MB 指定（默认 86MB）。
"""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
work, tlp, audio, outp = sys.argv[1:5]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 4
FPS = 30
tl = json.load(open(tlp))
total = tl['total']
nfr = int(round(total * FPS))
CH = 600                                    # 每段 20 秒
segs = [(a, min(a + CH, nfr)) for a in range(0, nfr, CH)]
os.makedirs(work + '/out/segs', exist_ok=True)


def run(i):
    a, b = segs[i]
    out = f'{work}/out/segs/seg_{i:03d}.mp4'
    log = f'{work}/out/segs/seg_{i:03d}.log'
    if os.path.exists(out + '.ok'):
        return out
    t = time.time()
    with open(log, 'w') as lf:
        r = subprocess.run([sys.executable, HERE + '/film.py', 'render', work, tlp, out, f'{a / FPS:.6f}', f'{b / FPS:.6f}'],
                           stdout=lf, stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
    if r.returncode != 0:
        raise RuntimeError(f'segment {i} failed, see {log}')
    open(out + '.ok', 'w').write('ok')
    print('seg %d/%d  frames %d-%d  %.0fs' % (i + 1, len(segs), a, b, time.time() - t), flush=True)
    return out


t0 = time.time()
with ThreadPoolExecutor(workers) as ex:
    outs = list(ex.map(run, range(len(segs))))
lst = work + '/out/segs/list.txt'
open(lst, 'w').write(''.join(f"file '{o}'\n" for o in outs))
print('frames rendered in %.0fs; encoding' % (time.time() - t0), flush=True)
# 两遍编码，按目标文件大小定码率（留出音频与余量）
TARGET_MB = float(os.environ.get('LC_TARGET_MB', '86'))
vbr = int((TARGET_MB * 8e6 / total - 192e3) / 1000)
common = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vbr}k', '-maxrate', f'{int(vbr * 2.2)}k', '-bufsize', f'{int(vbr * 4)}k',
          '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1', '-r', str(FPS),
          '-x264-params', 'aq-mode=3:aq-strength=1.0:deblock=-1,-1:psy-rd=0.8,0.1:keyint=150:min-keyint=30',
          '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709']
plog = work + '/out/segs/x264pass'
subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, *common,
                '-pass', '1', '-passlogfile', plog, '-an', '-f', 'null', '/dev/null'], stdin=subprocess.DEVNULL, check=True)
subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio,
                '-map', '0:v', '-map', '1:a', *common, '-pass', '2', '-passlogfile', plog,
                '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', outp],
               stdin=subprocess.DEVNULL, check=True)
print('video bitrate target %dk' % vbr, flush=True)
sz = os.path.getsize(outp) / 1e6
print('done %s  %.1f MB  total %.0fs' % (outp, sz, time.time() - t0), flush=True)
