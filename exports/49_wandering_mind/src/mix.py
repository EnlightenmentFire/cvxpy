# -*- coding: utf-8 -*-
"""Assemble narration from timeline, duck music under it, add SFX, normalise.
Outputs (WORK): narration.wav, mix_music.wav (full), mix_nomusic.wav (voice + sfx), mix_report.json
Targets: music 20-24 dB under the voice while speaking; final -15 LUFS integrated, true peak <= -1.5 dBTP.
"""
import os, json, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import uniform_filter1d
from scipy.signal import resample_poly

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
MUSIC_UNDER_DB = float(os.environ.get("MUSIC_UNDER", 21.0))   # voice-active music level below voice
GAP_LIFT_DB = 6.0                                              # music lift in longer pauses
TARGET_LUFS = -15.0


def limit(x, ceil_db=-2.0, look=0.004, rel=0.08):
    """Look-ahead peak limiter on the 4x-oversampled envelope (true-peak aware)."""
    from scipy.signal import resample_poly
    from scipy.ndimage import minimum_filter1d
    lim = 10 ** (ceil_db / 20)
    os4 = np.abs(resample_poly(x, 4, 1, axis=0)).max(1)
    env = os4.reshape(-1, 4).max(1)[: len(x)]
    g = np.minimum(1.0, lim / (env + 1e-9))
    n = int(look * SR)
    g = minimum_filter1d(g, 2 * n + 1)            # look-ahead window centred on the peak
    a = np.exp(-1 / (rel * SR))
    from scipy.signal import lfilter
    # release smoothing: one-pole on the gain, then take min with the instantaneous need
    gs = lfilter([1 - a], [1, -a], g - 1) + 1
    g = np.minimum(g, gs)
    g = uniform_filter1d(g, n)                    # smooth the attack edge
    g = np.minimum(g, minimum_filter1d(np.minimum(1.0, lim / (env + 1e-9)), 3))
    return x * g[:, None]


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    n = int((tl["total"] + 0.0) * SR)
    voice = np.zeros(n, np.float32)
    active = np.zeros(n, bool)
    for d in tl["lines"]:
        x, sr = sf.read(f"{WORK}/tts/proc/{d['id']}.wav")
        i = int(round(d["t0"] * SR))
        x = x[: n - i]
        voice[i:i + len(x)] += x
        active[i:i + len(x)] = True
    sf.write(f"{WORK}/narration.wav", voice, SR, subtype="PCM_24")

    mus, _ = sf.read(f"{WORK}/music.wav")
    sfx, _ = sf.read(f"{WORK}/sfx.wav")
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n].astype(np.float32)
    sfx = np.pad(sfx, ((0, max(0, n - len(sfx))), (0, 0)))[:n].astype(np.float32)

    # ducking gain: 0 dB in speech regions (widened 0.25 s), +GAP_LIFT in pauses > 1 s
    act = active.copy()
    w = int(0.25 * SR)
    act = uniform_filter1d(act.astype(np.float32), 2 * w + 1) > 0
    lift = np.where(act, 0.0, GAP_LIFT_DB).astype(np.float32)
    # only lift for long gaps: erode lifted regions by 0.5 s on each side
    e = int(0.5 * SR)
    long_gap = uniform_filter1d((~act).astype(np.float32), 2 * e + 1) > 0.999
    lift = np.where(long_gap, GAP_LIFT_DB, 0.0).astype(np.float32)
    lift = uniform_filter1d(lift, int(0.6 * SR))  # smooth ramps
    g = 10 ** (lift / 20)

    v_act = voice[active]
    m_act = mus[active].mean(1)
    base = rms_db(v_act) - MUSIC_UNDER_DB - rms_db(m_act)
    mus_out = mus * (10 ** (base / 20)) * g[:, None]
    # open: music fades in over 2 s under the bell
    fi = np.clip(np.arange(n) / (2.0 * SR), 0, 1)
    mus_out *= fi[:, None]
    sfx_out = sfx * (10 ** ((rms_db(v_act) - 8 - rms_db(sfx[: int(3 * SR)].mean(1))) / 20))
    # final 3 s fade
    fo = np.clip((n / SR - np.arange(n) / SR) / 3.0, 0, 1)
    vst = np.stack([voice, voice], 1)
    full = (vst + mus_out + sfx_out) * fo[:, None]
    nomus = (vst + sfx_out) * fo[:, None]

    meter = pyln.Meter(SR)
    rep = {}
    for name, x in (("mix_music", full), ("mix_nomusic", nomus)):
        for _ in range(4):  # normalise -> limit -> renormalise until both targets hold
            L = meter.integrated_loudness(x)
            x = x * 10 ** ((TARGET_LUFS - L) / 20)
            x = limit(x, -2.0)
        sf.write(f"{WORK}/{name}.wav", x.astype(np.float32), SR, subtype="PCM_24")
        rep[name] = dict(lufs=round(meter.integrated_loudness(x), 2),
                         true_peak_dbtp=round(20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max()), 2))
    # music-under-voice measurement on the final mix (speech regions)
    k = 10 ** ((TARGET_LUFS - meter.integrated_loudness(full)) / 20)
    rep["music_below_voice_db_speech"] = round(rms_db(v_act) - rms_db(mus_out[active].mean(1)), 1)
    rep["music_below_voice_db_gaps"] = round(rms_db(v_act) - rms_db(mus_out[~act].mean(1)), 1)
    json.dump(rep, open(f"{WORK}/mix_report.json", "w"), indent=1, default=float)
    print(json.dumps(rep, default=float))


if __name__ == "__main__":
    main()
