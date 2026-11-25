"""托克维尔声音：Qwen3-TTS-12Hz-1.7B-Base ICL 克隆，参考音 ref.wav（18 秒设计音色）。
逐句合成；中位基频须在 85–105 Hz、语速 2.6–6.5 字/秒，否则换种子（最多 3 次，取最接近者）。"""
import sys, os, re, json, time, torch, numpy as np, soundfile as sf, parselmouth, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/tmp/claude-0/work/vid')
from script import BEATS
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
OUT = '/tmp/claude-0/work/tts/raw'; os.makedirs(OUT, exist_ok=True)
REF = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
w, sr = sf.read('/tmp/claude-0/work/tts/ref.wav')
P = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF)
def f0(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300).selected_array['frequency']
    p = p[p > 0]; return float(np.median(p)) if len(p) else 0.0
only = [a for a in sys.argv[1:] if not a.startswith('-')]; force = '--force' in sys.argv
for b in BEATS:
    if only and b['id'] not in only: continue
    meta = f"{OUT}/{b['id']}.json"
    if not force and os.path.exists(meta) and json.load(open(meta)).get('say') == b['say']: continue
    n = len(re.sub(r'[^一-鿿0-9]', '', b['say'])); best = None; t = time.time()
    seeds = [1000 + 7 * k for k in range(3)]
    if force: seeds = [int(time.time()) % 9973 + 11 * k for k in range(3)]
    for k, seed in enumerate(seeds):
        torch.manual_seed(seed); np.random.seed(seed)
        ws, sr = m.generate_voice_clone(text=b['say'], language="Chinese", voice_clone_prompt=P, temperature=0.8, subtalker_temperature=0.8)
        x = ws[0].astype(np.float32); fz = f0(x, sr); d = len(x) / sr; cps = n / max(d, 0.1)
        ok = 85 <= fz <= 105 and 2.6 <= cps <= 6.5
        score = abs(fz - 92) + (0 if 2.6 <= cps <= 6.5 else 100)
        if best is None or score < best[0]: best = (score, x, sr, seed, fz, d, cps, ok)
        if ok: break
    _, x, sr, seed, fz, d, cps, ok = best
    sf.write(f"{OUT}/{b['id']}.wav", x, sr)
    json.dump(dict(id=b['id'], say=b['say'], seed=seed, f0=round(fz, 1), dur=round(d, 2), cps=round(cps, 2), ok=ok, tries=k + 1), open(meta, 'w'), ensure_ascii=False)
    print('GEN', b['id'], round(fz, 1), round(d, 2), 'cps', round(cps, 2), 'ok', ok, 'tries', k + 1, 'sec', round(time.time() - t), flush=True)
print('ALLDONE', flush=True)
