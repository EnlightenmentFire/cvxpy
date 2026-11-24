"""配音整理：裁首尾静音、统一响度、整体小幅提速（不变调）、升到 48 kHz。

用法: python prep_narr.py <work> <tempo>
产出: <work>/audio/narr48/<id>.wav
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from narration import BEATS

work, tempo = sys.argv[1], float(sys.argv[2])
src, dst = work + '/audio/narr', work + '/audio/narr48'
os.makedirs(dst, exist_ok=True)
TARGET_RMS_DB = -21.0


def bounds(y, sr, thr_db=-40.0, lead=0.03, tail=0.12):
    win = int(sr * 0.02)
    n = len(y) // win
    rms = np.sqrt((y[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-9) + 1e-9)
    idx = np.where(db > thr_db)[0]
    a = max(int(idx[0] * win - lead * sr), 0)
    b = min(int((idx[-1] + 1) * win + tail * sr), len(y))
    return a, b, rms[idx]


done = 0
for bid, _ in BEATS:
    p = f'{src}/{bid}.wav'
    if not os.path.exists(p):
        continue
    y, sr = sf.read(p, dtype='float32')
    a, b, voiced = bounds(y, sr)
    y = y[a:b].copy()
    loud = np.sort(voiced)[int(len(voiced) * 0.35):]              # 只按有声的部分量响度
    cur = 20 * np.log10(np.sqrt((loud ** 2).mean()) + 1e-9)
    gain = np.clip(TARGET_RMS_DB - cur, -9, 12)
    y *= 10 ** (gain / 20)
    f = int(0.008 * sr)
    y[:f] *= np.linspace(0, 1, f)
    y[-f * 4:] *= np.linspace(1, 0, f * 4)
    tmp = f'{dst}/_{bid}.wav'
    sf.write(tmp, y, sr, subtype='FLOAT')
    # 先升到 48 kHz 再变速（rubberband，不变调）。直接对 24 kHz 浮点文件用 atempo 会挂死。
    af = 'aresample=48000:resampler=soxr'
    if abs(tempo - 1) > 1e-3:
        af += f',rubberband=tempo={tempo:.4f}'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', tmp, '-af', af, '-c:a', 'pcm_f32le', f'{dst}/{bid}.wav'],
                   stdin=subprocess.DEVNULL, check=True, timeout=60)
    os.remove(tmp)
    done += 1
print('prepared', done, 'of', len(BEATS), 'tempo', tempo)
