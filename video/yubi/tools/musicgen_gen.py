# -*- coding: utf-8 -*-
"""配乐：本地 MusicGen（facebook/musicgen-stereo-medium，transformers）按层生成片段，再由 src/score.py 交叉淡化拼接。
模型权重许可：CC-BY-NC-4.0（非商用）。
用法：
  python tools/musicgen_gen.py bench                          # 测速
  python tools/musicgen_gen.py gen  层名:个数,层名:个数 秒数 [seed]          # 同一批生成多个候选
  python tools/musicgen_gen.py cont 源:层名:秒数,源:层名:秒数 [seed] [提示秒数=8]   # 以源文件结尾为音频提示续写，输出“源+续写”整段
输出：cache/music/<层名>_s<seed>_<k>.wav（32 kHz 立体声）；生成参数记入 cache/music/log.json"""
import sys, os, json, time, warnings, numpy as np, soundfile as sf, torch
warnings.filterwarnings('ignore'); torch.set_num_threads(4)
from transformers import AutoProcessor, MusicgenForConditionalGeneration
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'cache', 'music'); os.makedirs(OUT, exist_ok=True)
MID = 'facebook/musicgen-stereo-medium'
BASE = 'D minor, no vocals'
PROMPTS = {
    # 铺底：开场到交代背景，只有长音 / pad
    'bed':     f'dark cinematic ambient, sustained low cellos and double basses drone, soft string pad, distant chinese xun flute, sparse, solemn, mysterious, 60 bpm, no drums, {BASE}',
    # 推进：冲突升级，加入慢鼓
    'build':   f'cinematic orchestral tension, low cellos and double basses ostinato, slow taiko drums, chinese xun flute melody, solemn, tense, 70 bpm, {BASE}',
    # 肆段：鼓点加紧
    'drive':   f'cinematic war battle, driving taiko drums, fast low strings ostinato, tense, urgent, 80 bpm, {BASE}',
    # 高潮：规范给的悲壮战争提示词
    'climax':  'epic cinematic orchestral, low cellos and double basses, slow taiko drums, chinese xun flute melody, solemn, tragic, heroic, D minor, 70 bpm, no vocals',
    # 陆段：伤亡之后的哀段
    'lament':  f'tragic slow orchestral lament, low strings, solo chinese xun flute melody, mournful, sorrowful, 60 bpm, no drums, {BASE}',
    # 捌段：回落、沉思
    'reflect': f'solemn reflective cinematic, low strings pad, chinese guqin, sparse, calm, 60 bpm, no drums, {BASE}',
    # 结尾：收成单个乐器
    'coda':    f'solo chinese xun flute, slow mournful melody, sparse, long reverb, 60 bpm, no drums, no strings, {BASE}',
}

proc = AutoProcessor.from_pretrained(MID)
dtype = torch.bfloat16 if os.environ.get('MG_FP32') != '1' else torch.float32
model = MusicgenForConditionalGeneration.from_pretrained(MID, dtype=dtype)
model.audio_encoder.float()            # EnCodec 编解码保持 fp32
model.eval()
SR = model.config.audio_encoder.sampling_rate; FR = 50
logp = os.path.join(OUT, 'log.json'); log = json.load(open(logp)) if os.path.exists(logp) else {}


def run(texts, secs, audio=None, seed=0):
    torch.manual_seed(seed); np.random.seed(seed)
    if audio is None: inp = proc(text=texts, padding=True, return_tensors='pt')
    else: inp = proc(text=texts, audio=audio, sampling_rate=SR, padding=True, return_tensors='pt')
    with torch.inference_mode():
        out = model.generate(**inp, do_sample=True, guidance_scale=3.0, top_k=250, temperature=1.0, max_new_tokens=int(secs * FR) + 3)
    return out.float().numpy()          # (batch, 2, samples)


if sys.argv[1] == 'bench':
    for bs in (1, 3):
        t0 = time.time(); a = run([PROMPTS['climax']] * bs, 2.0); dt = time.time() - t0
        print(f'batch {bs}: 2 s audio in {dt:.1f} s  -> {dt / 100:.3f} s/step', a.shape, flush=True)
elif sys.argv[1] == 'gen':
    # 层名:个数,层名:个数 …  同一批生成（CPU 上批量几乎不增加每步耗时）
    spec = [(x.split(':')[0], int(x.split(':')[1])) for x in sys.argv[2].split(',')]; secs = float(sys.argv[3]); seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    names = [(ly, k) for ly, n in spec for k in range(n)]
    t0 = time.time(); a = run([PROMPTS[ly] for ly, _ in names], secs, seed=seed)
    for j, (ly, k) in enumerate(names):
        p = os.path.join(OUT, f'{ly}_s{seed}_{k}.wav'); sf.write(p, a[j].T, SR, subtype='FLOAT')
        log[os.path.basename(p)] = dict(model=MID, prompt=PROMPTS[ly], secs=secs, seed=seed, idx=k, mode='gen')
    json.dump(log, open(logp, 'w'), ensure_ascii=False, indent=1)
    print(f'{sys.argv[2]} {secs}s in {time.time() - t0:.0f}s', flush=True)
elif sys.argv[1] == 'cont':
    # 源wav:层名:续写秒数,源wav:层名:续写秒数 …  同一批续写；每条以源文件最后 ps 秒为音频提示，输出“源+续写”整段
    jobs = [x.split(':') for x in sys.argv[2].split(',')]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    ps = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0; secs = max(float(j[2]) for j in jobs)
    srcs = []
    for f, ly, _ in jobs:
        w, sr = sf.read(os.path.join(OUT, f)); assert sr == SR; srcs.append(w.T.astype(np.float32))
    prs = [w[:, -int(ps * SR):] for w in srcs]
    t0 = time.time(); a = run([PROMPTS[ly] for _, ly, _ in jobs], secs, audio=prs, seed=seed)
    inc = a.shape[2] > int(secs * SR) + pr.shape[1] // 2        # 输出是否含提示段（含则去掉）
    seen = {}
    print('output', a.shape, 'includes prompt:', inc, flush=True)
    for (f, ly, sc), w, pr, out in zip(jobs, srcs, prs, a):
        if inc:
            c = np.corrcoef(out[0, pr.shape[1] // 2: pr.shape[1]], pr[0, pr.shape[1] // 2:])[0, 1]; print(f'  {f}: prompt corr {c:.2f}', flush=True)
        o = pr.shape[1] if inc else 0; new = out[:, o: o + int(float(sc) * SR)]
        dup = sum(1 for j in jobs if j[0] == f and j[1] == ly); seen[(f, ly)] = seen.get((f, ly), -1) + 1
        if inc:      # 接缝：原文件最后 0.5 秒与输出里重新解码的同一段交叉，避免两次解码相接处的爆音
            xf = int(0.5 * SR); r = np.linspace(0, 1, xf)[None, :]
            full = np.concatenate([w[:, :-xf], w[:, -xf:] * (1 - r) + out[:, o - xf:o] * r, new], 1)
        else: full = np.concatenate([w, new], 1)
        name = f.replace('.wav', '') + f'+{ly}{seed}' + (f'v{seen[(f, ly)]}' if dup > 1 else '') + '.wav'
        sf.write(os.path.join(OUT, name), full.T, SR, subtype='FLOAT')
        log[name] = dict(model=MID, prompt=PROMPTS[ly], secs=float(sc), seed=seed, mode='cont', src=f, prompt_secs=ps)
        print(f'cont {name} total {full.shape[1] / SR:.1f}s', flush=True)
    json.dump(log, open(logp, 'w'), ensure_ascii=False, indent=1)
    print(f'cont batch {len(jobs)} +{secs}s in {time.time() - t0:.0f}s', flush=True)
