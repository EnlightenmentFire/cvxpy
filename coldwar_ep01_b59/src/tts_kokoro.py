"""Kokoro-82M v1.1-zh (Apache-2.0) narration synthesis.

Run with the Python 3.12 venv that has kokoro==0.9.4 + misaki[zh]==0.9.4.

Usage:
  python tts_kokoro.py audition OUT_DIR            # all male voices, one line each + pitch stats
  python tts_kokoro.py sample VOICE OUT.wav [SPEED] # ~20 s style sample
  python tts_kokoro.py lines VOICE LINES.json OUT_DIR [SPEED]  # one wav per narration line
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
import torch
from kokoro import KModel, KPipeline

REPO_ID = "hexgrad/Kokoro-82M-v1.1-zh"
SR = 24000

# Latin tokens that appear in the spoken text -> Kokoro (misaki) phonemes.
EN_PHONEMES = {
    "U": "jˈu",
    "B": "bˈi",
    "K": "kˈA",
    "DEFCON": "dˈɛfkɑn",
}


def en_callable(text):
    key = text.upper().replace("-", "").replace(" ", "")
    if key in EN_PHONEMES:
        return EN_PHONEMES[key]
    # spell letters
    out = []
    for ch in key:
        if ch in EN_PHONEMES:
            out.append(EN_PHONEMES[ch])
    return " ".join(out) if out else ""


_model = None
_pipe = None


def get_pipe():
    global _model, _pipe
    if _model is None:
        torch.set_num_threads(max(1, os.cpu_count() - 1))
        _model = KModel(repo_id=REPO_ID).eval()
        _pipe = KPipeline(lang_code="z", repo_id=REPO_ID, model=_model, en_callable=en_callable)
    return _pipe


def synth(text, voice, speed=1.0):
    pipe = get_pipe()
    chunks = []
    for res in pipe(text, voice=voice, speed=speed):
        a = res.audio
        if a is None:
            continue
        chunks.append(a.detach().cpu().numpy() if hasattr(a, "detach") else np.asarray(a))
    if not chunks:
        return np.zeros(1, np.float32)
    return np.concatenate(chunks).astype(np.float32)


def f0_track(x, sr=SR, fmin=60, fmax=260):
    """Very small autocorrelation pitch tracker -> array of voiced F0 values."""
    frame = int(0.04 * sr)
    hop = int(0.01 * sr)
    lag_min = int(sr / fmax)
    lag_max = int(sr / fmin)
    rms_all = np.sqrt(np.mean(x ** 2)) + 1e-9
    f0s = []
    for s in range(0, len(x) - frame, hop):
        fr = x[s:s + frame] * np.hanning(frame)
        if np.sqrt(np.mean(fr ** 2)) < 0.3 * rms_all:
            continue
        ac = np.correlate(fr, fr, mode="full")[frame - 1:]
        ac = ac / (ac[0] + 1e-9)
        seg = ac[lag_min:lag_max]
        k = int(np.argmax(seg))
        if seg[k] > 0.55:
            f0s.append(sr / (lag_min + k))
    return np.array(f0s)


def voices_male():
    from huggingface_hub import list_repo_files
    fs = list_repo_files(REPO_ID)
    return sorted(f.split("/")[1][:-3] for f in fs if f.startswith("voices/zm_"))


AUDITION_TEXT = "这一幕，没有发生。可是在一九六二年十月二十七日的晚上，它离发生，只差一个人。"
SAMPLE_TEXT = (
    "这一幕，没有发生。可是在一九六二年十月二十七日的晚上，它离发生，只差一个人。"
    "十月二十七日，星期六。后来，人们叫它黑色星期六。"
    "三个地方都离华盛顿和莫斯科很远。这一天，扳机落在了离中心最远的人手里。"
)


def main():
    mode = sys.argv[1]
    if mode == "audition":
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        rows = []
        for v in voices_male():
            a = synth(AUDITION_TEXT, v, 1.0)
            sf.write(os.path.join(out, f"{v}.wav"), a, SR)
            f0 = f0_track(a)
            med = float(np.median(f0)) if len(f0) else 0.0
            spread = float(np.percentile(f0, 90) - np.percentile(f0, 10)) if len(f0) else 0.0
            rows.append({"voice": v, "dur": len(a) / SR, "f0_med": med, "f0_p10_p90": spread})
            print(json.dumps(rows[-1]), flush=True)
        json.dump(rows, open(os.path.join(out, "pitch.json"), "w"), indent=1)
    elif mode == "sample":
        v, path = sys.argv[2], sys.argv[3]
        speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        a = synth(SAMPLE_TEXT, v, speed)
        sf.write(path, a, SR)
        print(path, len(a) / SR)
    elif mode == "lines":
        v, lines_path, out = sys.argv[2], sys.argv[3], sys.argv[4]
        speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
        os.makedirs(out, exist_ok=True)
        lines = json.load(open(lines_path))
        for ln in lines:
            p = os.path.join(out, f"{ln['id']}.wav")
            a = synth(ln["tts"], v, ln.get("speed", speed))
            sf.write(p, a, SR)
            print(ln["id"], round(len(a) / SR, 2), flush=True)


if __name__ == "__main__":
    main()
