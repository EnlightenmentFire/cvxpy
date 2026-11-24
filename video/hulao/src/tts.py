# -*- coding: utf-8 -*-
"""逐句合成旁白。模型：Kokoro-82M-v1.1-zh（Apache-2.0）。用法：python tts.py [voice] [speed_n] [speed_q] [outdir]
环境变量 ONLY=3,7 只重做指定行。"""
import sys, os, re, json, warnings, numpy as np, soundfile as sf; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text, LEX
from kokoro import KPipeline, KModel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
voice = sys.argv[1] if len(sys.argv) > 1 else 'zm_034'
sn = float(sys.argv[2]) if len(sys.argv) > 2 else 1.34
sq = float(sys.argv[3]) if len(sys.argv) > 3 else 1.16
out = sys.argv[4] if len(sys.argv) > 4 else f"{ROOT}/audio/lines"
os.makedirs(out, exist_ok=True)
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)
from lex import register; register(LEX)
def trim(a, sr=24000, th=0.003, pad=0.09):
    e = np.abs(a); w = int(sr * 0.01); env = np.convolve(e, np.ones(w) / w, 'same'); idx = np.where(env > th)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] - int(pad * sr)): min(len(a), idx[-1] + int(pad * 2.2 * sr))]
tot = 0; meta = []
ONLY = [int(x) for x in os.environ.get('ONLY', '').split(',') if x]
SLOW = {'s12'}
for i, l in enumerate(L):
    if ONLY and i not in ONLY:
        d = sf.info(f"{out}/{i:03d}.wav").duration; tot += d; meta.append(dict(i=i, dur=round(d, 3), chunks=1)); continue
    t = tts_text(l[2]); sp = sq if l[1] == 'q' else sn
    if l[0] in SLOW and l[1] == 'n': sp *= 0.9
    parts = [r.audio.numpy() for r in pipe(t, voice=voice, speed=sp)]
    a = trim(np.concatenate(parts)).astype(np.float32)
    a[:240] *= np.linspace(0, 1, 240); a[-480:] *= np.linspace(1, 0, 480)
    sf.write(f"{out}/{i:03d}.wav", a, 24000, subtype='PCM_16'); d = len(a) / 24000; tot += d
    meta.append(dict(i=i, dur=round(d, 3), chunks=len(parts)))
    if i % 10 == 0: print(i, round(tot, 1), flush=True)
json.dump(dict(voice=voice, speed_n=sn, speed_q=sq, lines=meta), open(f"{out}/meta.json", "w"))
print("voice", voice, "speech total %.1fs" % tot, "multi-chunk lines:", [m['i'] for m in meta if m['chunks'] > 1])
