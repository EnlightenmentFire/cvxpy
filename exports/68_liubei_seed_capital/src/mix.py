# -*- coding: utf-8 -*-
"""Arrange music layers by section, level under voice (-21 dB LUFS-relative, +4 dB in pauses), mix stems.
usage: python mix.py   (needs out/voice.wav, out/sfx.wav, music/<layer>/*.wav, out/timeline.json)
writes out/mix_music.wav, out/mix_nomusic.wav (pre-loudnorm) and out/mix_report.json
"""
import json, glob, os, sys
import numpy as np, soundfile as sf
import pyloudnorm as pyln
from scipy.signal import resample_poly
from scipy.ndimage import uniform_filter1d

SR = 48000
OUT = "/home/user/work/out"
MUS = "/home/user/work/music"
REL_DB = float(os.environ.get("MUSIC_REL", -21.0))
meter = pyln.Meter(SR)


def load(p):
    x, sr = sf.read(p, always_2d=True)
    x = x.mean(1).astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return x


def layer(name):
    fs = sorted(glob.glob(f"{MUS}/{name}/**/*.wav", recursive=True) + glob.glob(f"{MUS}/{name}/**/*.flac", recursive=True))
    return load(fs[0])


def main():
    tl = json.load(open(f"{OUT}/timeline.json"))
    voice = load(f"{OUT}/voice.wav")
    sfx = load(f"{OUT}/sfx.wav")
    n = max(len(voice), len(sfx))
    voice = np.pad(voice, (0, n - len(voice))); sfx = np.pad(sfx, (0, n - len(sfx)))
    sc = {s["id"]: s for s in tl["scenes"]}
    total = tl["total"]
    # section plan: (layer, start_scene, end_scene_exclusive or None)
    plan = [("rise", "s00", "s10"), ("base", "s10", "s20"), ("base2", "s20", "s30"), ("base", "s30", "s40"), ("push", "s40", "s50"), ("war", "s50", "s60"), ("coda", "s60", None)]
    music = np.zeros(n, np.float32)
    XF = 3.0
    seg_info = []
    for name, a, b in plan:
        try:
            x = layer(name)
        except IndexError:
            x = layer("base")
        t0 = sc[a]["start"] - (XF / 2 if a != "s00" else 0)
        t1 = (sc[b]["start"] + XF / 2) if b else total
        L = int((t1 - t0) * SR)
        if len(x) < L:   # loop with crossfade if short
            reps = [x]
            while sum(len(r) for r in reps) < L + SR * XF:
                reps.append(x)
            y = reps[0]
            for r in reps[1:]:
                f = int(XF * SR)
                ramp = np.linspace(0, 1, f)
                y = np.concatenate([y[:-f], y[-f:] * np.sqrt(1 - ramp) + r[:f] * np.sqrt(ramp), r[f:]])
            x = y
        x = x[:L].copy()
        # normalise each layer to same loudness first
        lv = meter.integrated_loudness(x) if len(x) > SR * 3 else -30
        x *= 10 ** ((-30 - lv) / 20)
        f = int(XF * SR)
        if a != "s00":
            x[:f] *= np.sqrt(np.linspace(0, 1, f))
        else:
            x[:int(0.5 * SR)] *= np.linspace(0, 1, int(0.5 * SR))
        if b:
            x[-f:] *= np.sqrt(np.linspace(1, 0, f))
        else:
            fo = int(4 * SR); x[-fo:] *= np.linspace(1, 0, fo) ** 1.5
        p = int(t0 * SR)
        e = min(n, p + len(x))
        music[p:e] += x[:e - p]
        seg_info.append(dict(layer=name, start=round(t0, 2), end=round(t1, 2)))
    # voice activity envelope
    vabs = uniform_filter1d(np.abs(voice), int(0.05 * SR))
    act = (vabs > 10 ** (-45 / 20)).astype(np.float32)
    act = uniform_filter1d(act, int(1.2 * SR)) > 0.02     # hold through short gaps
    g_db = np.where(act, 0.0, 4.0).astype(np.float32)
    g_db = uniform_filter1d(g_db, int(0.4 * SR))
    v_lufs = meter.integrated_loudness(voice[: int(total * SR)])
    m_lufs = meter.integrated_loudness(music)
    music *= 10 ** ((v_lufs + REL_DB - m_lufs) / 20)
    music *= 10 ** (g_db / 20)
    # first seconds: hook — music a bit lower under the sfx hook
    m_after = meter.integrated_loudness(music)
    mix_m = voice + sfx + music
    mix_n = voice + sfx
    sf.write(f"{OUT}/music_bed.wav", music, SR)
    sf.write(f"{OUT}/mix_music.wav", mix_m.astype(np.float32), SR, subtype="FLOAT")
    sf.write(f"{OUT}/mix_nomusic.wav", mix_n.astype(np.float32), SR, subtype="FLOAT")
    # per-section relative measurement under speech
    rel = []
    for s in seg_info:
        a, b = int(s["start"] * SR), int(min(s["end"], total) * SR)
        if b - a > 5 * SR:
            rel.append(dict(layer=s["layer"], voice_minus_music_db=round(meter.integrated_loudness(voice[a:b]) - meter.integrated_loudness(music[a:b]), 1)))
    rep = dict(voice_lufs=round(v_lufs, 2), music_lufs=round(m_after, 2), plan=seg_info, rel=rel)
    json.dump(rep, open(f"{OUT}/mix_report.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
