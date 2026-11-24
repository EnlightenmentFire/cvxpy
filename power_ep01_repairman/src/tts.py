"""Narration pipeline: Qwen3-TTS (VoiceDesign reference -> Base clone), QC, post-processing.

python tts.py synth  [ids...]      generate raw takes (batched), QC, keep the best take per line
python tts.py process [ids...]     trim / speed-up (rubberband, formant-preserving) / pause cap / HPF / level
python tts.py report               print QC table

QC per line: median F0 (parselmouth) must be 85–105 Hz; ASR (faster-whisper large-v3-turbo) pinyin error
<= 0.06 for Chinese. Failing lines are re-generated with a new seed (no global pitch shifting).
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

WORK = os.environ.get("EP_WORK", "/tmp/claude-0/-home-user-cvxpy/23149d0a-3dd1-5cf6-8dec-2980a0f4c270/scratchpad/work")
RAW = os.path.join(WORK, "tts/raw")
PROC = os.path.join(WORK, "tts/proc")
QC = os.path.join(WORK, "tts/qc.json")
REF_WAV = os.path.join(WORK, "voice/design_seed3.wav")
REF_TEXT = "上世纪五十年代，法国一家国营烟草厂里，组织图上最不起眼的一群人，成了车间里真正说了算的人。"
os.makedirs(RAW, exist_ok=True)
os.makedirs(PROC, exist_ok=True)
sys.path.insert(0, os.path.join(WORK, "voice"))

from script_data import BY_ID, LINES  # noqa: E402

F0_LO, F0_HI = 85.0, 105.0
ASR_MAX = 0.06
TEMPO = {"narr": 1.18, "quote": 1.08}
PAUSE_CAP = 0.40


def load_qc():
    if os.path.exists(QC):
        return json.load(open(QC))
    return {}


def save_qc(q):
    json.dump(q, open(QC, "w"), ensure_ascii=False, indent=1)


def f0_median(path):
    import parselmouth
    snd = parselmouth.Sound(path)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else float("nan")


def asr_err(path, line):
    from asr import pinyin_err, transcribe
    if line["lang"] == "Chinese":
        hyp = transcribe(path, lang="zh")
        return pinyin_err(line["tts"], hyp), hyp
    lang = {"English": "en", "French": "fr"}[line["lang"]]
    hyp = transcribe(path, lang=lang)
    import re
    a = re.sub(r"[^a-z' ]", "", line["tts"].lower()).split()
    b = re.sub(r"[^a-z' ]", "", hyp.lower()).split()
    from asr import edit
    return edit(a, b) / max(1, len(a)), hyp


def synth(ids, max_tries=4, batch=4):
    import torch
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained(os.path.join(WORK, "models/Qwen3-TTS-12Hz-1.7B-Base"), device_map="cpu",
                                      dtype=torch.bfloat16)
    prompt = m.create_voice_clone_prompt(ref_audio=REF_WAV, ref_text=REF_TEXT)
    q = load_qc()
    todo = [i for i in ids if BY_ID[i]["tts"] and not q.get(i, {}).get("ok")]
    tries = {i: q.get(i, {}).get("tries", 0) for i in todo}
    while todo:
        chunk = todo[:batch]
        seed = 1000 + sum(tries[i] for i in chunk) * 7 + len(chunk)
        torch.manual_seed(seed)
        texts = [BY_ID[i]["tts"] for i in chunk]
        langs = [BY_ID[i]["lang"] for i in chunk]
        wavs, sr = m.generate_voice_clone(text=texts, language=langs, voice_clone_prompt=prompt * len(chunk))
        for i, w in zip(chunk, wavs):
            tries[i] += 1
            path = os.path.join(RAW, f"{i}_t{tries[i]}.wav")
            sf.write(path, w, sr)
            f0 = f0_median(path)
            err, hyp = asr_err(path, BY_ID[i])
            ok_f0 = F0_LO <= f0 <= F0_HI
            ok_asr = err <= (ASR_MAX if BY_ID[i]["lang"] == "Chinese" else 0.15)
            rec = q.get(i, {"takes": []})
            rec["takes"].append(dict(path=path, f0=round(f0, 1), err=round(err, 3), hyp=hyp, dur=round(len(w) / sr, 2)))
            rec["tries"] = tries[i]
            if ok_f0 and ok_asr:
                rec["ok"] = True
                rec["best"] = path
            elif tries[i] >= max_tries:
                # keep the take closest to spec; flag for manual attention
                best = min(rec["takes"], key=lambda d: (d["err"] > ASR_MAX) * 10 + abs(d["f0"] - 95) / 10 + d["err"] * 5)
                rec["best"] = best["path"]
                rec["ok"] = False
                rec["flag"] = True
            q[i] = rec
            save_qc(q)
            print(f"{i} try{tries[i]} f0={f0:.1f} err={err:.3f} {'OK' if ok_f0 and ok_asr else 'retry'} | {hyp}", flush=True)
        todo = [i for i in todo if not q.get(i, {}).get("ok") and not q.get(i, {}).get("flag")]


# ------------------------------------------------------------------ post-processing
def _trim(y, sr, thr_db=-42, pad=0.06):
    env = np.abs(y)
    win = int(sr * 0.02)
    e = np.convolve(env, np.ones(win) / win, mode="same")
    thr = 10 ** (thr_db / 20) * max(1e-6, np.max(e))
    idx = np.where(e > thr)[0]
    if len(idx) == 0:
        return y
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(y), idx[-1] + int(pad * sr))
    return y[a:b]


def _cap_pauses(y, sr, cap=PAUSE_CAP, thr_db=-40):
    win = int(sr * 0.02)
    e = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, mode="same"))
    thr = 10 ** (thr_db / 20) * max(1e-6, np.max(e))
    silent = e < thr
    out = []
    i = 0
    n = len(y)
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            L = j - i
            if L > cap * sr:
                keep = int(cap * sr)
                half = keep // 2
                seg_ = np.concatenate([y[i:i + half], y[j - (keep - half):j]])
                # short crossfade-free join is fine inside silence
                out.append(seg_)
            else:
                out.append(y[i:j])
            i = j
        else:
            j = i
            while j < n and not silent[j]:
                j += 1
            out.append(y[i:j])
            i = j
    return np.concatenate(out) if out else y


def _hpf(y, sr, fc=50.0):
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, fc / (sr / 2), btype="highpass", output="sos")
    return sosfiltfilt(sos, y)


def _rubberband(inp, out, tempo):
    subprocess.run(["rubberband", "-q", "-T", f"{tempo:.4f}", "-F", "-3", inp, out], check=True)


def process(ids, target_rms_db=-18.0):
    q = load_qc()
    durs = {}
    for i in ids:
        ln = BY_ID[i]
        if not ln["tts"]:
            continue
        rec = q.get(i)
        if not rec or "best" not in rec:
            print("missing", i)
            continue
        y, sr = sf.read(rec["best"], dtype="float64")
        y = _trim(y, sr)
        tmp_in = os.path.join(PROC, f"_{i}_in.wav")
        tmp_out = os.path.join(PROC, f"_{i}_out.wav")
        sf.write(tmp_in, y, sr)
        _rubberband(tmp_in, tmp_out, TEMPO[ln["kind"]])
        y, sr = sf.read(tmp_out, dtype="float64")
        os.remove(tmp_in)
        os.remove(tmp_out)
        y = _cap_pauses(y, sr)
        y = _trim(y, sr, pad=0.04)
        y = _hpf(y, sr)
        # level: RMS over voiced frames
        win = int(sr * 0.05)
        fr = y[: len(y) // win * win].reshape(-1, win)
        r = np.sqrt((fr ** 2).mean(axis=1))
        voiced = r[r > np.max(r) * 0.1]
        rms = np.sqrt(np.mean(voiced ** 2)) if len(voiced) else np.sqrt(np.mean(y ** 2))
        y = y * (10 ** (target_rms_db / 20) / max(1e-9, rms))
        pk = np.max(np.abs(y))
        if pk > 0.97:
            y = y * 0.97 / pk
        # 8 ms fades
        f = int(sr * 0.008)
        y[:f] *= np.linspace(0, 1, f)
        y[-f:] *= np.linspace(1, 0, f)
        path = os.path.join(PROC, f"{i}.wav")
        sf.write(path, y.astype(np.float32), sr)
        durs[i] = round(len(y) / sr, 3)
        print(f"{i}: {durs[i]:.2f}s", flush=True)
    dpath = os.path.join(WORK, "tts/durations.json")
    old = json.load(open(dpath)) if os.path.exists(dpath) else {}
    old.update(durs)
    json.dump(old, open(dpath, "w"), indent=1)


def report():
    q = load_qc()
    for ln in LINES:
        r = q.get(ln["id"])
        if not r:
            continue
        b = [d for d in r["takes"] if d["path"] == r.get("best")]
        b = b[0] if b else r["takes"][-1]
        print(f"{ln['id']:6s} ok={r.get('ok')} tries={r['tries']} f0={b['f0']} err={b['err']} dur={b['dur']}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    ids = sys.argv[2:]
    if ids == ["sample"]:
        ids = [d["id"] for d in LINES if d["sec"] in ("cold", "intro")]
    elif ids == ["all"] or not ids:
        ids = [d["id"] for d in LINES]
    if cmd == "synth":
        synth(ids)
    elif cmd == "process":
        process(ids)
    elif cmd == "report":
        report()
