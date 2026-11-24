"""Synthesize narration lines with Qwen3-TTS (Base model, cloned designed voice).

For every line:
  * generate with a seed,
  * check median F0 (parselmouth) is inside [F0_LO, F0_HI],
  * read it back with faster-whisper and compare toneless pinyin with the text,
  * retry with a new seed when either check fails, keep the best take.

Usage: tts_worker.py script.json out_dir [line_id ...]   (no ids = all lines)
"""
import json
import zlib
import os
import re
import sys
import time

import numpy as np
import soundfile as sf
import torch
import parselmouth
from pypinyin import lazy_pinyin, Style
from opencc import OpenCC

BUILD = "/home/user/wude_build"
BASE_MODEL = f"{BUILD}/models/Qwen3-TTS-12Hz-1.7B-Base"
REF_WAV = f"{BUILD}/voice/design_seed22.wav"
REF_TEXT = ("战国后期，齐国有一个叫邹衍的人。他看着各国的君主越来越奢侈，就写下了十几万字的文章，"
            "从开天辟地讲起，讲五种力量怎样轮流当家。")
F0_LO, F0_HI = 85.0, 105.0
MAX_TRIES = int(os.environ.get("MAX_TRIES", "5"))
SER_OK = 0.08

torch.set_num_threads(4)
cc = OpenCC("t2s")


def f0_stats(wav, sr):
    snd = parselmouth.Sound(wav.astype(np.float64), sampling_frequency=sr)
    p = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    if len(f) == 0:
        return 0.0, 0.0
    return float(np.median(f)), float(np.percentile(f, 90) - np.percentile(f, 10))


def han_only(s):
    return "".join(ch for ch in s if "一" <= ch <= "鿿")


_DIG = "零一二三四五六七八九"


def num_to_cn(n):
    """Integer -> Chinese numerals as read aloud (enough for years like 104, 221, 1000)."""
    if n == 0:
        return "零"
    units = [(1000, "千"), (100, "百"), (10, "十"), (1, "")]
    out, zero = "", False
    started = False
    for u, name in units:
        d = n // u
        n %= u
        if d:
            if zero and started:
                out += "零"
            out += ("" if (u == 10 and d == 1 and not started) else _DIG[d]) + name
            started, zero = True, False
        elif started:
            zero = True
    return out


def pinyin_seq(s):
    import re as _re
    s = _re.sub(r"\d+", lambda m: num_to_cn(int(m.group(0))), s)
    return lazy_pinyin(han_only(s), style=Style.NORMAL, errors="ignore")


def edit_distance(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[len(b)]


def diff_report(exp, got):
    """Return list of (expected_syllable, got_syllable) mismatches via alignment."""
    n, m = len(exp), len(got)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        D[i][0] = i
    for j in range(m + 1):
        D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (exp[i - 1] != got[j - 1]))
    i, j, out = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + (exp[i - 1] != got[j - 1]):
            if exp[i - 1] != got[j - 1]:
                out.append((i - 1, exp[i - 1], got[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1:
            out.append((i - 1, exp[i - 1], "-"))
            i -= 1
        else:
            out.append((i, "-", got[j - 1]))
            j -= 1
    return out[::-1]


class ASR:
    def __init__(self):
        from faster_whisper import WhisperModel
        self.m = WhisperModel(f"{BUILD}/models/fw-large-v3-turbo", device="cpu",
                              compute_type="int8", cpu_threads=4)

    def __call__(self, wav, sr):
        import librosa
        if sr != 16000:
            wav = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000)
        segs, _ = self.m.transcribe(wav.astype(np.float32), language="zh", beam_size=5,
                                    initial_prompt="以下是普通话朗读的历史纪录片旁白。",
                                    condition_on_previous_text=False, vad_filter=False)
        return cc.convert("".join(s.text for s in segs)).strip()


def main():
    script_json, out_dir = sys.argv[1], sys.argv[2]
    ids = set(sys.argv[3:])
    os.makedirs(out_dir, exist_ok=True)
    segs = json.load(open(script_json, encoding="utf-8"))
    lines = [l for s in segs for l in s["lines"]]
    if ids:
        lines = [l for l in lines if l["id"] in ids]

    from qwen_tts import Qwen3TTSModel
    t0 = time.time()
    model = Qwen3TTSModel.from_pretrained(BASE_MODEL, device_map="cpu", dtype=torch.bfloat16,
                                          attn_implementation="sdpa")
    ref, rsr = sf.read(REF_WAV)
    prompt = model.create_voice_clone_prompt(ref_audio=(ref.astype(np.float32), rsr), ref_text=REF_TEXT)
    asr = ASR()
    print(f"models ready in {time.time()-t0:.1f}s", flush=True)

    for ln in lines:
        meta_path = f"{out_dir}/{ln['id']}.json"
        if os.path.exists(meta_path):
            continue
        text = ln["tts"]
        exp = pinyin_seq(text)
        n_han = len(han_only(text))
        max_tokens = int(12.5 * (n_han / 2.0 + 6))
        best = None
        for k in range(MAX_TRIES):
            seed = 1000 + 37 * k + (zlib.crc32(ln["id"].encode()) % 997 if k else 0)
            torch.manual_seed(seed)
            np.random.seed(seed % (2 ** 31))
            t1 = time.time()
            wavs, sr = model.generate_voice_clone(text=text, language="Chinese",
                                                  voice_clone_prompt=prompt,
                                                  max_new_tokens=max_tokens)
            w = np.asarray(wavs[0], dtype=np.float32)
            dur = len(w) / sr
            f0, f0span = f0_stats(w, sr)
            got_txt = asr(w, sr)
            got = pinyin_seq(got_txt)
            ser = edit_distance(exp, got) / max(1, len(exp))
            rate = n_han / max(dur, 0.1)
            ok_f0 = F0_LO <= f0 <= F0_HI
            ok_rate = 1.6 <= rate <= 6.5
            score = ser * 3 + (0 if ok_f0 else min(abs(f0 - 95) / 40, 1.0)) + (0 if ok_rate else 1.0)
            take = dict(seed=seed, dur=dur, f0=f0, f0span=f0span, ser=ser, asr=got_txt, rate=rate,
                        gen_s=time.time() - t1, score=score,
                        diffs=[d for d in diff_report(exp, got)][:20])
            print(f"{ln['id']} try{k} seed={seed} dur={dur:.1f}s f0={f0:.1f} ser={ser:.3f} "
                  f"rate={rate:.2f}c/s gen={take['gen_s']:.0f}s | {got_txt[:40]}", flush=True)
            if best is None or score < best[0]["score"]:
                best = (take, w, sr)
            if ok_f0 and ok_rate and ser <= SER_OK:
                break
        take, w, sr = best
        sf.write(f"{out_dir}/{ln['id']}.wav", w, sr)
        take.update(id=ln["id"], kind=ln["kind"], text=ln["text"], tts=text)
        json.dump(take, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"== {ln['id']} kept seed={take['seed']} f0={take['f0']:.1f} ser={take['ser']:.3f}", flush=True)


if __name__ == "__main__":
    main()
