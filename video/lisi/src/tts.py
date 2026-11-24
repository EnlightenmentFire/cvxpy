# -*- coding: utf-8 -*-
"""Kokoro-82M v1.1-zh (Apache-2.0) 逐句合成。用法: python tts.py --voice zm_029 [--only c1,c3]
输出 build/tts/<voice>/<id>.wav (24k mono)。按 (voice, speed, tts文本) 缓存。"""
import argparse, hashlib, json, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf, torch
from script_data import segments
REPO = "hexgrad/Kokoro-82M-v1.1-zh"; SR = 24000
ap = argparse.ArgumentParser()
ap.add_argument("--voice", default="zm_029"); ap.add_argument("--only", default="")
ap.add_argument("--speed-n", type=float, default=1.28); ap.add_argument("--speed-q", type=float, default=1.08)
a = ap.parse_args()
out = os.path.join(os.path.dirname(__file__), "..", "build", "tts", a.voice); os.makedirs(out, exist_ok=True)
from kokoro import KModel, KPipeline
torch.manual_seed(0); torch.set_num_threads(4)
model = KModel(repo_id=REPO).to("cpu").eval()
pipe = KPipeline(lang_code="z", repo_id=REPO, model=model)
only = set(filter(None, a.only.split(",")))
def trim(w, thr=0.004, pad=0.04):
    idx = np.where(np.abs(w) > thr)[0]
    if len(idx) == 0: return w
    return w[max(0, idx[0]-int(pad*SR)): min(len(w), idx[-1]+int(pad*SR))]
for s in segments():
    if only and s["id"] not in only: continue
    sp = a.speed_q if s["kind"] == "q" else a.speed_n
    key = hashlib.md5(f"{a.voice}|{sp}|{s['tts']}".encode()).hexdigest()[:10]
    wavp = os.path.join(out, s["id"] + ".wav"); keyp = wavp + ".key"
    if os.path.exists(wavp) and os.path.exists(keyp) and open(keyp).read() == key: continue
    parts = [r.audio.numpy() for r in pipe(s["tts"], voice=a.voice, speed=sp, split_pattern=None)]
    w = trim(np.concatenate(parts).astype(np.float32))
    sf.write(wavp, w, SR); open(keyp, "w").write(key)
    print(s["id"], "%.2fs" % (len(w)/SR), flush=True)
