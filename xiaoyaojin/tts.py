# 运行环境：/opt/ttsenv (Python 3.12, kokoro 0.9.4)
# 生成每条旁白 wav，并写 manifest.json（时长驱动画面时间线）
import json, os, re, sys
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import S
from kokoro import KPipeline, KModel

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SR = 24000
SEMI = -2.0                      # 降调（半音）：约 114Hz → 约 101Hz，更低沉
K = 2 ** (SEMI / 12)             # 播放速率因子
SPEED = 1.3                      # 目标语速（编导规范 1.3 倍）
UP, DOWN = 449, 400              # ≈ 1/K，重采样拉长并降调

REPL = [("乐进", "岳进"), ("乐将军", "岳将军"), ("张辽传", "张辽撰"), ("李典传", "李典撰"), ("吴主传", "吴主撰"),
        ("甘宁传", "甘宁撰"), ("凌统传", "凌统撰"), ("江表传", "江表撰"), ("蒋济传", "蒋济撰"), ("都亭侯", "嘟亭侯"),
        ("虎贲", "虎奔"), ("会稽", "快鸡"), ("椎牛", "垂牛"), ("张憙", "张喜"), ("薛悌", "薛替"), ("“", ""), ("”", ""),
        ("……", "，")]


def prep(t):
    for a, b in REPL:
        t = t.replace(a, b)
    return t


import torch
repo = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=repo).eval()
g2p = KPipeline(lang_code='z', repo_id=repo, model=False)
PACK = g2p.load_voice('zm_014')


def synth_chunk(ps, base, head=3, tail=5, slow=1.05):
    # Kokoro 在高语速下会吞掉首尾音节：逐 token 设定语速，首尾放慢
    n = len([p for p in ps if p in model.vocab]) + 2
    sp = torch.full((n,), base)
    sp[:head] = slow
    sp[-tail:] = slow
    with torch.no_grad():
        return model(ps, PACK[len(ps) - 1], sp).numpy()

ONLY = set(int(v) for v in sys.argv[2].split(',')) if len(sys.argv) > 2 else None
old = {m['i']: m for m in json.load(open(os.path.join(OUT, 'manifest.json')))} if ONLY else {}
man = []
log = open(os.path.join(OUT, 'phonemes.txt' if not ONLY else 'phonemes_partial.txt'), 'w')
for i, s in enumerate(S):
    if ONLY is not None and i not in ONLY and i in old and 't' in s:
        o = dict(old[i]); o['gap'] = s['gap']; man.append(o); continue
    if 't' not in s:
        man.append(dict(i=i, chap=True, dur=s['dur']))
        continue
    txt = prep(s.get('tts') or s['t'])
    chunks = []
    for r in g2p(txt, voice='zm_014'):
        log.write(f"{i}\t{r.graphemes}\t{r.phonemes}\n")
        chunks.append(synth_chunk(r.phonemes, SPEED / K))
        chunks.append(np.zeros(int(0.12 * SR), dtype=np.float32))
    a = np.concatenate(chunks[:-1])
    a = resample_poly(a, UP, DOWN).astype(np.float32)
    # 去掉首尾静音
    thr = 0.005 * np.max(np.abs(a))
    nz = np.where(np.abs(a) > thr)[0]
    a = a[max(0, nz[0] - int(0.05 * SR)): nz[-1] + int(0.09 * SR)]
    fn = os.path.join(OUT, f"seg_{i:03d}.wav")
    sf.write(fn, a, SR)
    man.append(dict(i=i, file=fn, dur=len(a) / SR, gap=s['gap']))
    print(i, round(len(a) / SR, 2), txt[:30], flush=True)
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
print('total', sum(m['dur'] + m.get('gap', 0) for m in man))
