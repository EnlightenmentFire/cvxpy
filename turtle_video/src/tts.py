"""Narration: Qwen3-TTS Base voice clone of the VoiceDesign candidate, per line,
with pitch gate, ASR readback, tempo, pause compression, 50 Hz HPF, -18 dBFS RMS.

usage: python tts.py OUTDIR [line_id ...]      (no ids = whole script, in order)
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
import torch
from scipy.signal import butter, sosfiltfilt, resample_poly

VOICE = os.environ.get("VOICE_DIR", "/tmp/claude-0/-home-user-cvxpy/78685b54-039d-5b0e-946b-2cbac616b0ef/scratchpad/voice")
sys.path.insert(0, VOICE)
from f0 import median_f0          # noqa: E402
from asr import transcribe         # noqa: E402
import cn2an                       # noqa: E402
from pypinyin import lazy_pinyin   # noqa: E402
from script_data import SEGMENTS   # noqa: E402

REF_WAV = os.path.join(VOICE, "design_cand_seed44.wav")
REF_TEXT = "一九八三年的秋天，芝加哥有两个交易员打了一个赌。一个说，交易这门本事可以教会；另一个说，教不会。为了分出输赢，他们登报招来了一群外行。"
TEMPO = 1.16          # narration speed-up (formant preserved)
F0_LO, F0_HI = 85.0, 105.0
MAX_TRIES = 5
SR = 48000
TARGET_RMS_DB = -18.0
MAX_PAUSE = 0.40


# ------------------------------------------------------------------ text checks
def to_pinyin(s):
    s = s.replace("％", "%")
    s = re.sub(r"[^一-鿿0-9A-Za-z%.]", "", s)
    try:
        s = cn2an.transform(s, "an2cn")
    except Exception:
        pass
    s = s.replace("N", "恩").replace("n", "恩").replace("嗯", "恩")
    return [p for p in lazy_pinyin(s) if p.strip() and p.isalpha()]


def edit(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(b)]


def per(ref, hyp):
    a, b = to_pinyin(ref), to_pinyin(hyp)
    return edit(a, b) / max(1, len(a))


# ------------------------------------------------------------------ audio processing
def trim(x, sr, thr_db=-42, pad=0.04):
    e = np.abs(x)
    win = int(0.01 * sr)
    env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same") + 1e-12)
    thr = env.max() * 10 ** (thr_db / 20)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def compress_pauses(x, sr, max_pause=MAX_PAUSE, thr_db=-40):
    hop = int(0.01 * sr)
    n = len(x) // hop
    if n < 3:
        return x
    fr = x[:n * hop].reshape(n, hop)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    thr = rms.max() * 10 ** (thr_db / 20)
    sil = rms < thr
    out, i = [], 0
    keep = int(max_pause / 0.01)
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            run = j - i
            if run > keep and i > 0 and j < n:
                h = keep // 2
                seg_a = x[i * hop:(i + h) * hop]
                seg_b = x[(j - (keep - h)) * hop:j * hop]
                out.append(np.concatenate([seg_a, seg_b]))
            else:
                out.append(x[i * hop:j * hop])
            i = j
        else:
            j = i
            while j < n and not sil[j]:
                j += 1
            out.append(x[i * hop:j * hop])
            i = j
    out.append(x[n * hop:])
    return np.concatenate(out)


def rubberband(x, sr, tempo):
    if abs(tempo - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as td:
        a, b = os.path.join(td, "a.wav"), os.path.join(td, "b.wav")
        sf.write(a, x, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-q", "-3", "-F", f"-T{tempo:.4f}", a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, _ = sf.read(b, dtype="float32")
    return y


def finish(x, sr_in, tempo):
    x = trim(x.astype(np.float32), sr_in)
    x = rubberband(x, sr_in, tempo)
    if sr_in != SR:
        from math import gcd
        g = gcd(sr_in, SR)
        x = resample_poly(x, SR // g, sr_in // g).astype(np.float32)
    x = compress_pauses(x, SR)
    sos = butter(4, 50, btype="highpass", fs=SR, output="sos")
    x = sosfiltfilt(sos, x).astype(np.float32)
    # RMS over active speech
    hop = int(0.02 * SR)
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    r = np.sqrt((fr ** 2).mean(1) + 1e-12)
    act = r > r.max() * 10 ** (-35 / 20)
    rms = np.sqrt((fr[act] ** 2).mean()) if act.any() else np.sqrt((x ** 2).mean())
    x = x * (10 ** (TARGET_RMS_DB / 20) / max(rms, 1e-6))
    peak = np.abs(x).max()
    if peak > 0.89:
        x = np.tanh(x / 0.89) * 0.89
    fade = int(0.012 * SR)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x


# ------------------------------------------------------------------ main
def all_lines():
    for seg in SEGMENTS:
        for ln in seg["lines"]:
            yield ln


BATCH = 4


def evaluate(ln, wav, sr, out, tag):
    tempo = TEMPO * (ln["rate"] or 1.0)
    n_chars = len(re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", ln["tts"]))
    y = finish(np.asarray(wav), sr, tempo)
    tmp = os.path.join(out, f".{ln['id']}.{tag}.wav")
    sf.write(tmp, y, SR)
    f0, lo, hi = median_f0(tmp)
    hyp = transcribe(tmp)
    e = per(ln["tts"], hyp)
    dur = len(y) / SR
    cps = n_chars / dur
    ok = (F0_LO <= f0 <= F0_HI, e <= 0.08, 3.6 <= cps <= 7.5)
    score = sum(0 if o else 1 for o in ok) + e + abs(f0 - 95) / 200
    rec = dict(tag=tag, f0=round(f0, 1), per=round(e, 3), cps=round(cps, 2), dur=round(dur, 2), asr=hyp)
    return all(ok), score, tmp, rec


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    want = sys.argv[2:]
    lines = list(all_lines())
    if want:
        order = {k: i for i, k in enumerate(want)}
        lines = sorted([l for l in lines if l["id"] in order], key=lambda l: order[l["id"]])
    todo = []
    for ln in lines:
        meta_p = os.path.join(out, ln["id"] + ".json")
        if os.path.exists(meta_p) and json.load(open(meta_p)).get("tts") == ln["tts"]:
            continue
        todo.append(ln)
    print(f"{len(todo)} lines to synthesise", flush=True)
    from qwen_tts import Qwen3TTSModel
    torch.set_num_threads(4)
    m = Qwen3TTSModel.from_pretrained("/opt/models/Qwen_Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu",
                                      dtype=torch.bfloat16, attn_implementation="sdpa")
    prompt = m.create_voice_clone_prompt(ref_audio=REF_WAV, ref_text=REF_TEXT, x_vector_only_mode=False)
    tries = {ln["id"]: [] for ln in todo}
    best = {}
    queue = list(todo)
    batch_no = 0
    while queue:
        # take the head of the queue plus the closest-length neighbours among the next few
        head = queue.pop(0)
        L = len(head["tts"])
        pool = sorted(queue[:12], key=lambda l: abs(len(l["tts"]) - L))[:BATCH - 1]
        for l in pool:
            queue.remove(l)
        batch = [head] + pool
        batch_no += 1
        seed = (batch_no * 7919 + sum(len(tries[l["id"]]) for l in batch) * 104729) % (2 ** 31)
        torch.manual_seed(seed)
        t0 = time.time()
        longest = max(len(re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", l["tts"])) for l in batch)
        cap = int(12 * (longest / 2.6) * 1.5) + 36     # ~12 codec frames per second of speech
        wavs, sr = m.generate_voice_clone(text=[l["tts"] for l in batch], language=["Chinese"] * len(batch),
                                          voice_clone_prompt=prompt * len(batch), max_new_tokens=cap)
        gen_s = time.time() - t0
        for ln, wav in zip(batch, wavs):
            k = len(tries[ln["id"]])
            ok, score, tmp, rec = evaluate(ln, wav, sr, out, f"try{k}")
            rec.update(seed=seed, batch=batch_no, gen_s=round(gen_s, 1))
            tries[ln["id"]].append(rec)
            print(ln["id"], json.dumps(rec, ensure_ascii=False), flush=True)
            if ln["id"] not in best or score < best[ln["id"]][0]:
                if ln["id"] in best and os.path.exists(best[ln["id"]][1]):
                    os.remove(best[ln["id"]][1])
                best[ln["id"]] = (score, tmp, rec, ok)
            elif os.path.exists(tmp):
                os.remove(tmp)
            if ok or k + 1 >= MAX_TRIES:
                _, btmp, brec, bok = best[ln["id"]]
                os.replace(btmp, os.path.join(out, ln["id"] + ".wav"))
                meta = dict(id=ln["id"], tts=ln["tts"], text=ln["text"], tempo=TEMPO * (ln["rate"] or 1.0),
                            chosen=brec, tries=tries[ln["id"]], passed=bool(bok))
                json.dump(meta, open(os.path.join(out, ln["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
            else:
                queue.insert(min(len(queue), 2), ln)   # retry soon, with a different batch / seed


if __name__ == "__main__":
    main()
