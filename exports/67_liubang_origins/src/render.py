# -*- coding: utf-8 -*-
"""按 timeline.json 渲染整片画面。用法：
  python render.py voice/timeline.json frames  t1 t2 ...   # 抽帧预览 PNG
  python render.py voice/timeline.json video out.mp4 [workers]
"""
import json, os, sys, subprocess, time, math
from multiprocessing import Process
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eng import *
import scenes as SC
from script import SCENES

TL = json.load(open(sys.argv[1]))
LINES = TL['lines']; SCN = TL['scenes']; TOTAL = TL['total']
PARAMS = {s['id']: dict(s.get('params', {}), _id=s['id']) for s in SCENES}
for s in SCN:
    s['L'] = [l['start'] - s['vstart'] for l in LINES if l['scene'] == s['id']]

CACHE = {}


def sub_img(text):
    fo = font('black', 50); tot = fo.getlength(text)
    n = len(wrap(text, 50, 'black', 960))
    mw = 960 if n == 1 else min(960, tot / n + 60)
    return block(text, 50, 'black', WHITE, mw, 1.35, 'c', 3, 0)


@lru_cache(4)
def corner():
    im = Image.new('RGBA', (W, 200), (0, 0, 0, 0))
    a = txt('乱世起家录｜序章', 30, 'serifsc', (220, 200, 160), 2)
    b = txt('AI 配音', 26, 'sans', (200, 200, 200), 2)
    im.alpha_composite(a, (40, 92)); im.alpha_composite(b, (W - 40 - b.width, 96))
    return im


def frame(gt):
    k = 0
    while k + 1 < len(SCN) and gt >= SCN[k + 1]['vstart']: k += 1
    s = SCN[k]
    t = gt - s['vstart']; T = s['vend'] - s['vstart']
    cv = Image.new('RGBA', (W, H), INK + (255,))
    C = CACHE.setdefault(s['id'], {})
    SC.KINDS[s['kind']](cv, t, T, s['L'], PARAMS[s['id']], C)
    # 转场：场首 0.3s 由暗转明；标题场金光一闪
    if k > 0 and t < 0.32:
        a = 1 - ease(t / 0.32)
        if s['kind'] == 'title':
            cv.alpha_composite(Image.new('RGBA', (W, H), (255, 220, 160, int(150 * a))))
        else:
            cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(230 * a))))
    if T - t < 0.18 and k + 1 < len(SCN):
        a = ease(1 - (T - t) / 0.18)
        cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(200 * a))))
    cv.alpha_composite(vignette(0.8))
    # 字幕
    for i, l in enumerate(LINES):
        nxt = LINES[i + 1]['start'] if i + 1 < len(LINES) else 1e9
        e = min(l['end'] + 0.3, nxt - 0.02)
        if l['start'] - 0.04 <= gt < e:
            im = sub_img(l['text'])
            a = appear(gt, l['start'] - 0.04, 0.12)
            bg = rrect((im.width + 60, im.height + 30), 12, (0, 0, 0, 150))
            put(cv, bg, W / 2, SC.SUBY, a)
            put(cv, im, W / 2, SC.SUBY, a)
            break
    cv.alpha_composite(corner())
    return cv.convert('RGB')


def run_chunk(f0, f1, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-g', '50', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        im = frame(f / FPS)
        p.stdin.write(im.tobytes())
        if (f - f0) % 250 == 0:
            print(out, f - f0, '/', f1 - f0, round(time.time() - t0), 's', flush=True)
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'frames':
        PD = os.environ.get('PREV', 'preview'); os.makedirs(PD, exist_ok=True)
        for x in sys.argv[3:]:
            if x.startswith('@'):   # @场景id[:偏移]
                sid, _, off = x[1:].partition(':')
                s = next(s for s in SCN if s['id'] == sid)
                gt = s['vstart'] + (float(off) if off else (s['vend'] - s['vstart']) * 0.7)
            else:
                gt = float(x)
            t0 = time.time(); im = frame(gt)
            fn = f'{PD}/f_{gt:07.2f}.png'; im.save(fn); print(fn, round(time.time() - t0, 2), 's')
    else:
        out = sys.argv[3]; nw = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        nf = int(math.ceil(TOTAL * FPS))
        # 按场景边界大致均分
        bounds = [int(nf * k / nw) for k in range(nw + 1)]
        ps = []
        for k in range(nw):
            p = Process(target=run_chunk, args=(bounds[k], bounds[k + 1], f'chunk_{k}.mp4')); p.start(); ps.append(p)
        for p in ps: p.join()
        with open('chunks.txt', 'w') as f:
            for k in range(nw): f.write(f"file 'chunk_{k}.mp4'\n")
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'chunks.txt', '-c', 'copy', out])
        print('done', out)
