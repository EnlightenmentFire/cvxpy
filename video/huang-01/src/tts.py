# -*- coding: utf-8 -*-
"""逐行合成旁白 -> build/lines/<voice>/NNN.wav + build/timeline.json + build/narration.wav
用法: python tts.py [voice] [speed] [--asr]
模型: hexgrad/Kokoro-82M-v1.1-zh (Apache-2.0)
"""
import sys, os, json, re, warnings
warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
from kokoro import KModel, KPipeline
from script import LINES, tts_text

REPO = 'hexgrad/Kokoro-82M-v1.1-zh'; SR = 24000
args = [a for a in sys.argv[1:] if not a.startswith('--')]
VOICE = args[0] if len(args) > 0 else 'zm_011'
SPEED = float(args[1]) if len(args) > 1 else 1.0
ASR = '--asr' in sys.argv
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
OUT = os.path.join(ROOT, 'lines', VOICE); os.makedirs(OUT, exist_ok=True)

_en = KPipeline(lang_code='a', repo_id=REPO, model=False)
def en_callable(t): return next(_en(t)).phonemes
model = KModel(repo_id=REPO).eval()
zh = KPipeline(lang_code='z', repo_id=REPO, model=model, en_callable=en_callable)

def speed_fn(len_ps):  # 官方示例的防"越读越快"修正
    s = 0.8
    if len_ps <= 83: s = 1
    elif len_ps < 183: s = 1 - (len_ps - 83) / 500
    return s * SPEED

def trim(w, thr=0.012, pad=0.05):
    idx = np.where(np.abs(w) > thr)[0]
    if len(idx) == 0: return w
    a = max(0, idx[0] - int(pad * SR)); b = min(len(w), idx[-1] + int(pad * SR))
    w = w[a:b].copy()
    f = int(0.01 * SR); w[:f] *= np.linspace(0, 1, f); w[-f:] *= np.linspace(1, 0, f)
    return w

def synth(text):
    parts = [r.audio.numpy() for r in zh(text, voice=VOICE, speed=speed_fn)]
    return trim(np.concatenate(parts))

asr_model = None
def asr(w):
    global asr_model
    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly
    if asr_model is None: asr_model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = asr_model.transcribe(resample_poly(w, 2, 3).astype(np.float32), language="zh",
                                   initial_prompt="以下是普通话的句子。")
    return "".join(s.text for s in segs)

t = 0.6  # 片头留白
tl = []; chunks = [np.zeros(int(t * SR), dtype=np.float32)]
scenes = []; CARD = 1.2  # 章节卡停留
cache_f = os.path.join(OUT, 'cache.json')
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
for i, (scene, zhs, o) in enumerate(LINES):
    text = tts_text(zhs, o)
    key = f"{text}|{SPEED}"
    f = os.path.join(OUT, f"{i:03}.wav")
    if cache.get(str(i)) == key and os.path.exists(f):
        w, _ = sf.read(f, dtype='float32')
    else:
        w = synth(text); sf.write(f, w, SR); cache[str(i)] = key
    pre = o.get('pre', 0.0); gap = o.get('gap', 0.28)
    if not scenes or scenes[-1]['name'] != scene:
        if scenes: pre += CARD; scenes[-1]['end'] = round(t, 3)
        scenes.append(dict(name=scene, start=round(t, 3) if scenes else 0.0))
    if pre: chunks.append(np.zeros(int(pre * SR), dtype=np.float32)); t += pre
    d = len(w) / SR
    e = dict(i=i, scene=scene, zh=zhs, start=round(t, 3), end=round(t + d, 3), **{k: v for k, v in o.items() if k in ('en', 'src', 'q', 'big', 'cue')})
    if ASR: e['asr'] = asr(w); print(i, f"{d:.1f}s", text, '=>', e['asr'], flush=True)
    tl.append(e)
    chunks += [w, np.zeros(int(gap * SR), dtype=np.float32)]; t += d + gap
t += 2.5
chunks.append(np.zeros(int(2.5 * SR), dtype=np.float32))
json.dump(cache, open(cache_f, 'w'), ensure_ascii=False)
nar = np.concatenate(chunks)
sf.write(os.path.join(ROOT, 'narration.wav'), nar, SR)
scenes[-1]['end'] = round(t, 3)
data = dict(voice=VOICE, speed=SPEED, duration=round(t, 3), scenes=scenes, lines=tl)
json.dump(data, open(os.path.join(ROOT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, 'timeline.js'), 'w', encoding='utf-8').write('window.TL=' + json.dumps(data, ensure_ascii=False) + ';')
print("voice", VOICE, "speed", SPEED, "total", round(t, 1), "s =", f"{int(t//60)}:{int(t%60):02}")
