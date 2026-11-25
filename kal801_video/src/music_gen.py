# -*- coding: utf-8 -*-
"""按《配乐规范》用 MusicGen（facebook/musicgen-stereo-medium）分层生成配乐片段。
注意：MusicGen 模型权重为 CC-BY-NC 4.0（非商用）。
用法：python3 music_gen.py [层名...] [--secs N] [--versions K]
产物：$WORK/music/<层>_<k>.wav（32 kHz 立体声）与 music_manifest.json
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
OUT = os.path.join(WORK, "music")
MODEL = "/opt/models/musicgen-stereo-medium"
os.makedirs(OUT, exist_ok=True)

# 题材：夜航空难 = 悬疑（低频 drone + 稀疏心跳低鼓）为主，分析段落用"组织"类（极简钢琴 + 轻脉冲），
# 遇难与结尾用"人物命运"类（低音弦乐 / 大提琴，克制）。全部 D 小调，便于交叉淡化。
LAYERS = {
    "L1_pad": "dark ambient cinematic underscore, deep low synthesizer drone and soft sustained pad, night flight "
              "atmosphere, very sparse, slow, D minor, no drums, no melody, no vocals",
    "L2_push": "tense suspense film underscore, low sub drone with sparse heartbeat-like low drum hits, slow pulse "
               "60 bpm, dark, minimal, cold war thriller, D minor, no melody, no vocals",
    "L3_climax": "solemn tragic cinematic orchestral swell, low cellos and double basses, soft french horns, deep "
                 "timpani roll, slow, D minor, restrained and mournful, no vocals",
    "L3_elegy": "solemn mournful orchestral adagio, sustained low strings and cellos, soft french horn, slow swell "
                "from silence, D minor, restrained, dignified, no percussion, no drums, no cymbals, no vocals",
    "L4_think": "minimal modern electronic pulse with soft sparse piano, steady, thoughtful, restrained, 80 bpm, "
                "D minor, no vocals",
    "L4_piano": "reflective minimal piano with soft low strings pad, calm, slow, thoughtful, D minor, no drums, "
                "no vocals",
    "L5_end": "solo cello melody over soft strings pad, slow, reflective, D minor, restrained, ending on a long "
              "sustained low note, no drums, no vocals",
}


def main():
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    secs = 25.0
    versions = 2
    threads = 4
    if "--secs" in sys.argv:
        secs = float(sys.argv[sys.argv.index("--secs") + 1])
    if "--versions" in sys.argv:
        versions = int(sys.argv[sys.argv.index("--versions") + 1])
    if "--threads" in sys.argv:
        threads = int(sys.argv[sys.argv.index("--threads") + 1])
    torch.set_num_threads(threads)
    layers = [a for a in args if a in LAYERS] or list(LAYERS)
    t0 = time.time()
    proc = AutoProcessor.from_pretrained(MODEL)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    model.audio_encoder.to(torch.float32)     # 解码器/文本编码器 bf16（CPU AMX 约快 2 倍、内存减半）；EnCodec 保持 fp32
    model.eval()
    sr = model.config.audio_encoder.sampling_rate
    fr = model.config.audio_encoder.frame_rate
    print(f"loaded in {time.time() - t0:.0f}s, sr={sr}, frame_rate={fr}", flush=True)
    manp = os.path.join(WORK, "music_manifest.json")
    man = json.load(open(manp)) if os.path.exists(manp) else {}
    for name in layers:
        keys = [f"{name}_{k}" for k in range(versions)]
        todo = [k for k, key in enumerate(keys) if not (key in man and os.path.exists(os.path.join(OUT, key + ".wav")))]
        if not todo:
            continue
        seed = 1997 + 101 * todo[0] + len(name)
        torch.manual_seed(seed)
        inputs = proc(text=[LAYERS[name]] * len(todo), padding=True, return_tensors="pt")
        t1 = time.time()
        with torch.inference_mode(), torch.autocast("cpu", dtype=torch.bfloat16):
            audio = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=int(secs * fr) + 4)
        for j, k in enumerate(todo):
            key = keys[k]
            path = os.path.join(OUT, key + ".wav")
            w = audio[j].float().cpu().numpy().T  # (n, ch)
            sf.write(path, w, sr)
            man[key] = dict(file=path, layer=name, prompt=LAYERS[name], seed=seed, batch_index=j,
                            secs=round(len(w) / sr, 2), gen_s=round(time.time() - t1, 1))
        json.dump(man, open(manp, "w"), indent=1)
        print(f"{name}: {len(todo)} x {secs:.0f}s in {time.time() - t1:.0f}s", flush=True)

if __name__ == "__main__":
    main()
