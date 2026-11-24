# -*- coding: utf-8 -*-
"""用 Qwen3-TTS Base 克隆 VoiceDesign 设计出的参考音（不是任何真人），逐句合成。
每句：量中位音高（目标 85–105 Hz，超出就换 seed 重来，最多 4 次，不做整体变调）→ 超过 0.4 秒的停顿压到 0.4 秒 → 50 Hz 高通 → 去首尾静音。
用法：LINES_DIR=audio/lines_qwen python tools/qwen_clone.py ref_dir [行号,行号,...]（不给行号则全篇）"""
import sys, os, json, time, re, warnings, numpy as np, soundfile as sf, torch, parselmouth
warnings.filterwarnings('ignore'); torch.set_num_threads(4)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from script import L
from qwen_tts import Qwen3TTSModel

REF = json.load(open(os.path.join(sys.argv[1], 'design.json')))
OUT = os.environ.get('LINES_DIR', os.path.join(ROOT, 'audio', 'lines_qwen')); os.makedirs(OUT, exist_ok=True)
ONLY = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else list(range(len(L)))
# Qwen 用原文朗读；只替换少数生僻字/易错多音字为同音字（字幕不受影响）
QFIX = [('《', ''), ('》', ''), ('——', '，'), ('……', '。'), ('以扞之', '以捍之'), ('木栅', '木炸'), ('祖珽', '祖挺'), ('一行字', '一杭字'), ('这行字', '这杭字')]
def qtext(t):
    for a, b in QFIX: t = t.replace(a, b)
    return t

def f0(w, sr):
    s = parselmouth.Sound(w.astype(np.float64), sr)
    f = s.to_pitch_ac(time_step=0.01, pitch_floor=55, pitch_ceiling=350).selected_array['frequency']; f = f[f > 0]
    if len(f) < 10: return 999.0, 999.0
    return round(float(np.median(f)), 1), round(float(np.percentile(f, 90)), 1)

def hp50(w, sr):
    X = np.fft.rfft(w); fr = np.fft.rfftfreq(len(w), 1 / sr); g = 1 / np.sqrt(1 + (50 / np.maximum(fr, 1e-3)) ** 8)
    return np.fft.irfft(X * g, len(w)).astype(np.float32)

def squeeze_pauses(w, sr, maxp=0.4, th_rel=0.04):
    """把句内超过 maxp 秒的停顿压到 maxp 秒（保留停顿两端各一半）。"""
    win = int(sr * 0.02); n = len(w) // win
    if n < 5: return w
    e = np.sqrt((w[:n * win].reshape(n, win) ** 2).mean(1)); q = e < max(0.006, e.max() * th_rel)
    keep = np.ones(len(w), bool); i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            dur = (j - i) * 0.02
            if dur > maxp and i > 0 and j < n:
                cut = dur - maxp; a = int((i * 0.02 + maxp / 2) * sr); b = a + int(cut * sr); keep[a:b] = False
            i = j
        else: i += 1
    return w[keep]

def trim(w, sr, th=0.006, pad=0.06):
    win = int(sr * 0.01); env = np.convolve(np.abs(w), np.ones(win) / win, 'same'); idx = np.where(env > th)[0]
    if len(idx) == 0: return w
    a = w[max(0, idx[0] - int(pad * sr)): min(len(w), idx[-1] + int(pad * 2.2 * sr))].copy()
    k = min(len(a) // 4, int(0.01 * sr)); a[:k] *= np.linspace(0, 1, k); k2 = min(len(a) // 4, int(0.03 * sr)); a[-k2:] *= np.linspace(1, 0, k2)
    return a

model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
prompt = model.create_voice_clone_prompt(ref_audio=REF['chosen']['path'], ref_text=REF['ref_text'], x_vector_only_mode=False)
logp = os.path.join(OUT, 'qwen_log.json'); log = json.load(open(logp)) if os.path.exists(logp) else {}
for i in ONLY:
    l = L[i]; txt = qtext(l[2]); nch = len(re.findall(r'[一-鿿]', l[2])); best = None; t0 = time.time()
    for k, seed in enumerate((7, 19, 31, 43)):
        torch.manual_seed(seed + 1000 * i)
        wavs, sr = model.generate_voice_clone(text=txt, language="Chinese", voice_clone_prompt=prompt)
        w = np.asarray(wavs[0], np.float32); med, p90 = f0(w, sr); dur = len(w) / sr; cps = nch / max(0.1, dur)
        ok = 85 <= med <= 105 and p90 <= 165 and 1.8 <= cps <= 7.0
        score = abs(med - 95) + 0.15 * max(0, p90 - 140)
        if best is None or score < best[0]: best = (score, w, sr, med, p90, seed)
        if ok: break
    _, w, sr, med, p90, seed = best
    w = trim(squeeze_pauses(hp50(w, sr), sr), sr)
    sf.write(os.path.join(OUT, f'{i:03d}.wav'), w, sr, subtype='PCM_16')
    log[str(i)] = dict(med=med, p90=p90, seed=seed, tries=k + 1, dur=round(len(w) / sr, 2), cps=round(nch / (len(w) / sr), 2))
    json.dump(log, open(logp, 'w'), ensure_ascii=False, indent=0)
    print('LINE', i, l[1], 'med', med, 'p90', p90, 'dur', round(len(w) / sr, 2), 'cps', round(nch / (len(w) / sr), 2), 'tries', k + 1, round(time.time() - t0), 's', flush=True)
print('DONE')
