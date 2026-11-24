# -*- coding: utf-8 -*-
"""逐句合成旁白。模型：Kokoro-82M-v1.1-zh（hexgrad，Apache-2.0）。
用法：python src/tts.py [voice] [speed_n] [speed_q]；ONLY=3,17 只重做指定行。"""
import sys, os, json, warnings, numpy as np, soundfile as sf; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text
import torch; torch.set_num_threads(4)
from kokoro import KPipeline, KModel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
voice = sys.argv[1] if len(sys.argv) > 1 else 'zm_029'
sn = float(sys.argv[2]) if len(sys.argv) > 2 else 1.4
sq = float(sys.argv[3]) if len(sys.argv) > 3 else 1.18
out = os.environ.get("LINES_DIR", f"{ROOT}/audio/lines"); os.makedirs(out, exist_ok=True)
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)


def trim(a, sr=24000, th=0.004, pad=0.07):
    e = np.abs(a); w = int(sr * 0.01); env = np.convolve(e, np.ones(w) / w, 'same'); idx = np.where(env > th)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] - int(pad * sr)): min(len(a), idx[-1] + int(pad * 2.4 * sr))]


ONLY = [int(x) for x in os.environ.get('ONLY', '').split(',') if x]
meta = []; tot = 0
for i, l in enumerate(L):
    p = f"{out}/{i:03d}.wav"
    if ONLY and i not in ONLY and os.path.exists(p):
        d = sf.info(p).duration; tot += d; meta.append(dict(i=i, dur=round(d, 3))); continue
    sp = sq if l[1] == 'q' else sn
    if l[0] == 's10': sp *= 0.86                 # 收尾三句放慢
    if l[0] == 's7' and l[1] == 'q': sp *= 0.92  # 敕勒歌再慢一点
    if l[0] == 's5' and l[1] == 'q': sp *= 0.96  # 核心段的原文放慢
    a = np.concatenate([r.audio.numpy() for r in pipe(tts_text(l[2]), voice=voice, speed=sp)])
    a = trim(a).astype(np.float32); a[:200] *= np.linspace(0, 1, 200); a[-480:] *= np.linspace(1, 0, 480)
    sf.write(p, a, 24000, subtype='PCM_16'); d = len(a) / 24000; tot += d; meta.append(dict(i=i, dur=round(d, 3)))
json.dump(dict(voice=voice, speed_n=sn, speed_q=sq, lines=meta), open(f"{out}/meta.json", "w"))
print("voice", voice, "speech total %.1fs" % tot)
