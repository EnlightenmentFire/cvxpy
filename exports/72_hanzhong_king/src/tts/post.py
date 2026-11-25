"""旁白后期：48 kHz、去首尾静音、句内停顿压到 ≤0.40 s、rubberband 变速（保音高共振峰）、50 Hz 高通、统一语音 RMS。
写 proc/{id}.wav 与 proc/{id}.json（dur）。"""
import sys, os, json, subprocess, re, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, '/tmp/claude-0/work/vid')
from script import BEATS
RAW = '/tmp/claude-0/work/tts/raw'; OUT = '/tmp/claude-0/work/tts/proc'; os.makedirs(OUT, exist_ok=True)
SR = 48000; TEMPO = float(os.environ.get('TEMPO', 1.15)); MAXP = 0.40; RMS_DB = -19.0

def fdb(x, n):
    m = len(x) // n; fr = x[:m * n].reshape(m, n); return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
def trim_cap(x):
    n = int(0.02 * SR); db = fdb(x, n); thr = max(db.max() - 40, -58); v = db > thr
    if not v.any(): return x
    i0 = max(0, np.argmax(v) - 2); i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 3)
    out = []; k = i0; mx = int(MAXP / 0.02)
    while k < i1:
        if not v[k]:
            j = k
            while j < i1 and not v[j]: j += 1
            L = j - k; keep = min(L, mx); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out); f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y
def proc(b):
    x, sr = sf.read(f"{RAW}/{b['id']}.wav", dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_cap(x)
    a, o = f'/tmp/claude-0/work/tts/_a.wav', f'/tmp/claude-0/work/tts/_b.wav'
    sf.write(a, x, SR, subtype='FLOAT')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a, '-af', f'rubberband=tempo={TEMPO}:formant=preserved:pitchq=quality,highpass=f=50', '-ar', str(SR), o], check=True)
    y, _ = sf.read(o, dtype='float32')
    n = int(0.02 * SR); db = fdb(y, n); v = db > db.max() - 32
    fr = y[:len(db) * n].reshape(len(db), n)[v]; r = np.sqrt((fr ** 2).mean())
    y = y * (10 ** (RMS_DB / 20) / (r + 1e-9)); pk = np.abs(y).max()
    if pk > 0.9: y *= 0.9 / pk
    sf.write(f"{OUT}/{b['id']}.wav", y, SR, subtype='PCM_24')
    d = len(y) / SR; nc = len(re.sub(r'[^一-鿿0-9]', '', b['say']))
    json.dump(dict(id=b['id'], dur=round(d, 3), cps=round(nc / d, 2), tempo=TEMPO), open(f"{OUT}/{b['id']}.json", 'w'))
    return d, nc
if __name__ == '__main__':
    only = sys.argv[1:]; td = tc = 0
    for b in BEATS:
        if only and b['id'] not in only: continue
        if not os.path.exists(f"{RAW}/{b['id']}.wav"): continue
        d, nc = proc(b); td += d; tc += nc
    print('speech', round(td, 1), 's chars', tc, 'cps', round(tc / max(td, 1), 2))
