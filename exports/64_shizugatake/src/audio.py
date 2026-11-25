# -*- coding: utf-8 -*-
"""Build voice / sfx / music stems from timeline.json, mix with voice-keyed ducking.
Outputs (48 kHz): work/mix/voice.wav, sfx.wav, music.wav, mix_premaster.wav, nomusic_premaster.wav
Music: Kevin MacLeod (incompetech.com), CC BY 4.0."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as X

WK = "/tmp/claude-0/work"
SR = 48000
TL = json.load(open(f"{WK}/timeline.json"))
N = int((TL["total"] + 1) * SR)
SC = {s["id"]: s for s in TL["scenes"]}
MUS = f"{WK}/music"


def db(x):
    return 10 ** (x / 20)


def put(buf, x, t, g_db=0.0):
    k = int(t * SR)
    if k >= len(buf) or k + len(x) <= 0:
        return
    if k < 0:
        x = x[-k:]; k = 0
    L = min(len(x), len(buf) - k)
    buf[k:k + L] += x[:L] * db(g_db)


def T(sid, i=None, off=0.0):
    s = SC[sid]
    return s["start"] + (s["L"][i] if i is not None else 0.0) + off


def load_track(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{MUS}/{name}.mp3", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def voice_track():
    v = np.zeros(N, np.float32)
    for L in TL["lines"]:
        p = f"{WK}/tts/proc/{L['id']}.wav"
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p)
        put(v, x.astype(np.float32), L["start"])
    return v


def sfx_track():
    s = np.zeros(N, np.float32)
    # ---- hook: torches -> hooves -> conch -> taiko
    for k, t0 in enumerate((0.0, 0.22, 0.45, 0.8, 1.3)):
        put(s, X.whoosh(0.8), t0, 2 - k)
    put(s, X.crackle(15), 0.2, -10)
    put(s, X.hooves(14, 2.7, 8), 0.4, -6)
    put(s, X.horn(2.6), 0.6, 0)
    put(s, X.taiko(1.3), 2.4, 3)
    put(s, X.taiko(1.0), 3.0, -8)
    put(s, X.wind(12), T("h1"), -22)
    put(s, X.volley(5, 10, 1), T("h3", 1, -0.8), -14)
    put(s, X.crowd(5), T("h3", 1, -0.5), -20)
    put(s, X.hooves(8, 2.8, 6), T("h5"), -16)
    put(s, X.taiko(1.4), T("h6"), -4)
    put(s, X.brush_hit(), T("h6", None, 0.3), -8)
    # chapter hits
    for sid, sc in SC.items():
        if sc.get("chapter"):
            put(s, X.taiko(1.2), sc["start"] + 0.05, -6)
    # standoff wind
    put(s, X.wind(T("t1") - T("s1")), T("s1"), -20)
    put(s, X.rainsnd(10), T("t1", 2, -0.5), -20)
    put(s, X.volley(6, 16, 2), T("t2", 3, -1.2), -14)
    put(s, X.crowd(7, 3), T("t2", 3, -1.0), -19)
    put(s, X.horn(2.0, 200), T("t2", 2, 0.2), -14)
    # march
    md = T("r4") - T("r3")
    put(s, X.hooves(md, 3.0, 10), T("r3"), -13)
    put(s, X.crackle(md, 20), T("r3"), -18)
    put(s, X.brush_hit(), T("r5"), -8)
    # battle
    put(s, X.horn(2.8, 175), T("r6", 1, -0.6), -9)
    put(s, X.volley(14, 40, 4), T("r6", 3, -0.5), -12)
    put(s, X.crowd(18, 5), T("r6", 1, 0.5), -17)
    lv = T("r7", 0, 1.6)
    put(s, X.taiko(1.6), lv + 1.0, -3)
    put(s, X.boom(), T("r7", 5, 0.2), -6)
    put(s, X.crowd(8, 6), T("r7", 5, 0.3), -17)
    put(s, X.crackle(10, 40), T("e1", 0, 3.0), -14)
    put(s, X.brush_hit(), T("c2"), -8)
    put(s, X.taiko(1.3), T("c4", 1, 0.1), -4)
    return s


CUES = [  # (from scene, to scene, track, offset s, gain dB rel.)
    ("h0", "b1", "Five Armies", 12.0, 2.0),
    ("b1", "s1", "Ishikari Lore", 0.0, 0.0),
    ("s1", "t1", "Lightless Dawn", 0.0, 1.0),
    ("t1", "r2", "Interloper", 0.0, 0.0),
    ("r2", "r5", "Ancient Rite", 0.0, 0.0),
    ("r5", "r6", "Lightless Dawn", 120.0, -2.0),
    ("r6", "r8", "Five Armies", 70.0, 2.5),
    ("r8", "e1", "Lightless Dawn", 170.0, 0.0),
    ("e1", "c1", "Return of Lazarus", 58.0, -1.0),
    ("c1", None, "Despair and Triumph", 140.0, 0.0),
]
XF = 2.0


def music_track():
    m = np.zeros((N, 2), np.float32)
    cache = {}
    for a, b, name, off, g in CUES:
        if name not in cache:
            cache[name] = load_track(name)
        tr = cache[name]
        t0 = SC[a]["start"]
        t1 = SC[b]["start"] if b else TL["total"] + 0.5
        L = int((t1 - t0 + XF) * SR)
        seg = tr[int(off * SR): int(off * SR) + L]
        if len(seg) < L:  # loop
            reps = int(np.ceil(L / len(tr))) + 1
            seg = np.concatenate([tr[int(off * SR):]] + [tr] * reps)[:L]
        rms = np.sqrt((seg ** 2).mean()) + 1e-9
        seg = seg / rms * db(-24 + g)
        f = int(XF * SR)
        e = np.ones(len(seg), np.float32)
        e[:f] = np.linspace(0, 1, f) ** 0.5
        if b:
            e[-f:] = np.linspace(1, 0, f) ** 0.5
        else:
            k = int(3.5 * SR); e[-k:] = np.linspace(1, 0, k)
        k0 = int((t0 - (XF / 2 if a != "h0" else 0)) * SR)
        if a == "h0":
            k0 = int(2.4 * SR)  # music enters with the taiko
            seg = seg[:max(0, len(m) - k0)]
            e = e[:len(seg)]
        L2 = min(len(seg), len(m) - k0)
        m[k0:k0 + L2] += seg[:L2] * e[:L2, None]
    return m


def duck_curve(v):
    """gain (dB) for music: under speech -21 dB rel. voice speech level, pauses lifted."""
    hop = SR // 100
    nf = N // hop + 1
    act = np.zeros(nf, bool)
    for L in TL["lines"]:
        act[int(L["start"] * 100): int(L["end"] * 100) + 1] = True
    target = np.where(act, -23.0, -16.0)
    # louder sections
    for sid, extra in (("h0", 2.0), ("h6", 4.0), ("r3", 2.0), ("r6", 2.5), ("r7", 2.5)):
        a = int(SC[sid]["start"] * 100); b = int(SC[sid]["end"] * 100)
        target[a:b] += extra
    # Maeda stop-beat: music cut for ~1.0 s
    lv = T("r7", 0, 1.6)
    target[int((lv - 0.05) * 100): int((lv + 1.0) * 100)] = -80
    g = np.zeros(nf)
    cur = target[0]
    for i in range(nf):
        tg = target[i]
        if tg < -60 or cur < -60:
            cur = tg if tg < -60 else -30.0 if cur < -60 else cur
        k = 0.25 if tg < cur else 0.04   # fast duck, slow release (per 10 ms)
        cur += (tg - cur) * k
        g[i] = cur
    return np.repeat(g, hop)[:N]


def main():
    os.makedirs(f"{WK}/mix", exist_ok=True)
    v = voice_track()
    s = sfx_track()
    m = music_track()
    # voice speech level
    vr = 20 * np.log10(np.sqrt((v[np.abs(v) > 1e-3] ** 2).mean()) + 1e-9)
    mr = 20 * np.log10(np.sqrt((m ** 2).mean()) + 1e-9)
    g = duck_curve(v)
    m2 = m * db(vr - mr + g)[:, None] * db(0)  # music relative to voice level
    # sfx relative to voice: sfx were authored with gains around 0 dBFS peaks; scale to voice
    s2 = s * db(vr + 6)
    V = np.stack([v, v], 1)
    S2 = np.stack([s2, s2], 1)
    mix = V + m2 + S2
    nom = V + S2
    for name, x in (("voice", V), ("music", m2), ("sfx", S2), ("mix_premaster", mix), ("nomusic_premaster", nom)):
        sf.write(f"{WK}/mix/{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")
    print(f"voice speech RMS {vr:.1f} dBFS; music raw {mr:.1f}")


if __name__ == "__main__":
    main()
