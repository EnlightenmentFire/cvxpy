# -*- coding: utf-8 -*-
"""时间轴：由逐句配音（已后期处理）的时长生成每句起止、章节卡、字幕块。缺配音时按 4.3 字/秒估算。"""
import os, re, json
from script import BEATS, SECTIONS
PROC = '/tmp/claude-0/work/tts/proc/'
FPS = 25
GAP = 0.50          # 句间停顿（VOICE_SPEC）
QUOTE_HOLD = 0.55   # 引文句后多留一点，让古文卡停住
LEAD = 0.55         # 片头：鼓点先行
CHAP_D = 2.4
END_D = 5.0

def nchar(s): return len(re.sub(r'[^一-鿿0-9A-Za-z]', '', s))

def dur_of(bid):
    p = PROC + bid + '.json'
    if os.path.exists(p): return json.load(open(p))['dur']
    return None

def chunks(text):
    """字幕切块：按标点切，合并到每块 ≤16 字；“”内为引文块。返回 [(文本, 是否引文, 字数)]。"""
    parts = []; cur = ''; q = False
    for ch in text:
        if ch in '“”':
            if nchar(cur): parts.append([cur, q])
            cur = ''; q = (ch == '“'); continue
        cur += ch
        if ch in '，。；：？！':
            if nchar(cur): parts.append([cur, q])
            elif parts: parts[-1][0] += cur
            cur = ''
    if nchar(cur): parts.append([cur, q])
    out = []
    for s, qq in parts:
        s = s.lstrip('，。；： ')
        lim = 15 if qq else 16
        if out and out[-1][1] == qq and nchar(out[-1][0]) + nchar(s) <= lim and out[-1][0].rstrip()[-1] not in '。？！：':
            out[-1][0] += s
        else: out.append([s, qq])
    res = []
    for s, qq in out:
        s2 = s.strip()
        s2 = s2.rstrip('，。；：') if not s2.endswith(('？', '！')) else s2
        res.append((s2, qq, nchar(s)))
    return res

class TL:
    def __init__(self):
        self.s = {}; self.e = {}; self.chap = {}; self.subs = []; self.audio = []
        align = {}
        ap = '/tmp/claude-0/work/tts/align.json'
        if os.path.exists(ap): align = json.load(open(ap))
        t = LEAD; prev = 0
        for b in BEATS:
            sec = b['sec']
            if sec != prev and sec in SECTIONS:
                t += 0.3; self.chap[sec] = (t, t + CHAP_D); t += CHAP_D
            d = dur_of(b['id'])
            real = d is not None
            if d is None: d = nchar(b['say']) / 4.3 + 0.2
            self.s[b['id']] = t; self.e[b['id']] = t + d
            self.audio.append(dict(id=b['id'], t=t, d=d, real=real))
            ch = chunks(b['text']); al = align.get(b['id'])
            tot = sum(max(1, c[2]) + 1.0 for c in ch); acc = 0; first = len(self.subs)
            for i, (s, q, n) in enumerate(ch):
                if al and len(al) == len(ch) and al[i] is not None:
                    c0 = t + max(0.0, al[i] - 0.05)
                else:
                    c0 = t + d * acc / tot
                acc += max(1, n) + 1.0
                self.subs.append([c0, None, s, q, b['id']])
            for j in range(first, len(self.subs)):
                self.subs[j][1] = self.subs[j + 1][0] if j + 1 < len(self.subs) else t + d
            self.subs[-1][1] = t + d + 0.15
            t += d + GAP + (QUOTE_HOLD if '“' in b['text'] else 0.0)
            prev = sec
        t += 1.0
        self.end = (t, t + END_D); self.total = t + END_D
    def S(self, bid, off=0.0): return self.s[bid] + off
    def E(self, bid, off=0.0): return self.e[bid] + off
    def sub_at(self, t):
        for s in self.subs:
            if s[0] <= t < s[1]: return s
        return None

if __name__ == '__main__':
    T = TL(); print('total', round(T.total, 1), 'min', round(T.total / 60, 2))
    for k, v in T.chap.items(): print('chap', k, [round(x, 1) for x in v])
    for b in BEATS: print(b['id'], round(T.s[b['id']], 1), round(T.e[b['id']], 1), '|'.join(c[0] for c in chunks(b['text'])))
