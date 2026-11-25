# -*- coding: utf-8 -*-
"""原始合成句 → 成品句：裁头尾静音、句内停顿压到 ≤0.38 s、rubberband R3 保共振峰变速、50 Hz 高通、语音段 RMS 归一。
usage: python voice_post.py [ids...]   （TEMPO 环境变量可覆盖全局变速）
"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines

W = os.environ.get('WORK', '/home/user/work')
RAW, OUT = f'{W}/tts/raw', f'{W}/tts/proc'
SR = 48000
TEMPO = float(os.environ.get('TEMPO', 1.18))
MAX_PAUSE = 0.38
TARGET_RMS_DB = -18.0


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    voiced = db > max(db.max() - 42, -60)
    if not voiced.any(): return x
    i0 = max(0, np.argmax(voiced) - 2); i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out = []; maxf = int(MAX_PAUSE / 0.02); k = i0
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]: j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.01 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, sr, factor):
    if abs(factor - 1) < 1e-3: return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'a.wav'), os.path.join(d, 'b.wav')
        sf.write(a, x, sr, subtype='FLOAT')
        subprocess.run(['rubberband', '-3', '-F', '-T', f'{factor}', a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d, tmp=None):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, TEMPO if tmp is None else tmp)
    x = sosfiltfilt(butter(4, 50, 'highpass', fs=SR, output='sos'), x).astype(np.float32)
    db, n = frame_db(x, SR); v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95: x = x * 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype='PCM_24')
    nch = len(re.sub(r'[，。？！：；、“”《》\s]', '', d['say']))
    return dict(id=d['id'], dur=len(x) / SR, cps=nch / (len(x) / SR))


if __name__ == '__main__':
    ids = sys.argv[1:]
    for d in all_lines():
        if (not ids or d['id'] in ids) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            r = process(d); print(f"{r['id']} {r['dur']:.2f}s {r['cps']:.2f} cps")
