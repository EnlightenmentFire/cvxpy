# -*- coding: utf-8 -*-
"""约 1 分钟样音：冷启动（悬赏令）+ 伍段（劝降与“关西男子”），用指定的逐句音频 + 同一版配乐。
人声统一到约 -18 dBFS RMS，音乐在人声下自动压低。用法：python tools/excerpt.py lines_dir 输出名.mp3"""
import sys, os, re, subprocess, numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from script import L
from sound import *
LD, NAME = sys.argv[1], sys.argv[2]
PARTS = [list(range(0, 5)), list(range(39, 49))]
segs = []; t = 1.3; starts = {}
for pi, part in enumerate(PARTS):
    if pi: t += 1.3
    for i in part:
        a, sr = sf.read(os.path.join(LD, f'{i:03d}.wav')); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
        if L[i][1] == 'q': t += 0.12
        starts[i] = t; segs.append((t, a)); t += len(a) / SR
        t += 0.35 if L[i][1] == 'q' else (0.22 if L[i][2][-1] in '。？！' else 0.08)
total = t + 2.5; N = int(total * SR)
nar = np.zeros(N)
for st, a in segs: i = int(st * SR); nar[i:i + len(a)] += a[:N - i]
nar = fft_filter(nar, 50, None, 4)
w = int(0.03 * SR); e = np.sqrt(np.convolve(nar ** 2, np.ones(w) / w, 'same')) + 1e-6
g = np.where(e > 0.09 * np.abs(nar).max(), (0.09 * np.abs(nar).max() / e) ** 0.4, 1.0); nar = nar * np.convolve(g, np.ones(w) / w, 'same')
w2 = int(0.05 * SR); en = np.sqrt(np.convolve(nar ** 2, np.ones(w2) / w2, 'same')); act = en > en.max() * 0.05
nar = nar * (10 ** (-18 / 20) / np.sqrt((nar[act] ** 2).mean()))
dry = np.zeros((N, 2)); perc = np.zeros((N, 2)); fx = np.zeros((N, 2)); amb = np.zeros((N, 2))
b0 = starts[39] - 1.3
dr = drone(total); dry[:, 0] += dr * 0.13; dry[:, 1] += dr * 0.13
for t0, nm, d in ((0.0, 'Dm', 9.5), (8.5, 'Bb', 7.5), (15.0, 'Gm', 6.5), (21.0, 'Asus', b0 - 21 + 1.5)):
    add(dry, strings([NOTE(s - 12) for s in CH[nm]], d, 800, 1.8, 1.6), t0, 0.9)
tt = b0; k = 0
while tt < total - 2:
    add(dry, strings([NOTE(s - 12) for s in CH[['Dm', 'Gm', 'Dsus', 'F', 'C', 'Dm'][k % 6]]], 9 + 2.6, 650, 1.6, 1.8), tt - 0.8, 0.5); tt += 9; k += 1
for tt in np.arange(1.0, starts[2] - 0.3, 2.4): add(perc, taiko(56, 1.4, 0.8), tt, 0.38)
add(perc, taiko(50, 2.2, 1.2), starts[2] - 0.12, 0.85)
add(perc, taiko(52, 2.2, 1.1), b0 + 0.2, 0.9)
add(perc, taiko(46, 3.0, 1.0), starts[43] - 0.1, 0.85); add(perc, taiko(46, 3.0, 1.0), starts[47] - 0.1, 0.85)
add(fx, arrow_fly(0.6), 0.28, 0.95, -0.6); add(fx, thunk(), 0.88, 1.0, 0.1); add(fx, paper(1.2), 1.15, 0.7)
add(fx, arrow_fly(0.6)[::-1].copy() * 0.5 + arrow_fly(0.6) * 0.5, starts[3] + 0.8, 0.9, -0.5)
add(amb, wind(total, 1.0, 0.1), 0, 1.0)
mus = reverb(dry, 3.0, 0.45) + reverb(perc, 2.0, 0.28) * 0.95 + reverb(fx, 1.2, 0.18) * 0.8
mus /= np.abs(mus).max() + 1e-9; amb /= np.abs(amb).max() + 1e-9
gate = (en > en.max() * 0.05).astype(float); k = int(0.45 * SR); gate = np.clip(np.convolve(gate, np.ones(k) / k, 'same') * 2.2, 0, 1)
mus = mus * (0.66 - 0.42 * gate)[:, None] + amb * (0.22 - 0.08 * gate)[:, None]
mrms = np.sqrt((mus[~act] ** 2).mean()); mus = mus * (10 ** (-24 / 20) / mrms)
fade = np.minimum(np.arange(N) / (0.3 * SR), 1) * np.minimum((N - np.arange(N)) / (2.0 * SR), 1); mus *= fade[:, None]
mix = mus + nar[:, None]; lim = 10 ** (-1 / 20)
if np.abs(mix).max() > lim: mix = np.tanh(mix / lim * 0.98) * lim
wav = os.path.join(ROOT, 'cache', 'excerpt.wav'); sf.write(wav, mix, SR, subtype='PCM_16')
out = os.path.join(ROOT, 'out', 'samples', NAME); subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-b:a', '192k', out], check=True)
db = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
print(NAME, 'dur %.1fs' % total, 'voice RMS %.1f dBFS' % db(nar[act]), 'music(no voice) %.1f dBFS' % db(mus[~act]))
