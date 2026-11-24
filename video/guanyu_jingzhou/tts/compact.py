# -*- coding: utf-8 -*-
"""压缩句间过长的停顿：段内静音超过 MAXS 秒的，缩到 MAXS 秒（两侧各留一半并做淡入淡出）。"""
import sys, os, glob, numpy as np, soundfile as sf
MAXS = 0.42
def compact(w, sr):
    fl = int(0.02 * sr); n = len(w) // fl
    rms = np.sqrt(np.mean(w[:n * fl].reshape(n, fl) ** 2, axis=1) + 1e-12)
    thr = max(rms.max() * 10 ** (-38 / 20), 0.004)
    sil = rms < thr; out = []; i = 0; cut = 0.0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            d = (j - i) * fl / sr
            if d > MAXS and i > 0 and j < n:
                k = int(MAXS / 2 * sr); a = w[i * fl:i * fl + k].copy(); b = w[j * fl - k:j * fl].copy()
                f = int(0.01 * sr); a[-f:] *= np.linspace(1, 0, f); b[:f] *= np.linspace(0, 1, f)
                out += [a, b]; cut += d - MAXS
            else: out.append(w[i * fl:j * fl])
            i = j
        else:
            j = i
            while j < n and not sil[j]: j += 1
            out.append(w[i * fl:j * fl]); i = j
    out.append(w[n * fl:])
    return np.concatenate(out), cut
if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True); tot = 0; totd = 0
    for p in sorted(glob.glob(src + '/*.wav')):
        w, sr = sf.read(p, dtype='float32')
        if w.ndim > 1: w = w.mean(1)
        o, cut = compact(w, sr); sf.write(dst + '/' + os.path.basename(p), o, sr); tot += cut; totd += len(o) / sr
    print('removed %.1f s of pauses; total now %.1f s' % (tot, totd))
