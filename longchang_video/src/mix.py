"""混音：旁白 + 配乐。旁白说话时配乐自动让位，空隙里回来。

用法: python mix.py <work> <timeline.json> <music.wav> <out.wav>
"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
work, tlp, musp, outp = sys.argv[1:5]
tl = json.load(open(tlp))
B = tl['beats']
TOTAL = tl['total']
N = int(TOTAL * SR)

# ── 旁白轨 ──
voice = np.zeros(N, np.float32)
for bid, (t0, t1, tn) in B.items():
    y, sr = sf.read(f'{work}/audio/narr48/{bid}.wav', dtype='float32')
    assert sr == SR
    i = int(t0 * SR)
    voice[i:i + len(y)] += y[:max(0, N - i)]
voice = sosfilt(butter(2, 75, btype='high', fs=SR, output='sos'), voice).astype(np.float32)
sf.write(work + '/audio/_voice_raw.wav', voice, SR, subtype='FLOAT')
# 轻压缩，把句与句之间的音量拉齐一点
subprocess.run(stdin=subprocess.DEVNULL, args=['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', work + '/audio/_voice_raw.wav', '-af',
                'acompressor=threshold=-25dB:ratio=2.2:attack=10:release=160:makeup=1.6:knee=6',
                '-c:a', 'pcm_f32le', work + '/audio/_voice_c.wav'], check=True)
voice, _ = sf.read(work + '/audio/_voice_c.wav', dtype='float32')
voice = voice[:N]
# 一点很短的房间感，让人声和配乐坐在同一个空间里
g = np.random.default_rng(5)
n_ir = int(0.5 * SR)
t = np.arange(n_ir) / SR
ir = np.stack([sosfilt(butter(2, [250, 5000], btype='band', fs=SR, output='sos'), g.standard_normal(n_ir)) * 10 ** (-3 * t / 0.42)
               for _ in range(2)], -1)
ir[:int(0.006 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(0)).mean()
vst = np.stack([voice, voice], -1)
wet = np.stack([fftconvolve(voice, ir[:, c])[:N] for c in range(2)], -1)
vst = vst + wet * 0.055

# ── 配乐让位 ──
mus, sr = sf.read(musp, dtype='float32')
assert sr == SR
mus = mus[:N]
if len(mus) < N:
    mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
hop = 480
env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, mode='same')[::hop])
gate = (env > 10 ** (-46 / 20)).astype(np.float32)
# 起得快，放得慢
sm = np.zeros_like(gate)
a_up, a_dn = 1 - np.exp(-1 / (0.18 * SR / hop)), 1 - np.exp(-1 / (0.95 * SR / hop))
v = 0.0
for i, x in enumerate(gate):
    v += (a_up if x > v else a_dn) * (x - v)
    sm[i] = v
sm = np.interp(np.arange(N), np.arange(len(sm)) * hop, sm).astype(np.float32)
tt = np.arange(N) / SR


def bump(a, b, fin=1.5, fout=2.0):
    x = np.clip((tt - a) / fin, 0, 1) * np.clip((b - tt) / fout, 0, 1)
    return x * x * (3 - 2 * x)


feature = np.maximum.reduce([bump(*tl['title']), bump(B['e09'][1] + 0.2, B['e09'][2] + 0.5), bump(B['h08'][1], TOTAL, 2.0, 3.0),
                             bump(0, B['a01'][0] + 0.3, 0.5, 1.0)])
voiced_rms = float(np.sqrt((voice[np.abs(voice) > 1e-3] ** 2).mean()))
mus_rms = float(np.sqrt((mus ** 2).mean()))
UNDER_DB, GAP_DB, FEAT_DB = -15.5, -9.0, -5.0          # 相对旁白响度：说话时 / 空隙 / 片名与收尾
base = voiced_rms / mus_rms
gain_db = GAP_DB + (UNDER_DB - GAP_DB) * sm
gain_db = gain_db + (FEAT_DB - GAP_DB) * feature * (1 - sm)
mgain = base * 10 ** (gain_db / 20)
mix = vst + mus * mgain[:, None]
peak = float(np.abs(mix).max())
print('voice rms %.1f dBFS  music stem rms %.1f dBFS  mix peak %.2f' % (20 * np.log10(voiced_rms), 20 * np.log10(mus_rms), peak))
sf.write(work + '/audio/_mix_pre.wav', mix / max(peak / 0.9, 1.0), SR, subtype='FLOAT')
sf.write(work + '/audio/_music_ducked.wav', (mus * mgain[:, None]) / max(peak / 0.9, 1.0), SR, subtype='FLOAT')
# 响度归一：-16 LUFS，真峰值 -1.5 dB
import re
p = subprocess.run(stdin=subprocess.DEVNULL, args=['ffmpeg', '-nostdin', '-hide_banner', '-i', work + '/audio/_mix_pre.wav', '-af',
                    'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', p.stderr, re.S).group(0))
print('measured', {k: m[k] for k in ('input_i', 'input_tp', 'input_lra')})
gain = -16.0 - float(m['input_i'])
af = f'volume={gain:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled'
subprocess.run(stdin=subprocess.DEVNULL, args=['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', work + '/audio/_mix_pre.wav', '-af', af, '-ar', '48000', '-c:a', 'pcm_s24le', outp], check=True)
p = subprocess.run(stdin=subprocess.DEVNULL, args=['ffmpeg', '-nostdin', '-hide_banner', '-i', outp, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
print(p.stderr[p.stderr.rfind('Summary:'):].strip())
