# -*- coding: utf-8 -*-
"""用 ACE-Step 1.5（MIT，可商用；训练数据为授权/免版税/合成素材）在本地生成配乐分层。

python ace_music.py OUTDIR layer=秒数:版本数 ...
层：base（铺底） push（推进） climax（高潮） coda（尾声）
只用 DiT（turbo，8 步），不用 5Hz LM（CPU 上太慢）。
"""
import json
import os
import sys
import time

ACE = "/home/user/work/acestep/code"
sys.path.insert(0, ACE)

PROMPTS = {
    "base": ("dark cinematic ambient underscore, low cellos and double basses holding long sustained notes, "
             "sparse chinese xun flute phrases, soft guqin harmonics, solemn, tragic, spacious, D minor, 64 bpm, "
             "no drums, no vocals, instrumental film score"),
    "push": ("cinematic orchestral build, low strings ostinato, slow deep taiko drums, timpani rolls, "
             "chinese xun flute melody, tense, heroic, ancient battle, D minor, 72 bpm, no vocals, instrumental film score"),
    "climax": ("epic cinematic orchestral climax, full orchestra, powerful taiko drum ensemble, low brass, "
               "cellos and double basses, chinese xun flute lead, solemn, tragic, heroic, D minor, 72 bpm, "
               "no vocals, instrumental film score"),
    "coda": ("solo chinese xun flute, slow and sparse, long reverb tail, low string drone fading, melancholic, "
             "D minor, 60 bpm, no drums, no vocals, instrumental"),
    "after": ("quiet mournful cinematic underscore after a battle, low strings sustained, very soft distant taiko heartbeat, "
              "sparse guqin notes, solemn reflection, D minor, 60 bpm, no vocals, instrumental film score"),
}
BPM = {"base": 64, "push": 72, "climax": 72, "coda": 60, "after": 60}


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    jobs = []
    for a in sys.argv[2:]:
        layer, spec = a.split("=")
        dur, n = spec.split(":")
        jobs.append((layer, float(dur), int(n)))
    import torch
    torch.set_num_threads(int(os.environ.get("ACE_THREADS", "4")))
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    t0 = time.time()
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=ACE, config_path="acestep-v15-turbo", device="cpu")
    print("init", ok, round(time.time() - t0, 1), "s", flush=True)
    llm = LLMHandler()
    log = []
    for layer, dur, n in jobs:
        for k in range(n):
            seed = 1000 + 37 * k + hash(layer) % 100
            p = GenerationParams(caption=PROMPTS[layer], lyrics="[Instrumental]", instrumental=True,
                                 bpm=BPM[layer], keyscale="D minor", timesignature="4", duration=dur,
                                 inference_steps=8, seed=seed, thinking=False, use_cot_metas=False,
                                 use_cot_caption=False, use_cot_language=False)
            c = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format="wav")
            t1 = time.time()
            res = generate_music(dit, llm, p, c, save_dir=os.path.join(out, f"{layer}_{k}"))
            el = time.time() - t1
            files = []
            for root, _, fs in os.walk(os.path.join(out, f"{layer}_{k}")):
                files += [os.path.join(root, f) for f in fs if f.endswith((".wav", ".flac", ".mp3"))]
            print(f"{layer} v{k} seed={seed} {dur}s -> {el:.0f}s  {files}", flush=True)
            log.append(dict(layer=layer, k=k, seed=seed, dur=dur, secs=round(el, 1), files=files,
                            ok=bool(getattr(res, 'success', True))))
            json.dump(log, open(os.path.join(out, "gen_log.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
