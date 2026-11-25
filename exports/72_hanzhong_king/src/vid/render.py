# -*- coding: utf-8 -*-
"""分段并行渲染：每段原始帧经管道送入 ffmpeg 生成近无损中间文件（恒定 25 fps），最后拼接。"""
import sys, os, subprocess, time, math
from multiprocessing import Pool
FPS = 25
OUT = '/tmp/claude-0/work/vid/out'
def render_seg(args):
    k, f0, f1 = args
    import skia, scenes
    from geo import W, H
    path = f'{OUT}/seg_{k:03d}.mp4'
    if os.path.exists(path + '.done'): return k, 0
    t0 = time.time()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-qp', '12', '-pix_fmt', 'yuv420p', '-threads', '1', '-r', str(FPS),
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
    T = TL(); nf = int(round(T.total * FPS))
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    step = 250
    segs = [(i, f, min(nf, f + step)) for i, f in enumerate(range(0, nf, step))]
    print('frames', nf, 'segs', len(segs), flush=True)
    t0 = time.time()
    with Pool(nproc, maxtasksperchild=4) as pool:
        for k, dt in pool.imap_unordered(render_seg, segs):
            print('seg', k, round(dt, 1), 'elapsed', round(time.time() - t0), flush=True)
    with open(f'{OUT}/list.txt', 'w') as f:
        for k, _, _ in segs: f.write(f"file 'seg_{k:03d}.mp4'\n")
    print('RENDERDONE', round(time.time() - t0), flush=True)
