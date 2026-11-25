# -*- coding: utf-8 -*-
"""时间轴：按成品配音时长排每句起止、场景区间、字幕分块（有 ASR 对齐时按对齐切分）。"""
import os, re, json
from script import all_lines

W = os.environ.get('WORK', '/home/user/work')
PROC = f'{W}/tts/proc'
FPS = 25
LEAD = 0.55          # 片头：声音钩子先响半秒，旁白随即进入
TAIL = 3.2


def nch(s): return len(re.sub(r'[^一-鿿0-9A-Za-z]', '', s))


def wav_dur(i):
    p = f'{PROC}/{i}.wav'
    if not os.path.exists(p): return None
    import soundfile as sf
    return sf.info(p).duration


def chunks(s, maxn=17):
    """按标点切字幕块，每块 ≤maxn 字；句末标点去掉，书名号保留。"""
    parts = []; cur = ''
    for ch in s:
        cur += ch
        if ch in '，。；：？！、':
            parts.append(cur); cur = ''
    if cur.strip(): parts.append(cur)
    out = []
    for p in parts:
        if out and nch(out[-1]) + nch(p) <= maxn and out[-1][-1] not in '。？！：':
            out[-1] += p
        else:
            out.append(p)
    res = []
    for p in out:
        p = p.strip()
        while nch(p) > maxn + 4:      # 过长：按字数硬切
            k = maxn
            res.append(p[:k]); p = p[k:]
        res.append(p)
    return [r.rstrip('，。；：、') for r in res if nch(r)]


class TL:
    def __init__(self):
        self.L = all_lines()
        al = json.load(open(f'{W}/tts/align.json')) if os.path.exists(f'{W}/tts/align.json') else {}
        self.s, self.e, self.d = {}, {}, {}
        self.subs = []
        t = LEAD
        for d in self.L:
            dur = wav_dur(d['id'])
            if dur is None: dur = nch(d['say']) / 4.45 + 0.15
            self.s[d['id']] = t; self.e[d['id']] = t + dur; self.d[d['id']] = dur
            if not d['nosub']:
                ch = chunks(d['sub'])
                a = al.get(d['id'])          # 每块起点（相对句首秒）
                tot = sum(nch(x) + 1.0 for x in ch); acc = 0.0
                for k, x in enumerate(ch):
                    if a and len(a) == len(ch):
                        c0 = t + a[k]
                    else:
                        c0 = t + dur * acc / tot
                    acc += nch(x) + 1.0
                    self.subs.append([c0, None, x, d['id']])
                for j in range(len(self.subs) - len(ch), len(self.subs)):
                    self.subs[j][1] = self.subs[j + 1][0] if j + 1 < len(self.subs) else t + dur + 0.15
            t += dur + d['gap']
        self.total = t + TAIL
        # 场景区间：自本场景首句起，到下一场景首句前
        self.sc = {}
        order = []
        for d in self.L:
            if d['sc'] not in self.sc:
                self.sc[d['sc']] = [self.s[d['id']], None]; order.append(d['sc'])
        for i, k in enumerate(order):
            self.sc[k][1] = self.sc[order[i + 1]][0] if i + 1 < len(order) else self.total
        self.sc[order[0]][0] = 0.0
        self.order = order

    def S(self, i, off=0.0): return self.s[i] + off
    def E(self, i, off=0.0): return self.e[i] + off
    def SC(self, k): return self.sc[k]


if __name__ == '__main__':
    T = TL()
    print('total', round(T.total, 1), 's =', round(T.total / 60, 2), 'min')
    for k in T.order: print(k, [round(x, 1) for x in T.sc[k]])
