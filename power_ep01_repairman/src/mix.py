"""Assemble narration + score into the final soundtrack.

python mix.py OUT.wav [T_END]       full mix (optionally only up to T_END seconds)
python mix.py OUT.wav T_END --dry   narration only
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

import music
from music import SR
from script_data import LINES
from timeline import build, load_durations
from tts import PROC, WORK

VOICE_RMS_DB = -18.0
BED_RMS_DB = -27.0     # beat + tonal before ducking (measured over active parts)


def rms_db(x):
    x = x[np.abs(x) > 1e-5]
    if len(x) == 0:
        return -120.0
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def narration_track(tl, n):
    import librosa
    v = np.zeros(n)
    for ln in LINES:
        if not ln["tts"] or ln["id"] not in tl["lines"]:
            continue
        p = os.path.join(PROC, f"{ln['id']}.wav")
        if not os.path.exists(p):
            continue
        y, sr = sf.read(p, dtype="float64")
        if sr != SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=SR)
        music.add(v, y, tl["lines"][ln["id"]][0])
    return v


def soft_limit(x, ceiling=0.89):
    # gentle tanh knee above 0.7*ceiling
    k = 0.7 * ceiling
    y = x.copy()
    m = np.abs(y) > k
    y[m] = np.sign(y[m]) * (k + (ceiling - k) * np.tanh((np.abs(y[m]) - k) / (ceiling - k)))
    return y


def make_mix(tl, t_end=None, dry=False):
    total = t_end or tl["total"]
    n = int(total * SR)
    voice = narration_track(tl, n)
    if dry:
        return voice[:n], voice[:n]
    beat, tonal, sfx = music.build_score(tl, total)
    beat, tonal, sfx = beat[:n], tonal[:n], sfx[:n]
    bed = beat * 1.0 + tonal * 0.9
    # normalise the bed to target level, then duck under the voice
    g = 10 ** ((BED_RMS_DB - rms_db(bed)) / 20)
    bed *= g
    sfx *= g * 1.6
    duck = music.duck_envelope(voice)
    mixd = voice + bed * duck + sfx * np.maximum(duck, 0.5)
    mixd = music.lowpass(mixd, 16000)
    mixd = soft_limit(mixd)
    return mixd, voice


def main():
    out = sys.argv[1]
    t_end = float(sys.argv[2]) if len(sys.argv) > 2 else None
    dry = "--dry" in sys.argv
    durs = load_durations(os.path.join(WORK, "tts/durations.json"))
    tl = build(durs)
    m, v = make_mix(tl, t_end, dry)
    st = np.stack([m, m], axis=1)
    sf.write(out, st.astype(np.float32), SR)
    print(f"wrote {out}: {len(m) / SR:.1f}s  voice {rms_db(v):.1f} dBFS(rms)  mix peak {20 * np.log10(np.max(np.abs(m)) + 1e-9):.1f} dBFS")
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(SR)
        print("integrated loudness %.1f LUFS" % meter.integrated_loudness(st))
    except Exception as e:  # pragma: no cover
        print("loudness n/a", e)


if __name__ == "__main__":
    main()
