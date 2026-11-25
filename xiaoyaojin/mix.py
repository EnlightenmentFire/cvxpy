# 按 timeline.json 拼接旁白，并叠加少量合成音效（不含配乐）。
# 输出 48kHz 立体声 wav；响度在 make.sh 里用 ffmpeg loudnorm 双遍校正。
import json, os, sys
import numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import S

SR = 48000
tl = json.load(open(os.path.join(HERE, 'timeline.json')))
N = int((tl['total'] + 0.5) * SR)
voice = np.zeros(N, np.float32)
sfx = np.zeros(N, np.float32)
rng = np.random.default_rng(1)

for sg in tl['segs']:
    if sg.get('chap'):
        continue
    a, sr = sf.read(sg['file'], dtype='float32')
    a = resample_poly(a, 2, 1).astype(np.float32)  # 24k → 48k
    i0 = int(sg['start'] * SR)
    voice[i0:i0 + len(a)] += a[:N - i0]


def boom(level=0.5, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    f = 38 + 34 * np.exp(-t * 5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 2.6)
    n = rng.standard_normal(len(t)) * np.exp(-t * 40)
    sos = butter(2, 900, 'lowpass', fs=SR, output='sos')
    y = y + 0.35 * sosfilt(sos, n)
    return (level * y / np.max(np.abs(y))).astype(np.float32)


def whoosh(level=0.25, dur=0.9, rise=True):
    t = np.arange(int(dur * SR)) / SR
    n = rng.standard_normal(len(t))
    env = (t / dur) ** 2 if rise else np.sin(np.pi * t / dur) ** 2
    out = np.zeros_like(n)
    # 逐段带通，中心频率上扬
    seg = 2400
    for k in range(0, len(n), seg):
        fc = 400 + 2600 * (k / len(n))
        sos = butter(2, [fc * 0.6, fc * 1.6], 'bandpass', fs=SR, output='sos')
        out[k:k + seg] = sosfilt(sos, n[k:k + seg])
    y = out * env
    return (level * y / (np.max(np.abs(y)) + 1e-9)).astype(np.float32)


def put(sig, t):
    i0 = int(t * SR)
    if i0 >= N:
        return
    seg = sig[:N - i0]
    sfx[i0:i0 + len(seg)] += seg


# 片头：第一秒即有推进感
put(whoosh(0.22, 0.45), 0.0)
put(boom(0.55), 0.05)
for sg in tl['segs']:
    v = S[sg['i']]['v'][0]
    if sg.get('chap'):
        put(whoosh(0.18, 0.7), max(0, sg['start'] - 0.55))
        put(boom(0.45), sg['start'])
    elif v == 'title':
        put(boom(0.5), sg['start'])
    elif v == 'letter' and S[sg['i']]['v'][1].get('mode') == 'final':
        put(boom(0.32, 2.4), sg['start'])
    elif v == 'battle' and S[sg['i']]['v'][1].get('p', (0, 0))[0] in (0.4, 0.9):
        put(boom(0.28, 1.0), sg['start'] + 0.3)

# 旁白处 SFX 压低（ducking）
env = np.abs(voice)
k = int(0.05 * SR)
env = np.convolve(env, np.ones(k) / k, mode='same')
duck = 1.0 - 0.55 * np.clip(env / 0.05, 0, 1)
mix = voice + sfx * duck
mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.89
st = np.stack([mix, mix], axis=1)
out = sys.argv[1]
sf.write(out, st, SR, subtype='PCM_16')
print('wrote', out, len(mix) / SR)
