"""Qwen3-TTS (Apache-2.0) narration pipeline, CPU bf16.

  design  OUT_DIR [N]          VoiceDesign: N candidate reference voices from a text description
  clone   REF.wav LINES.json OUT_DIR     Base: clone the designed voice, line by line, with QC + retries

No real person's voice is used anywhere: the reference voice is generated from a text description.
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(__file__))
import voiceqc as Q  # noqa: E402

VD_REPO = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
BASE_REPO = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
VOICE_DESC = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
REF_TEXT = ("一九六二年的秋天，大西洋深处，一艘潜艇在黑暗里航行。"
            "没有人知道它带着什么，也没有人知道，接下来会发生什么。")
TARGET_F0 = 90.0


def load(repo):
    from qwen_tts import Qwen3TTSModel
    torch.set_num_threads(os.cpu_count())
    t = time.time()
    m = Qwen3TTSModel.from_pretrained(repo, device_map="cpu", dtype=torch.bfloat16, attn_implementation="sdpa")
    print(f"loaded {repo} in {time.time() - t:.1f}s", flush=True)
    return m


def lang_name(model):
    try:
        langs = model.model.get_supported_languages()
        for cand in ("chinese", "Chinese", "zh"):
            if langs and cand in langs:
                return cand
        print("supported languages:", langs)
    except Exception:
        pass
    return "Chinese"


def design(out_dir, n=3, seeds=None):
    os.makedirs(out_dir, exist_ok=True)
    m = load(VD_REPO)
    lang = lang_name(m)
    seeds = seeds or [101 + i for i in range(n)]
    rows = []
    for s in seeds:
        torch.manual_seed(s)
        t = time.time()
        wavs, sr = m.generate_voice_design(text=REF_TEXT, instruct=VOICE_DESC, language=lang)
        x = np.asarray(wavs[0], np.float32)
        p = os.path.join(out_dir, f"design_seed{s}.wav")
        sf.write(p, x, sr)
        f0 = Q.f0_median(x, sr)
        row = {"seed": s, "path": p, "sr": sr, "dur": round(len(x) / sr, 2), "f0_median": round(f0, 1),
               "gen_s": round(time.time() - t, 1), "rate_cps": round(Q.speech_rate(REF_TEXT, x, sr), 2)}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    best = min(rows, key=lambda r: abs(r["f0_median"] - TARGET_F0))
    json.dump({"candidates": rows, "chosen": best, "desc": VOICE_DESC, "ref_text": REF_TEXT},
              open(os.path.join(out_dir, "design.json"), "w"), ensure_ascii=False, indent=1)
    print("CHOSEN", json.dumps(best, ensure_ascii=False))


def clone(ref_wav, lines_path, out_dir, max_tries=6, ser_max=0.08, batch=4):
    os.makedirs(out_dir, exist_ok=True)
    lines = json.load(open(lines_path))
    m = load(BASE_REPO)
    lang = lang_name(m)
    prompt = m.create_voice_clone_prompt(ref_audio=ref_wav, ref_text=REF_TEXT)
    report = {}
    rp = os.path.join(out_dir, "qc.json")
    if os.path.exists(rp):
        report = json.load(open(rp))
    todo = [ln for ln in lines if not report.get(ln["id"], {}).get("ok")]
    tries = {ln["id"]: report.get(ln["id"], {}).get("tries", 0) for ln in lines}
    round_ = 0
    while todo and round_ < max_tries:
        round_ += 1
        nxt = []
        for b0 in range(0, len(todo), batch):
            chunk = todo[b0:b0 + batch]
            seed = 1000 + round_ * 97 + b0 + 7919 * sum(tries[c['id']] for c in chunk)
            torch.manual_seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=[c["tts"] for c in chunk], language=[lang] * len(chunk),
                                              voice_clone_prompt=prompt * len(chunk) if len(prompt) == 1 else prompt,
                                              non_streaming_mode=True)
            dt = time.time() - t
            for c, w in zip(chunk, wavs):
                x = np.asarray(w, np.float32)
                x = Q.trim_silence(x, sr)
                tries[c["id"]] += 1
                f0 = Q.f0_median(x, sr)
                heard = Q.asr(x, sr)
                ser = Q.syllable_error_rate(c["tts"], heard)
                ok = (Q.PITCH_LO <= f0 <= Q.PITCH_HI) and ser <= ser_max
                p = os.path.join(out_dir, f"{c['id']}_try{tries[c['id']]}.wav")
                sf.write(p, x, sr)
                rec = {"text": c["text"], "tts": c["tts"], "kind": c.get("kind", "N"), "path": p, "sr": sr,
                       "seed": seed, "tries": tries[c["id"]], "f0_median": round(f0, 1), "asr": heard,
                       "ser": round(ser, 3), "diff": Q.diff_report(c["tts"], heard), "dur": round(len(x) / sr, 2),
                       "rate_cps": round(Q.speech_rate(c["tts"], x, sr), 2), "ok": ok}
                prev = report.get(c["id"])
                # keep the best attempt so far (ok first, then lowest ser, then pitch closeness)
                def score(r):
                    return (r["ok"], -r["ser"], -abs(r["f0_median"] - 95))
                if prev is None or score(rec) > score(prev):
                    report[c["id"]] = rec
                else:
                    report[c["id"]]["tries"] = tries[c["id"]]
                print(f"[{c['id']}] try{tries[c['id']]} f0={f0:.1f} ser={ser:.3f} ok={ok} "
                      f"rate={rec['rate_cps']} heard={heard}", flush=True)
                if not ok:
                    nxt.append(c)
            print(f"  batch of {len(chunk)} in {dt:.1f}s", flush=True)
            json.dump(report, open(rp, "w"), ensure_ascii=False, indent=1)
        todo = nxt
    json.dump(report, open(rp, "w"), ensure_ascii=False, indent=1)
    bad = [k for k, v in report.items() if not v["ok"]]
    print("DONE; failing:", bad)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "design":
        design(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3)
    elif cmd == "design_more":
        design(sys.argv[2], seeds=[int(s) for s in sys.argv[3].split(",")])
    elif cmd == "clone":
        clone(sys.argv[2], sys.argv[3], sys.argv[4],
              ser_max=float(sys.argv[5]) if len(sys.argv) > 5 else 0.0,
              max_tries=int(sys.argv[6]) if len(sys.argv) > 6 else 6)
