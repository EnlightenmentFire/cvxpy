"""Background score clips with MusicGen (facebook/musicgen-stereo-medium), per 配乐规范 §三.

Batched bf16 generation on CPU (several prompts per forward pass); EnCodec decodes in fp32.
  music_gen.py versions                -> every layer x VERSIONS[layer] clips of SECONDS[layer]
  music_gen.py extend <sel.json> <layer:steps> ...   -> continue the chosen clip of a layer
Clips: /home/user/wude_build/music/clips/<layer>_v<k>.wav (32 kHz stereo) + .json
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf
import torch

MODEL = "/home/user/wude_build/models/musicgen-stereo-medium"
OUT = "/home/user/wude_build/music/clips"
BATCH = int(os.environ.get("MG_BATCH", "4"))

NEG = "no vocals, no singing, no choir"
PROMPTS = {
    # 铺底：只有长音 / pad，古琴稀疏
    "base": ("cinematic underscore, ancient chinese, low cello and double bass long notes with soft string pad, "
             "very sparse guqin plucks, solemn, restrained, desolate, slow, D minor, no drums, " + NEG),
    # 推进（秦）：规整、冷硬的低鼓 + 低音弦乐
    "push_cold": ("cinematic underscore, ancient chinese, low strings ostinato, steady slow taiko drum pulse, "
                  "distant bronze bells, cold, stern, tense, solemn, D minor, 70 bpm, no melody, " + NEG),
    # 推进（汉初的别扭 / 争论）：心跳式低鼓、紧张但不吵
    "push_tension": ("cinematic underscore, low strings drone with soft heartbeat-like frame drum, guqin harmonics, "
                     "uneasy, restrained tension, slow, D minor, 66 bpm, sparse, " + NEG),
    # 推进（太初 / 东汉）：更暖，但仍克制
    "push_warm": ("cinematic underscore, ancient chinese, warm strings with gentle guqin melody, soft frame drum, "
                  "dignified, solemn yet hopeful, restrained, 72 bpm, " + NEG),
    # 高潮：全编制
    "climax": ("epic cinematic orchestral, low cellos and double basses, slow taiko drums, chinese xun flute melody, "
               "bronze chime bells, solemn, tragic, heroic, D minor, 70 bpm, " + NEG),
    # 结尾：单件乐器 + 余音
    "ending": ("solo guqin, slow, sparse, reflective, ancient chinese, gentle final cadence, long reverb tail, "
               + NEG),
}
VERSIONS = {"base": 2, "push_cold": 2, "push_tension": 2, "push_warm": 2, "climax": 2, "ending": 2}
SECONDS = {"base": 30, "push_cold": 30, "push_tension": 30, "push_warm": 30, "climax": 30, "ending": 20}


def load():
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    torch.set_num_threads(int(os.environ.get("THREADS", "4")))
    proc = AutoProcessor.from_pretrained(MODEL)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL, torch_dtype=torch.bfloat16).eval()
    model.audio_encoder.to(torch.float32)  # decode audio in full precision
    return proc, model


def generate(proc, model, prompts, seconds, seed, audio_prompts=None, sr=32000):
    torch.manual_seed(seed)
    kw = dict(text=prompts, padding=True, return_tensors="pt")
    if audio_prompts is not None:
        kw.update(audio=[a.T.astype(np.float32) for a in audio_prompts], sampling_rate=sr)
    inputs = proc(**kw)
    if "input_values" in inputs:
        inputs["input_values"] = inputs["input_values"].to(torch.float32)
    with torch.inference_mode():
        out = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=int(seconds * 50))
    res = []
    for o in out:
        a = o.float().numpy().T  # (samples, channels)
        pk = float(np.abs(a).max())
        if pk > 0.98:            # EnCodec can overshoot: scale down instead of clipping
            a = a * (0.98 / pk)
        res.append(a)
    return res


def cmd_versions(proc, model, sr):
    jobs = []
    for layer, n in VERSIONS.items():
        for k in range(n):
            path = f"{OUT}/{layer}_v{k}.wav"
            if not os.path.exists(path):
                jobs.append((layer, k, path))
    # group jobs of equal length so a batch shares one max_new_tokens
    jobs.sort(key=lambda j: SECONDS[j[0]])
    for b in range(0, len(jobs), BATCH):
        batch = jobs[b:b + BATCH]
        secs = max(SECONDS[j[0]] for j in batch)
        t0 = time.time()
        outs = generate(proc, model, [PROMPTS[j[0]] for j in batch], secs, seed=1000 + b)
        for (layer, k, path), a in zip(batch, outs):
            sf.write(path, a, sr, subtype="FLOAT")
            json.dump(dict(layer=layer, prompt=PROMPTS[layer], version=k, seed=1000 + b, seconds=len(a) / sr),
                      open(path[:-4] + ".json", "w"), ensure_ascii=False)
        print(f"batch {b // BATCH}: {[j[0] + '_v' + str(j[1]) for j in batch]} {secs}s in {time.time() - t0:.0f}s",
              flush=True)


def cmd_extend(proc, model, sr, sel_path, specs):
    """specs like base:2 push_tension:2 -> continue the first-choice clip of each layer by 20 s steps."""
    sel = json.load(open(sel_path))["choice"]
    plan = {s.split(":")[0]: int(s.split(":")[1]) for s in specs}
    cur = {layer: sf.read(sel[layer][0])[0] for layer in plan}
    ctx, new_s = 10.0, 20.0
    for step in range(max(plan.values())):
        layers = [l for l in plan if plan[l] > step]
        tails = [cur[l][-int(ctx * sr):] for l in layers]
        t0 = time.time()
        outs = generate(proc, model, [PROMPTS[l] for l in layers], new_s, seed=2000 + step, audio_prompts=tails, sr=sr)
        for l, tail, out in zip(layers, tails, outs):
            new = out[len(tail):]
            f = int(1.0 * sr)
            w = np.sin(np.linspace(0, np.pi / 2, f))[:, None]
            join = cur[l][-f:] * w[::-1] + out[len(tail) - f:len(tail)] * w
            cur[l] = np.concatenate([cur[l][:-f], join, new])
        print(f"extend step {step}: {layers} in {time.time() - t0:.0f}s", flush=True)
    for l in plan:
        path = sel[l][0][:-4] + "_ext.wav"
        sf.write(path, cur[l], sr, subtype="FLOAT")
        print("wrote", path, f"{len(cur[l]) / sr:.1f}s", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    proc, model = load()
    sr = model.config.audio_encoder.sampling_rate
    if sys.argv[1] == "versions":
        cmd_versions(proc, model, sr)
    elif sys.argv[1] == "extend":
        cmd_extend(proc, model, sr, sys.argv[2], sys.argv[3:])
