# -*- coding: utf-8 -*-
"""批量配音（每批 N 句一起合成，摊薄内存带宽开销）。规则与 tts_build.py 相同：
音高 85–105 Hz、拼音错误率 ≤10%，不合格换 seed 重来（最多 MAX_TRIES 次，保留最好的一版）。
用法：python3 tts_batch.py [段落号...] [--bs 4] [--try-offset K]
"""
import hashlib
import os
import sys
import time

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import B                                         # noqa: E402
from tts_build import (OUT, RAW, REF_WAV, REF_TEXT, F0_LO, F0_HI, CER_MAX, MAX_TRIES, TEMPO,  # noqa: E402
                       cer, median_f0, postprocess, load_manifest, save_manifest)


def main():
    import torch
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    from asr_check import transcribe
    args = sys.argv[1:]
    bs = int(args[args.index("--bs") + 1]) if "--bs" in args else 4
    k0 = int(args[args.index("--try-offset") + 1]) if "--try-offset" in args else 0
    secs = [int(a) for a in args if a.isdigit() and (args.index(a) == 0 or args[args.index(a) - 1] not in ("--bs", "--try-offset"))]
    man = load_manifest()
    todo = [x for x in B if x["say"] and (not secs or x["sec"] in secs)]
    if k0 == 0:
        todo = [x for x in todo if not (x["id"] in man and man[x["id"]].get("ok") and man[x["id"]].get("say") == x["say"])]
    else:
        todo = [x for x in todo if x["id"] in man and not man[x["id"]].get("ok")]
    print(f"{len(todo)} beats, batch size {bs}", flush=True)
    if not todo:
        return
    model = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.bfloat16,
                                          device_map="cpu", attn_implementation="sdpa")
    prompt = model.create_voice_clone_prompt(ref_audio=REF_WAV, ref_text=REF_TEXT, x_vector_only_mode=False)
    tries = {x["id"]: k0 for x in todo}
    best = {}
    queue = list(todo)
    while queue:
        batch, queue = queue[:bs], queue[bs:]
        seed = int(hashlib.md5("".join(x["id"] for x in batch).encode()).hexdigest()[:6], 16) + 7919 * max(tries[x["id"]] for x in batch)
        torch.manual_seed(seed)
        t0 = time.time()
        wavs, sr = model.generate_voice_clone(text=[x["say"] for x in batch], language=["Chinese"] * len(batch),
                                              voice_clone_prompt=prompt * len(batch))
        dt = time.time() - t0
        for x, w in zip(batch, wavs):
            k = tries[x["id"]]
            w = np.asarray(w, dtype=np.float32)
            rawp = os.path.join(RAW, f"{x['id']}_b{k}.wav")
            sf.write(rawp, w, sr)
            f0 = median_f0(w, sr)
            hyp = transcribe(rawp)
            e = cer(x["say"], hyp)
            ok = (F0_LO <= f0 <= F0_HI) and e <= CER_MAX
            score = (0 if F0_LO <= f0 <= F0_HI else 1) * 10 + e + abs(f0 - 95) / 1000
            print(f"{x['id']} try{k} f0={f0:.1f} cer={e:.3f} dur={len(w) / sr:.1f}s batch={dt:.0f}s ok={ok} | {hyp}",
                  flush=True)
            cand = dict(seed=seed, f0=f0, cer=e, asr=hyp, raw=rawp, sr=sr, score=score, ok=ok)
            if x["id"] not in best or score < best[x["id"]]["score"]:
                best[x["id"]] = cand
            tries[x["id"]] = k + 1
            if not ok and tries[x["id"]] < k0 + MAX_TRIES:
                queue.append(x)
                continue
            bb = best[x["id"]]
            wb, srb = sf.read(bb["raw"], dtype="float32")
            y = postprocess(wb, srb, TEMPO[x["tempo"]], x["id"])
            outp = os.path.join(OUT, f"{x['id']}.wav")
            sf.write(outp, y, srb)
            man = load_manifest()
            man[x["id"]] = dict(say=x["say"], seed=bb["seed"], f0=round(bb["f0"], 1), cer=round(bb["cer"], 3),
                                asr=bb["asr"], ok=bool(bb["ok"]), dur=round(len(y) / srb, 3), tempo=TEMPO[x["tempo"]],
                                file=outp)
            save_manifest(man)


if __name__ == "__main__":
    main()
