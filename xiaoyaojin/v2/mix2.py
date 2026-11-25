# -*- coding: utf-8 -*-
"""混音：旁白 + 音效 (+ 配乐)。配乐在人声下约 -22 dB，高潮段约 -19 dB，无旁白处抬起；整片 -15 LUFS、真峰值 ≤ -1.5 dBTP。
输出 mix_music.wav（有配乐）、mix_nomusic.wav（无配乐，保留音效）。"""
import json, os, re, subprocess, sys
import numpy as np, soundfile as sf

A = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import visuals2 as V
meta = json.load(open(f'{A}/audio_meta.json')); SR = meta['SR']; N = meta['N']
voice, _ = sf.read(f'{A}/voice.wav', dtype='float32')
sfx, _ = sf.read(f'{A}/sfx.wav', dtype='float32')
mus, _ = sf.read(f'{A}/music.wav', dtype='float32')
assert len(voice) == N and len(sfx) == N and len(mus) == N, (len(voice), len(sfx), len(mus), N)


def lufs(x):
    p = f'{A}/_m.wav'; sf.write(p, x, SR, subtype='FLOAT')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
    return I, TP


def db(x): return 10 ** (x / 20)


def smooth(x, sec):
    k = max(1, int(sec * SR)); return np.convolve(x, np.ones(k, np.float32) / k, mode='same').astype(np.float32)


# 说话掩码
env = smooth(np.abs(voice), 0.05)
speak = smooth((env > 0.01).astype(np.float32), 0.5)
speak = np.clip(speak * 1.6, 0, 1)
tl = json.load(open(os.path.join(HERE, 'timeline_yy.json')))
E = np.full(N, 0.4, np.float32)
for sg in tl['segs']:
    if not sg.get('chap'):
        E[int(sg['start'] * SR):int((sg['start'] + sg['dur']) * SR)] = V.energy(sg['i'])
E = smooth(E, 1.0)

Lv, _ = lufs(voice)
Lm, _ = lufs(mus.mean(1))
Ls, _ = lufs(sfx)
print('voice', Lv, 'music', Lm, 'sfx', Ls)
# 配乐增益曲线（dB，相对人声）
rel = -22.0 + 3.0 * np.clip((E - 0.6) / 0.35, 0, 1) + 7.0 * (1 - speak)
outro = np.zeros(N, np.float32); outro[int(meta['VT'] * SR):] = 1.0; outro = smooth(outro, 1.0)
rel = rel + 2.0 * outro
gm = db((Lv - Lm) + rel).astype(np.float32)
music_bus = mus * gm[:, None]
# 音效：人声下约 -17 dB，说话时再压 4 dB
gs = db((Lv - Ls) - 17.0 - 4.0 * speak).astype(np.float32)
sfx_bus = sfx * gs
v2 = np.stack([voice, voice], 1)
mixA = v2 + music_bus + np.stack([sfx_bus, sfx_bus], 1)
mixB = v2 + np.stack([sfx_bus, sfx_bus], 1)


def finish(x, name):
    # 先测响度给增益，再用 ffmpeg alimiter 限峰，迭代到 -15 LUFS ±0.2
    raw = f'{A}/_{name}_raw.wav'; sf.write(raw, x, SR, subtype='FLOAT')
    I0, _ = lufs(x); g = -15.0 - I0
    for it in range(6):
        out = f'{A}/{name}.wav'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                        f'volume={g:.2f}dB,alimiter=limit=0.84:level=false:attack=3:release=60', '-c:a', 'pcm_s24le', out], check=True)
        y, _ = sf.read(out, dtype='float32'); I, TP = lufs(y)
        print(name, 'gain', round(g, 2), 'I', I, 'TP', TP)
        if abs(I + 15.0) <= 0.2: break
        g += (-15.0 - I) * 1.3
    return I, TP


ra = finish(mixA, 'mix_music'); rb = finish(mixB, 'mix_nomusic')
json.dump({'music': ra, 'nomusic': rb, 'Lv': Lv}, open(f'{A}/mix_report.json', 'w'))
print('done')
