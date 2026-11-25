# -*- coding: utf-8 -*-
"""Voice post-processing, SFX synthesis, narration/SFX stems.
usage: python audio.py post        -> tts/raw -> tts/proc
       python audio.py stems       -> out/voice.wav, out/sfx.wav (needs timeline)
"""
import sys, os, json, glob, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly, fftconvolve

SR = 48000
RAW = "/home/user/work/tts/raw"
PROC = "/home/user/work/tts/proc"
OUT = "/home/user/work/out"
os.makedirs(PROC, exist_ok=True)
MAX_PAUSE = 0.42
TEMPO = {"n": float(os.environ.get("TEMPO_N", 1.0)), "q": float(os.environ.get("TEMPO_Q", 0.94))}


def frame_db(x, win=0.02):
    n = int(SR * win)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    thr = max(db.max() - 40, -60)
    v = db > thr
    if not v.any():
        return x
    i0 = max(0, np.argmax(v) - 2)
    i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not v[k]:
            j = k
            while j < i1 and not v[j]:
                j += 1
            L = j - k
            keep = min(L, maxf)
            a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n])
            k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.012 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        a, b = d + "/a.wav", d + "/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def post_one(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from script import all_lines
    kind = {d["id"]: d["k"] for d in all_lines()}
    lid = os.path.basename(path)[:-4]
    x, sr = sf.read(path)
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    g = np.gcd(sr, SR)
    x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, TEMPO[kind.get(lid, "n")])
    x = sosfiltfilt(butter(4, 55, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 30
    rms = np.sqrt(np.mean(x[:len(db) * n].reshape(len(db), n)[v] ** 2))
    x *= 10 ** (-18 / 20) / max(rms, 1e-6)
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    sf.write(f"{PROC}/{lid}.wav", x, SR)


# ───────── SFX synthesis ─────────
rng = np.random.default_rng(7)


def env(n, a, d, sus=0.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    return e + sus


def lp(x, f, o=2):
    return sosfiltfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)


def bp(x, f0, f1, o=2):
    return sosfiltfilt(butter(o, [f0, f1], "bandpass", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfiltfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)


def reverb(x, rt=1.6, mix=0.25):
    n = int(rt * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6.9 / rt)
    ir = lp(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    w = fftconvolve(x, ir)[:len(x) + n]
    y = np.zeros(len(w)); y[:len(x)] = x
    return y * (1 - mix) + w * mix


def straw_rustle(dur=1.0):
    n = int(dur * SR)
    x = np.zeros(n)
    for k in range(40):
        p = rng.integers(0, n - 4000)
        L = rng.integers(800, 4000)
        b = rng.normal(0, 1, L) * env(L, 0.002, 0.02)
        x[p:p + L] += b * rng.uniform(0.2, 1)
    return bp(x, 1500, 7000) * 0.5


def neigh(dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-t * 0.9) + 380 + 60 * np.sin(2 * np.pi * 13 * t) * np.minimum(t * 3, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum((1 / k) * np.sin(k * ph) for k in range(1, 12))
    x = x * (1 + 0.5 * np.sin(2 * np.pi * 27 * t))
    x = bp(x, 400, 3500) + 0.3 * bp(rng.normal(0, 1, n), 800, 3000)
    e = np.minimum(t / 0.05, 1) * np.exp(-np.maximum(t - 0.7, 0) * 4)
    return reverb(x * e * 0.6, 1.2, 0.2)


def hoof(level=1.0):
    L = int(0.12 * SR)
    t = np.arange(L) / SR
    thump = np.sin(2 * np.pi * (90 + 40 * np.exp(-t * 40)) * t) * np.exp(-t * 35)
    click = hp(rng.normal(0, 1, L), 1500) * np.exp(-t * 120) * 0.35
    dirt = bp(rng.normal(0, 1, L), 300, 2000) * np.exp(-t * 30) * 0.4
    return (thump + click + dirt) * level


def gallop(dur, rate=2.3, horses=1, gain=0.6, fade_in=0.3, fade_out=0.8):
    n = int(dur * SR)
    x = np.zeros(n + SR)
    for h in range(horses):
        r = rate * rng.uniform(0.9, 1.1)
        off = rng.uniform(0, 1 / r)
        t = off
        lv = rng.uniform(0.4, 1.0) if horses > 1 else 1.0
        while t < dur:
            for k, dt in enumerate((0, 0.07, 0.15)):
                p = int((t + dt + rng.normal(0, 0.004)) * SR)
                if 0 <= p < n:
                    hb = hoof(lv * (1.0 if k else 0.8))
                    x[p:p + len(hb)] += hb
            t += 1 / r
    x = x[:n]
    e = np.minimum(np.arange(n) / SR / fade_in, 1) * np.minimum((n - np.arange(n)) / SR / fade_out, 1)
    x = lp(x, 4000) * e
    return reverb(x / max(np.abs(x).max(), 1e-6) * gain, 1.0, 0.18)


def taiko(gain=0.9, f=55):
    L = int(2.5 * SR)
    t = np.arange(L) / SR
    x = np.sin(2 * np.pi * (f + 40 * np.exp(-t * 18)) * t) * np.exp(-t * 3.2)
    x += 0.4 * lp(rng.normal(0, 1, L), 900) * np.exp(-t * 25)
    return reverb(x * gain, 2.2, 0.3)


def stamp(gain=0.8):
    L = int(0.6 * SR)
    t = np.arange(L) / SR
    x = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 50)) * t) * np.exp(-t * 14)
    x += 0.5 * bp(rng.normal(0, 1, L), 200, 3000) * np.exp(-t * 60)
    return reverb(x * gain, 0.6, 0.12)


def whoosh(dur=1.0, gain=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    for i in range(0, n, 2400):
        fc = 300 + 2500 * np.sin(np.pi * i / n)
        seg = x[i:i + 2400]
        out[i:i + len(seg)] = seg
    out = bp(out, 300, 2600) * np.sin(np.pi * t / dur) ** 2
    return out * gain


def clink(gain=0.15):
    L = int(0.4 * SR)
    t = np.arange(L) / SR
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((3200, 18), (4700, 25), (6100, 30)))
    return x * gain / 3


def add(buf, x, t, g=1.0):
    p = int(t * SR)
    if p < 0:
        x = x[-p:]; p = 0
    e = min(len(buf), p + len(x))
    if e > p:
        buf[p:e] += x[:e - p] * g


def stems():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    R = render.Renderer()
    total = R.total
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    lines_meta = []
    for s in R.scs:
        for i, ln in enumerate(s["sc"]["lines"]):
            lid = f"{s['sc']['id']}_{i:02d}"
            x, _ = sf.read(f"{PROC}/{lid}.wav")
            a = s["L"][i][0]
            add(voice, x, a)
            lines_meta.append(dict(id=lid, start=a, end=a + len(x) / SR, say=ln["say"]))
    sfx = np.zeros(n)
    # hook: straw rustle -> neigh -> hoofbeats
    add(sfx, straw_rustle(1.0), 0.0, 0.8)
    add(sfx, neigh(), 0.55, 0.9)
    add(sfx, gallop(6.0, horses=6, gain=0.55, fade_in=0.2, fade_out=2.0), 0.8, 1.0)
    sc = {s["sc"]["id"]: s for s in R.scs}
    # tree: 滅吾門 drum
    s = sc["s01"]; add(sfx, taiko(0.7, 50), s["L"][4][0] - 0.1)
    # teaser horses
    s = sc["s04"]; add(sfx, gallop(s["end"] - s["start"], horses=8, gain=0.4), s["start"])
    # section stings
    for s in R.scs:
        if s["sc"].get("title"):
            add(sfx, taiko(0.9, 52), s["start"] + 0.1)
            add(sfx, whoosh(1.2, 0.18), s["start"] - 0.4)
    # seals
    for i, tt in R.hud.items():
        pass
    for s in R.scs:
        for i, ln in enumerate(s["sc"]["lines"]):
            if ln.get("seal"):
                st = s["L"][i][1] + 0.45 if ln["k"] == "q" else s["L"][i][1] - 1.6
                add(sfx, stamp(0.9), st + 0.4)
    # 兌不出 stamp
    s = sc["s10"]; add(sfx, stamp(0.7), s["L"][4][0] + 0.25)
    # horses scene: big herd
    s = sc["s41"]
    add(sfx, neigh(), s["start"] + 0.3, 0.8)
    add(sfx, gallop(s["L"][2][1] - s["start"] + 2, horses=14, gain=0.6, fade_in=0.8, fade_out=3.0), s["start"])
    for k in range(10):
        add(sfx, clink(0.12), s["L"][2][0] + k * 0.45 + rng.uniform(0, 0.2))
    # map arrows whoosh
    for sid, li in (("s31", 4), ("s50", 3), ("s50", 2)):
        s = sc[sid]; add(sfx, whoosh(1.6, 0.2), s["L"][li][0])
    # 杖二百
    s = sc["s53"]; add(sfx, taiko(0.6, 60), s["L"][2][0] + 2.0)
    # finale drum
    s = sc["s61"]; add(sfx, taiko(0.8, 48), s["start"] + 0.2)
    sf.write(f"{OUT}/voice.wav", voice, SR)
    sf.write(f"{OUT}/sfx.wav", (sfx * 0.5).astype(np.float32), SR)
    json.dump(dict(total=total, lines=lines_meta), open(f"{OUT}/voice_lines.json", "w"), ensure_ascii=False, indent=1)
    print("stems", total)


if __name__ == "__main__":
    if sys.argv[1] == "post":
        fs = sorted(glob.glob(f"{RAW}/*.wav"))
        for p in fs:
            post_one(p)
        print("post", len(fs))
    elif sys.argv[1] == "stems":
        stems()
