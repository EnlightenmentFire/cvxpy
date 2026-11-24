"""Score MusicGen takes for 'supports the voice, never competes with it' and flag defects.

Lower competition = less energy and fewer transients in the 1-4 kHz speech band, steady level.
Defects = vocal-like content (ASR finds words), dropouts, clipping, noise bursts.
Also writes a spectrogram sheet for a visual check."""
import glob
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import stft

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tts"))


def analyse(path):
    w, sr = sf.read(path, dtype="float32")
    m = w.mean(axis=1) if w.ndim > 1 else w
    f, t, Z = stft(m, sr, nperseg=2048, noverlap=1536)
    P = np.abs(Z) ** 2 + 1e-12
    tot = P.sum(axis=0)
    band = P[(f >= 1000) & (f <= 4000)].sum(axis=0)
    speech_ratio = float(np.median(band / tot))
    # transient density in the speech band: positive spectral flux
    B = np.log(P[(f >= 1000) & (f <= 5000)] + 1e-9)
    flux = np.maximum(0, np.diff(B, axis=1)).mean(axis=0)
    trans = float(np.mean(flux > np.median(flux) + 2.5 * flux.std()))
    # level stability (short-term RMS in dB, 400 ms)
    hop = int(0.4 * sr)
    rms = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(m) - hop, hop)])
    db = 20 * np.log10(rms)
    lrange = float(np.percentile(db, 95) - np.percentile(db, 10))
    jumps = float(np.max(np.abs(np.diff(db)))) if len(db) > 1 else 0.0
    dropouts = int(np.sum(db < np.median(db) - 25))
    clip = float(np.mean(np.abs(w) > 0.99))
    flat = np.exp(np.mean(np.log(P), axis=0)) / np.mean(P, axis=0)
    noise = float(np.median(flat))
    return dict(path=path, speech_ratio=round(speech_ratio, 3), transients=round(trans, 3), lrange=round(lrange, 1),
                max_jump_db=round(jumps, 1), dropouts=dropouts, clip=round(clip, 4), flatness=round(noise, 3),
                level_db=round(float(np.median(db)), 1))


def vocal_check(path):
    from audio_utils import asr_model
    w, sr = sf.read(path, dtype="float32")
    m = w.mean(axis=1) if w.ndim > 1 else w
    from scipy.signal import resample_poly
    m16 = resample_poly(m, 1, 2) if sr == 32000 else m
    segs, info = asr_model().transcribe(m16.astype(np.float32), vad_filter=True, beam_size=1)
    segs = list(segs)
    words = "".join(s.text for s in segs if s.no_speech_prob < 0.5)
    return words.strip()


def score(a):
    s = 0.0
    s += a["speech_ratio"] * 10          # energy where the voice lives
    s += a["transients"] * 8             # clicky / busy in the speech band
    s += max(0, a["lrange"] - 8) * 0.15  # uneven level
    s += max(0, a["max_jump_db"] - 6) * 0.2
    s += a["dropouts"] * 0.5 + a["clip"] * 50 + max(0, a["flatness"] - 0.3) * 5
    return round(s, 3)


if __name__ == "__main__":
    takes = sorted(glob.glob(os.path.join(sys.argv[1], "*_v[0-9].wav")))
    res = []
    for p in takes:
        a = analyse(p)
        a["vocals"] = vocal_check(p) if "--asr" in sys.argv else ""
        a["score"] = score(a) + (5 if len(a["vocals"]) > 6 else 0)
        res.append(a)
        print(json.dumps(a, ensure_ascii=False), flush=True)
    json.dump(res, open(os.path.join(sys.argv[1], "scores.json"), "w"), ensure_ascii=False, indent=1)
    if "--choose" in sys.argv:
        best = {}
        for a in res:
            fn = os.path.basename(a["path"])
            if "_ext" in fn:
                continue
            key = fn.rsplit("_v", 1)[0]
            ok = len(a["vocals"]) <= 6
            cand = (0 if ok else 1, a["score"], a["speech_ratio"], fn)
            if key not in best or cand < best[key]:
                best[key] = cand
        choices = {k: [v[3]] for k, v in best.items()}
        json.dump(choices, open(os.path.join(sys.argv[1], "choices.json"), "w"), indent=1)
        print("choices", choices)
    # spectrogram sheet
    from PIL import Image, ImageDraw, ImageFont
    rows = []
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 18, index=2)
    for a in res:
        w, sr = sf.read(a["path"], dtype="float32")
        m = w.mean(axis=1)
        f, t, Z = stft(m, sr, nperseg=1024, noverlap=768)
        S = 20 * np.log10(np.abs(Z[f <= 8000]) + 1e-6)
        S = np.clip((S - S.max() + 70) / 70, 0, 1)[::-1]
        im = Image.fromarray((S * 255).astype(np.uint8)).resize((900, 140))
        canvas = Image.new("RGB", (1220, 150), (15, 15, 20))
        canvas.paste(im.convert("RGB"), (310, 5))
        d = ImageDraw.Draw(canvas)
        d.text((8, 10), os.path.basename(a["path"]), font=font, fill=(230, 230, 230))
        d.text((8, 40), f"score {a['score']}  speech {a['speech_ratio']}", font=font, fill=(200, 200, 200))
        d.text((8, 70), f"trans {a['transients']}  lr {a['lrange']}dB  jump {a['max_jump_db']}", font=font, fill=(200, 200, 200))
        d.text((8, 100), f"vocals: {a['vocals'][:18]}", font=font, fill=(255, 140, 140) if a['vocals'] else (140, 200, 140))
        rows.append(canvas)
    if rows:
        sheet = Image.new("RGB", (1220, 150 * len(rows)), (0, 0, 0))
        for i, r in enumerate(rows):
            sheet.paste(r, (0, 150 * i))
        sheet.save(os.path.join(sys.argv[1], "spectrograms.jpg"), quality=85)


def chroma(path):
    """12-bin pitch-class profile (for checking that two takes share a key)."""
    w, sr = sf.read(path, dtype="float32")
    m = w.mean(axis=1) if w.ndim > 1 else w
    f, t, Z = stft(m, sr, nperseg=8192, noverlap=4096)
    P = np.abs(Z) ** 2
    sel = (f > 60) & (f < 2000)
    pc = np.round(12 * np.log2(f[sel] / 440.0)).astype(int) % 12
    prof = np.zeros(12)
    for k in range(12):
        prof[k] = P[sel][pc == k].sum()
    return prof / (np.linalg.norm(prof) + 1e-9)


def compatible(a, b, thr=0.93):
    return float(np.dot(chroma(a), chroma(b))) >= thr
