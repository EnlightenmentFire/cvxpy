# -*- coding: utf-8 -*-
"""由旁白稿 + 每句音频时长生成时间轴 timeline.json。
没有音频时按字数估算（用于先出静帧）。"""
import json, os, re, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, SECTIONS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
CARD = 2.0        # 章节卡时长
TITLE = 4.0       # 片名卡
ENDCARD = 7.0
HAN = re.compile(r'[一-鿿〇]')


def est(text, kind):
    n = len(HAN.findall(text)); p = len(re.findall(r'[，。；：？！、—…]', text))
    return n / (4.2 if kind == 'q' else 4.9) + p * 0.16


def wav_dur(p):
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def chunks(text, maxlen=17):
    """按标点切成字幕块：先按句号类切句，句内再按逗号切；尽量不在顿号处断开。"""
    n = lambda x: len(HAN.findall(x))
    sents = [p for p in re.split(r'(?<=[。；：？！…])|(?<=——)', text) if p and n(p)]
    res = []
    for st in sents:
        if n(st) <= maxlen: res.append(st); continue
        parts = [p for p in re.split(r'(?<=[，])', st) if p]; cur = ''
        for p in parts:
            if n(cur + p) <= maxlen: cur += p
            else:
                if cur: res.append(cur)
                cur = p
        if cur: res.append(cur)
    # 仍超长的在顿号处或硬切
    out = []
    for c in res:
        while n(c) > maxlen + 3:
            k = c.rfind('、', 0, maxlen); k = k + 1 if k > 5 else maxlen
            out.append(c[:k]); c = c[k:]
        out.append(c)
    # 合并相邻短块
    mg = []
    for c in out:
        if mg and n(mg[-1]) + n(c) <= 15 and n(c) <= 9 and n(mg[-1]) <= 9: mg[-1] += c
        else: mg.append(c)
    return mg


def weight(c):
    return len(HAN.findall(c)) + 0.8 * len(re.findall(r'[，；：、]', c)) + 1.4 * len(re.findall(r'[。？！…—]', c))


def pauses(p):
    """返回音频内的停顿中点（秒）。"""
    import numpy as np
    with wave.open(p) as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    win = int(sr * 0.02); n = len(a) // win; e = np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(1)); q = e < max(0.008, e.max() * 0.04)
    out = []; i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            if (j - i) * 0.02 >= 0.09 and i > 3 and j < n - 3: out.append(((i + j) / 2 * 0.02, (j - i) * 0.02))
            i = j
        else: i += 1
    return out


def main():
    adir = f"{ROOT}/audio/lines"
    t = 1.2
    lines, secs = [], {}
    cur = None
    for i, l in enumerate(L):
        sec, kind, text = l[0], l[1], l[2]
        src = l[3] if len(l) > 3 else ''
        if sec != cur:
            if cur is not None:
                secs[cur]['end'] = t
            meta = [s for s in SECTIONS if s[0] == sec][0]
            secs[sec] = dict(start=t, num=meta[1], title=meta[2])
            if sec == 's1':
                secs['title'] = dict(start=t, end=t + TITLE); t += TITLE
                secs[sec]['start'] = t
            if meta[2]:
                secs[sec]['card'] = [t, t + CARD]; t += CARD
            elif sec in ('s11', 's12'):
                t += 1.3
            secs[sec]['body'] = t
            cur = sec; k = 0
        p = f"{adir}/{i:03d}.wav"
        d = wav_dur(p) if os.path.exists(p) else est(text, kind)
        if kind == 'q': t += 0.12
        st, en = t, t + d
        cs = chunks(text) if kind == 'n' else [text]
        ws = [weight(c) for c in cs]; tot = sum(ws); acc = 0; cl = []
        bounds = [0.0]
        ps = pauses(p) if os.path.exists(p) and len(cs) > 1 else []
        for c, w in zip(cs[:-1], ws[:-1]):
            acc += w; guess = d * acc / tot
            cand = [x for x in ps if abs(x[0] - guess) < 0.9 and x[0] > bounds[-1] + 0.4]
            bounds.append(min(cand, key=lambda x: abs(x[0] - guess) - x[1])[0] if cand else guess)
        bounds.append(d)
        for c, b0, b1 in zip(cs, bounds[:-1], bounds[1:]):
            cl.append(dict(text=c.strip(), start=st + b0, end=st + b1))
        lines.append(dict(i=i, sec=sec, k=k, kind=kind, text=text, src=src, start=round(st, 3), end=round(en, 3), chunks=cl))
        k += 1
        gap = 0.3 if kind == 'q' else (0.22 if text[-1] in '。？！' else 0.06)
        # 语气停顿：收尾三句、关键句
        if sec == 's12': gap = 1.0
        if text.endswith('，') or text.endswith('：'): gap = min(gap, 0.10)
        t = en + gap
    secs[cur]['end'] = t + 0.8
    t += 0.8
    secs['end'] = dict(start=t, end=t + ENDCARD)
    total = t + ENDCARD
    json.dump(dict(fps=FPS, total=round(total, 3), lines=lines, secs=secs), open(f"{ROOT}/src/timeline.json", "w"), ensure_ascii=False, indent=1)
    print("total %.1fs (%d:%02d)" % (total, total // 60, total % 60), {k: round(v['start'], 1) for k, v in secs.items()})


if __name__ == "__main__":
    main()
