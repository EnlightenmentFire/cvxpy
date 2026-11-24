# -*- coding: utf-8 -*-
"""时间轴：由各段配音时长生成每个 beat 的起止时间、章节卡时间、字幕分块时间。"""
import os, re, json, numpy as np
from script import BEATS, SECTIONS
WAVDIR = '/home/user/work/tts/wav/'
TEMPO = 1.10          # 旁白整体变速（ffmpeg atempo）
GAP = 0.36            # 段间停顿
LEAD = 0.9
TITLE_D = 3.4
CHAP_D = 2.3
END_D = 6.0

def wav_info(bid):
    p = WAVDIR + bid + '.wav'
    if not os.path.exists(p): return None
    import soundfile as sf
    w, sr = sf.read(p, dtype='float32')
    if w.ndim > 1: w = w.mean(1)
    idx = np.where(np.abs(w) > 0.012)[0]
    if len(idx) == 0: return None
    a = max(0, idx[0] - int(0.04 * sr)); b = min(len(w), idx[-1] + int(0.10 * sr))
    le = _QC.get(bid, {}).get('last_end')
    ms = _QC.get(bid, {}).get('miss') or []
    if le and _QC[bid].get('tail') and ms and ms[-1][0] == '': b = min(b, int((le + 0.22) * sr))   # 末尾多出的杂音/赘字裁掉
    return a / sr, b / sr, sr

_QC = json.load(open('/home/user/work/tts/qc.json')) if os.path.exists('/home/user/work/tts/qc.json') else {}
def nchar(s): return len(re.sub(r'[^一-鿿0-9]', '', s))

def chunks(text):
    """把一段旁白切成字幕块：[(文本, 是否引文, 字数)]。按标点切，合并到每块 ≤16 字；引文前的短引导语并入引文块。"""
    parts = []; cur = ''; q = False
    for ch in text:
        if ch in '“”':
            if nchar(cur): parts.append([cur, q])
            elif parts and cur.strip(): parts[-1][0] += cur
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
        if out and out[-1][1] == qq and nchar(out[-1][0]) + nchar(s) <= 16 and out[-1][0][-1] not in '。？！':
            out[-1][0] += s
        elif out and (not out[-1][1]) and qq and nchar(out[-1][0]) <= 6 and nchar(out[-1][0]) + nchar(s) <= 16 and out[-1][0][-1] not in '。？！':
            out[-1] = [out[-1][0].rstrip('：，') + '“' + s, True]      # 短引导语 + 引文
        else: out.append([s, qq])
    res = []
    for s, qq in out:
        s2 = s.strip().rstrip('，。；：')
        if qq and '“' in s2: s2 = s2.replace('“', '：')
        res.append((s2, qq, nchar(s)))
    return res

class TL:
    def __init__(self):
        self.s = {}; self.e = {}; self.chap = {}; self.subs = []; self.audio = []
        align = {}
        if os.path.exists('/home/user/work/tts/align.json'):
            align = json.load(open('/home/user/work/tts/align.json'))
        t = LEAD; prev = None
        for b in BEATS:
            sec = b['sec']
            if prev is not None and sec != prev:
                if prev == 0:
                    self.title = (t + 0.25, t + 0.25 + TITLE_D); t += 0.25 + TITLE_D
                if sec in SECTIONS:
                    self.chap[sec] = (t, t + CHAP_D); t += CHAP_D
                if sec == 7: t += 1.0
            info = wav_info(b['id'])
            if info: a0, a1, sr = info; d = (a1 - a0) / TEMPO
            else: a0 = a1 = None; d = nchar(b['text']) / 4.3 + 0.3
            self.s[b['id']] = t; self.e[b['id']] = t + d
            self.audio.append(dict(id=b['id'], t=t, a0=a0, a1=a1))
            # 字幕
            ch = chunks(b['text']); tot = sum(max(1, c[2]) + 1.2 for c in ch); acc = 0
            al = align.get(b['id'])
            for i, (s, q, n) in enumerate(ch):
                if al and i < len(al) and al[i] is not None and a0 is not None:
                    c0 = t + max(0.0, (al[i] - a0) / TEMPO - 0.06)
                else:
                    c0 = t + d * acc / tot
                acc += max(1, n) + 1.2
                self.subs.append([c0, None, s, q, b['id']])
            for j in range(len(self.subs) - len(ch), len(self.subs)):
                self.subs[j][1] = self.subs[j + 1][0] if j + 1 < len(self.subs) else t + d
            self.subs[-1][1] = t + d + 0.12
            t += d + (0.95 if sec == 7 else GAP)
            prev = sec
        t += 1.3
        self.end = (t, t + END_D); self.total = t + END_D
    def S(self, bid, off=0.0): return self.s[bid] + off
    def E(self, bid, off=0.0): return self.e[bid] + off
    def sec_range(self, sec):
        ids = [b['id'] for b in BEATS if b['sec'] == sec]
        t0 = self.chap[sec][0] if sec in self.chap else self.s[ids[0]]
        return t0, self.e[ids[-1]]
    def beat_at(self, t):
        cur = None
        for b in BEATS:
            if self.s[b['id']] <= t: cur = b
        return cur

if __name__ == '__main__':
    T = TL(); print('total', round(T.total, 1), 'title', T.title, 'end', T.end)
    for k, v in T.chap.items(): print(k, [round(x, 1) for x in v])
    for b in BEATS: print(b['id'], round(T.s[b['id']], 2), round(T.e[b['id']], 2), [c[0] for c in chunks(b['text'])])
