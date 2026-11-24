"""Parallel frame renderer -> H.264 chunks -> concat.

usage: python3 render.py <tts_meta_dir> <out.mp4> [t0 t1] [--scale 0.5]
"""
import os, sys, json, time, subprocess, math
import multiprocessing as mp
import numpy as np
import cv2
from common import *
import timeline as TL

ARGS = {}


def init_worker(meta_dir, scale):
    global SH, TLD
    import shots as SH_
    SH = SH_
    TLD = TL.build(meta_dir)
    SH.setup(TLD)
    ARGS['scale'] = scale


def render_range(job):
    f0, f1, path = job
    scale = ARGS['scale']
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14',
           '-pix_fmt', 'yuv420p', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    for f in range(f0, f1):
        img = SH.render(f / FPS, f)
        u8 = to_u8(img)
        if scale != 1.0:
            u8 = cv2.resize(u8, (w, h), interpolation=cv2.INTER_AREA)
        p.stdin.write(u8.tobytes())
        if (f - f0) % 150 == 0:
            el = time.time() - t_start
            print(f'[{os.getpid()}] frame {f} ({f - f0}/{f1 - f0}) {el:.0f}s', flush=True)
    p.stdin.close()
    p.wait()
    return path


def main():
    meta_dir = sys.argv[1]
    out = sys.argv[2]
    scale = 1.0
    if '--scale' in sys.argv:
        scale = float(sys.argv[sys.argv.index('--scale') + 1])
    nums = [a for a in sys.argv[3:] if a.replace('.', '', 1).isdigit()]
    tl = TL.build(meta_dir)
    t0, t1 = (float(nums[0]), float(nums[1])) if len(nums) >= 2 else (0.0, tl['total'])
    F0, F1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    nproc = int(os.environ.get('NPROC', '4'))
    tmpd = os.path.join(SCRATCH, 'render_chunks')
    os.makedirs(tmpd, exist_ok=True)
    # interleaved small chunks balance load across uneven scenes
    step = 60
    jobs = []
    for k, a in enumerate(range(F0, F1, step)):
        jobs.append((a, min(F1, a + step), os.path.join(tmpd, f'c{k:05d}.mp4')))
    print(f'rendering {F1 - F0} frames in {len(jobs)} chunks with {nproc} procs', flush=True)
    with mp.get_context('fork').Pool(nproc, initializer=init_worker, initargs=(meta_dir, scale)) as pool:
        paths = list(pool.imap(render_range, jobs))
    lst = os.path.join(tmpd, 'list.txt')
    with open(lst, 'w') as f:
        for pth in paths:
            f.write(f"file '{pth}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
    for pth in paths:
        os.remove(pth)
    print('wrote', out)


if __name__ == '__main__':
    main()
