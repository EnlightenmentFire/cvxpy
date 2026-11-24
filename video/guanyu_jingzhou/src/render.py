# -*- coding: utf-8 -*-
"""分段并行渲染：每段把原始帧经管道送入 ffmpeg 生成近无损中间文件，最后拼接并与音频合成。"""
import sys, os, subprocess, time, math
from multiprocessing import Pool
FPS = 30
OUT = '/home/user/work/vid/out'
def render_seg(args):
    k, f0, f1 = args
    import skia
    import scenes
    from geo import W, H
    path = f'{OUT}/seg_{k:03d}.mp4'
    if os.path.exists(path + '.done'): return k, 0
    t0 = time.time()
    ct = 'bgra'   # Image.tobytes() 实测为 BGRA 字节序（见 colortest）
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', ct, '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-qp', '10', '-pix_fmt', 'yuv420p', '-threads', '1',
                          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', path], stdin=subprocess.PIPE)
    s = skia.Surface(W, H); c = s.getCanvas()
    for f in range(f0, f1):
        scenes.draw_frame(c, f / FPS, f)
        p.stdin.write(s.makeImageSnapshot().tobytes())
    p.stdin.close(); p.wait()
    open(path + '.done', 'w').write('ok')
    return k, time.time() - t0
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    from timeline import TL
    T = TL(); nf = int(math.ceil(T.total * FPS))
    a = float(sys.argv[2]) if len(sys.argv) > 2 else 0; b = float(sys.argv[3]) if len(sys.argv) > 3 else T.total
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    fa, fb = int(a * FPS), min(nf, int(b * FPS))
    step = 240
    segs = [(i, f, min(fb, f + step)) for i, f in enumerate(range(fa, fb, step))]
    print('frames', fb - fa, 'segs', len(segs), flush=True)
    t0 = time.time()
    with Pool(nproc) as pool:
        for k, dt in pool.imap_unordered(render_seg, segs):
            print('seg', k, round(dt, 1), 'elapsed', round(time.time() - t0), flush=True)
    with open(f'{OUT}/list.txt', 'w') as f:
        for k, _, _ in segs: f.write(f"file 'seg_{k:03d}.mp4'\n")
    print('RENDERDONE', round(time.time() - t0), flush=True)
