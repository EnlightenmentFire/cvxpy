"""Render episode 55 video track from script.txt + voice/timeline.json.
python render.py SCRIPT VOICE_DIR OUT.mp4 [--stills t1,t2,...] [--workers 4]
"""
import sys, os, json, re, math, subprocess, argparse
from multiprocessing import Process
import numpy as np, skia
sys.path.insert(0, os.path.dirname(__file__))
from gfx import *
import scenes as S

FPS = 25
VO_OFF = 0.40     # narration starts 0.4 s after the first frame (qing strike at 0)
LEAD = 0.25       # scene starts slightly before its first line
TAIL = 5.0
XF = 0.45
TITLE = '修行几万小时的人，大脑有什么不一样？'
SERIES = '佛法与心智 · 静坐的科学'

META = {  # scene -> (evidence tag, colour, source line)
 'hook_eeg': ('实证 · 小样本 · 有方法争议', S.GOLD, 'Lutz 等，PNAS，2004 · 画面为示意'),
 'hook_gamma': ('实证 · 小样本 · 有方法争议', S.GOLD, 'Lutz 等，PNAS，2004 · 画面为示意'),
 'hook_cortex': ('实证 · 小样本 · 相关', S.GOLD, 'Lazar 等，NeuroReport，2005 · 画面为示意'),
 'lutz_intro': ('实证 · 小样本', S.GOLD, 'Lutz et al., PNAS 101(46):16369–73, 2004'),
 'lutz_method': ('实证 · 小样本', S.GOLD, 'Lutz et al., PNAS, 2004'),
 'lutz_result': ('实证 · 小样本 · 有方法争议', S.GOLD, 'Lutz et al., PNAS, 2004'),
 'lutz_trait': ('相关 · 非因果', S.GOLD, 'Lutz et al., PNAS, 2004 · 散点为示意'),
 'gamma_meaning': ('解释仍有争议', S.RED, '画面为示意'),
 'lutz_caveat': ('小样本 · 横断面', S.RED, 'Lutz et al., PNAS, 2004'),
 'emg': ('方法争议', S.RED, 'Whitham et al., Clin Neurophysiol 2007 · Braboszcz et al., PLOS ONE 2017'),
 'lutz_tag': ('实证 · 小样本 · 有方法争议', S.GOLD, 'Lutz et al., PNAS, 2004'),
 'lazar_intro': ('实证 · 小样本 · 相关', S.GOLD, 'Lazar et al., NeuroReport 16(17):1893–97, 2005'),
 'lazar_people': ('实证 · 小样本 · 相关', S.GOLD, 'Lazar et al., NeuroReport, 2005'),
 'lazar_result': ('实证 · 小样本 · 相关', S.GOLD, 'Lazar et al., NeuroReport, 2005 · 地形图为示意'),
 'lazar_insula': ('实证 · 小样本 · 相关', S.GOLD, 'Lazar et al., NeuroReport, 2005 · 画面为示意'),
 'lazar_age': ('相关 · 非因果', S.GOLD, 'Lazar et al., NeuroReport, 2005 · 曲线为示意'),
 'lazar_caveat': ('小样本 · 横断面', S.RED, 'Lazar et al., NeuroReport, 2005'),
 'plastic': ('实证 · 纵向', '#2f6b4f', 'Draganski et al., Nature 427:311–12, 2004 · 柱图为示意'),
 'holzel': ('初步线索 · 非随机', S.GOLD, 'Hölzel et al., Psychiatry Res Neuroimaging 191(1):36–43, 2011'),
 'kral': ('随机对照 · 阴性结果', '#2f6b4f', 'Kral et al., Science Advances 8(20):eabk3316, 2022'),
 'vandam': ('方法批评', S.RED, 'Van Dam et al., Perspect Psychol Sci 13(1):36–61, 2018'),
 'honest': ('元分析 · 有发表偏倚', S.GOLD, 'Fox et al., Neurosci Biobehav Rev 43:48–73, 2014'),
 'altered': ('二手 · 作者自评', S.GOLD, 'Goleman & Davidson, Altered Traits, Avery, 2017'),
 'states': ('二手 · 作者自评', S.GOLD, 'Goleman & Davidson, Altered Traits, 2017'),
 'tanjing': ('经典原文', S.RED, '《六祖坛经·定慧品》宗宝本'),
 'analogy': ('印照 · 类比 · 非证明', S.RED, ''),
}

def load_plan(script, voice):
    tl = json.load(open(os.path.join(voice, 'timeline.json')))
    tags, cur = [], None
    for l in open(script):
        l = l.strip()
        if not l: continue
        if l.startswith('##'): cur = l[2:].strip(); continue
        tags.append(cur)
    assert len(tags) == len(tl), (len(tags), len(tl))
    for e, g in zip(tl, tags):
        e['scene'] = g; e['start'] += VO_OFF; e['end'] += VO_OFF
    scenes = []
    for e in tl:
        if not scenes or scenes[-1]['id'] != e['scene']:
            scenes.append({'id': e['scene'], 'start': 0.0 if not scenes else e['start'] - LEAD, 'lines': []})
        scenes[-1]['lines'].append(e)
    total = tl[-1]['end'] + TAIL
    for i, s in enumerate(scenes):
        s['end'] = scenes[i + 1]['start'] if i + 1 < len(scenes) else total
    return tl, scenes, total

# ---------- subtitles ----------
def split_pages(text, maxc=17):
    clauses = re.findall(r'[^，。；：？！、]+[，。；：？！、]?', text)
    pages, cur = [], []
    def flush():
        if cur: pages.append(cur.copy()); cur.clear()
    for cl in clauses:
        while len(cl) > maxc:  # hard split long clause
            cur.append(cl[:maxc]); cl = cl[maxc:]
            if len(cur) == 2: flush()
        if cur and len(cur[-1]) + len(cl) <= maxc:
            cur[-1] += cl
        else:
            cur.append(cl)
        if len(cur) == 2: flush()
    flush()
    # merge single short trailing page into previous if fits
    clean = lambda s: s.rstrip('，。；、：')
    return [[clean(x) for x in p if clean(x)] for p in pages if any(clean(x) for x in p)]

def sub_events(tl):
    ev = []
    for e in tl:
        pages = split_pages(e['text'])
        n = sum(sum(len(x) for x in p) for p in pages)
        t = e['start']; dur = e['end'] - e['start']
        for p in pages:
            k = sum(len(x) for x in p) / n
            ev.append((t, t + dur * k, p)); t += dur * k
    ev[0] = (0.0,) + ev[0][1:]   # first subtitle on the very first frame
    return ev

def draw_subs(c, t, ev):
    for (a, b, p) in ev:
        if a - 0.02 <= t < b + 0.12:
            y0 = 1590 if len(p) == 1 else 1555
            for i, l in enumerate(p):
                text(c, l, W / 2, y0 + i * 74, 56, 'sans_b', '#ffffff', 1.0, shadow=('#000000', 0.55, 0, 0, 4), stroke=('#14100c', 0.9, 7))
            return

def draw_overlay(c, t, sc):
    # header band
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 285), paint('#15120f', 0.86))
    c.drawLine(0, 285, W, 285, paint(S.GOLD, 0.7, stroke=2))
    text(c, SERIES, W / 2, 98, 32, 'sans', '#c9b48a', 0.95, spacing=3)
    text(c, TITLE, W / 2, 205, 56, 'serif_k', '#f6efe2', 1.0)
    # AI badge
    rrect(c, W - 150, 26, 124, 44, 10, paint('#000000', 0.35))
    text(c, 'AI 配音', W - 88, 57, 26, 'sans', '#e8dcc6', 0.9)
    m = META.get(sc['id'])
    if m:
        tag, col, src = m
        chip(c, tag, W / 2, 1715, 30, '#fff8ec', col, 0.92)
        if src:
            text(c, src, W / 2, 1830, 25, 'sans', '#ffffff', 0.85, shadow=('#000000', 0.7, 0, 0, 2))

def frame(c, t, scenes, ev):
    idx = max(i for i, s in enumerate(scenes) if s['start'] <= t or i == 0)
    sc = scenes[idx]
    def render_scene(s, tt):
        L = [e['start'] - s['start'] for e in s['lines']]
        S.SCENES[s['id']](c, tt - s['start'], s['end'] - s['start'], L)
    c.clear(skia.ColorBLACK)
    if idx > 0 and t - sc['start'] < XF:
        k = smooth((t - sc['start']) / XF)
        render_scene(scenes[idx - 1], t)
        c.saveLayerAlpha(None, int(255 * k)); render_scene(sc, t); c.restore()
    else:
        render_scene(sc, t)
    # bottom gradient for subtitle legibility
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 1460), (0, 1920)], [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(150, 0, 0, 0)]))
    c.drawRect(skia.Rect.MakeXYWH(0, 1460, W, 460), p)
    draw_overlay(c, t, sc)
    draw_subs(c, t, ev)
    # end fade
    total = scenes[-1]['end']
    if t > total - 1.2:
        c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint('#000000', smooth((t - (total - 1.2)) / 1.2)))

def worker(k, f0, f1, plan, out):
    tl, scenes, total = plan; ev = sub_events(tl)
    surf = skia.Surface(W, H); c = surf.getCanvas()
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '1000k', '-bufsize', '2000k',
                           '-pix_fmt', 'yuv420p', '-g', '50', '-threads', '2', out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        frame(c, fi / FPS, scenes, ev)
        ff.stdin.write(surf.toarray().tobytes())
        if (fi - f0) % 500 == 0: print(f'[w{k}] {fi - f0}/{f1 - f0}', flush=True)
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    ap_ = argparse.ArgumentParser(); ap_.add_argument('script'); ap_.add_argument('voice'); ap_.add_argument('out')
    ap_.add_argument('--stills', default=''); ap_.add_argument('--workers', type=int, default=4)
    a = ap_.parse_args()
    plan = load_plan(a.script, a.voice)
    tl, scenes, total = plan
    json.dump({'total': total, 'vo_offset': VO_OFF, 'scenes': [{k: s[k] for k in ('id', 'start', 'end')} for s in scenes]},
              open(os.path.splitext(a.out)[0] + '_plan.json', 'w'), ensure_ascii=False, indent=1)
    if a.stills:
        ev = sub_events(tl); surf = skia.Surface(W, H); c = surf.getCanvas()
        for ts in a.stills.split(','):
            if ts.startswith('@'):  # scene id (+offset)
                sid, _, off = ts[1:].partition('+'); s = next(x for x in scenes if x['id'] == sid); o = float(off or 1.5); tt = s['start'] + o if o >= 0 else s['end'] + o
            else: tt = float(ts)
            frame(c, tt, scenes, ev)
            fn = f"{os.path.splitext(a.out)[0]}_{ts.replace('@', '').replace('+', '_')}.png"
            surf.makeImageSnapshot().save(fn); print(fn)
        sys.exit(0)
    nf = int(math.ceil(total * FPS)); n = a.workers
    bounds = [nf * i // n for i in range(n + 1)]
    parts = [f'{a.out}.part{i}.mp4' for i in range(n)]
    ps = [Process(target=worker, args=(i, bounds[i], bounds[i + 1], plan, parts[i])) for i in range(n)]
    [p.start() for p in ps]; [p.join() for p in ps]
    lst = a.out + '.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', a.out], check=True)
    for p in parts: os.remove(p)
    os.remove(lst)
    print('frames', nf, 'duration', total)
