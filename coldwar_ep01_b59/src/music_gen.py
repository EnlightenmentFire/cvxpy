"""Select and stitch MusicGen clips into per-layer beds (配乐规范, priority 1: local AI generation).

For each layer: score every generated 30 s clip on objective "doesn't fight the voice" metrics, reject
broken clips, then chain the needed number of clips with 3.5 s equal-power crossfades, ordering them
so neighbours are harmonically close (chroma cosine similarity) to keep the joins inaudible.
Writes 48 kHz stereo layer files: <OUT>/gen_<layer>.wav + a selection report.
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
CLIPS = os.path.join(SCR, "musicgen/clips")
OUT = os.path.join(SCR, "musicgen/layers")
SR = 48000
XF = 3.5      # crossfade seconds between clips
TRIM = 0.6    # trim clip edges (MusicGen onsets/tails)

# seconds each stitched layer must cover (from the edit: see music.plan); generous margins
NEED = {"bed": 104.0, "build": 140.0, "climax": 31.0, "post": 172.0, "ending": 50.0}


def load(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    return x


def metrics(x):
    m = x.mean(1)
    hop = int(0.1 * SR)
    n = len(m) // hop
    fr = m[: n * hop].reshape(n, hop)
    db = 10 * np.log10(np.mean(fr ** 2, 1) + 1e-12)
    act = db > db.max() - 45
    sec = 10 * np.log10(np.convolve(10 ** (db / 10), np.ones(10) / 10, "valid") + 1e-12)
    rise = float(np.max(sec[10:] - sec[:-10])) if len(sec) > 10 else 0.0
    f, t, S = signal.stft(m, SR, nperseg=4096, noverlap=2048)
    P = np.abs(S) ** 2
    tot = P.sum() + 1e-12
    pres = P[(f >= 1000) & (f < 4000)].sum() / tot
    low = P[(f >= 20) & (f < 250)].sum() / tot
    # chroma (12 pitch classes) from the magnitude spectrum, 55 Hz - 2 kHz
    sel = (f >= 55) & (f < 2000)
    pc = np.round(12 * np.log2(f[sel] / 440.0)).astype(int) % 12
    chroma = np.zeros(12)
    np.add.at(chroma, pc, P[sel].sum(1))
    chroma /= np.linalg.norm(chroma) + 1e-12
    # onset regularity (pulse) in the low band, for the build layer
    lowband = signal.sosfilt(signal.butter(4, 150 / (SR / 2), "low", output="sos"), m)
    env = np.abs(signal.hilbert(lowband[::48]))  # 1 kHz envelope
    env = env - np.convolve(env, np.ones(500) / 500, "same")
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    ac /= ac[0] + 1e-12
    lag = np.arange(len(ac)) / 1000.0
    win = (lag > 0.4) & (lag < 2.0)
    pulse = float(ac[win].max()) if win.any() else 0.0
    pulse_period = float(lag[win][np.argmax(ac[win])]) if win.any() else 0.0
    slope = float(np.polyfit(np.arange(len(db)) * 0.1, db, 1)[0])
    return {"rms_db": float(10 * np.log10(np.mean(m ** 2) + 1e-12)), "presence_1_4k": float(pres), "low_share": float(low),
            "loud_std_db": float(np.std(sec)), "max_rise_db_per_s": rise, "silent_frac": float(1 - act.mean()),
            "pulse": pulse, "pulse_period_s": pulse_period, "slope_db_per_s": slope, "chroma": chroma.tolist()}


def score(layer, m):
    s = -40 * m["presence_1_4k"] - 0.25 * m["loud_std_db"] - 0.15 * max(0, m["max_rise_db_per_s"] - 4)
    s -= 8 * m["silent_frac"]
    if layer == "build":
        s += 2.0 * m["pulse"]
    if layer == "climax":
        s += 1.2 * m["slope_db_per_s"] + 0.05 * m["max_rise_db_per_s"]  # wants a build, can be bigger
        s += 20 * m["presence_1_4k"]  # full orchestra is allowed some presence (voice pauses there)
    return float(s)


def broken(m):
    return m["silent_frac"] > 0.12 or m["rms_db"] < -50


def chain(layer, ids, mets, need):
    """pick and order clips: best first, then harmonically closest that fits."""
    usable = [i for i in ids if not broken(mets[i])]
    usable.sort(key=lambda i: -mets[i]["score"])
    per = 30.0 - 2 * TRIM - XF
    k = max(1, math.ceil((need - XF) / per))
    if layer == "climax":
        return usable[:1]
    pool = usable[: max(k, min(len(usable), k + 1))]
    order = [pool[0]]
    rest = pool[1:]
    while len(order) < k and rest:
        last = np.array(mets[order[-1]]["chroma"])
        nxt = max(rest, key=lambda i: float(np.dot(last, np.array(mets[i]["chroma"]))) + 0.02 * mets[i]["score"])
        order.append(nxt)
        rest.remove(nxt)
    return order


def stitch(clips):
    out = None
    for x in clips:
        x = x[int(TRIM * SR): len(x) - int(TRIM * SR)]
        if out is None:
            out = x.copy()
            continue
        n = int(XF * SR)
        a = np.cos(0.5 * np.pi * np.linspace(0, 1, n))[:, None]
        b = np.sin(0.5 * np.pi * np.linspace(0, 1, n))[:, None]
        # level-match the incoming clip to the outgoing tail over the overlap
        g = math.sqrt((np.mean(out[-n:] ** 2) + 1e-12) / (np.mean(x[:n] ** 2) + 1e-12))
        g = min(2.0, max(0.5, g))
        x = x * g
        out = np.concatenate([out[:-n], out[-n:] * a + x[:n] * b, x[n:]])
    return out.astype(np.float32)


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for layer, need in NEED.items():
        files = sorted(f for f in os.listdir(CLIPS) if f.startswith(layer + "_") and f.endswith(".wav"))
        if not files:
            print("no clips for", layer)
            continue
        ids = [int(f.split("_")[1][:-4]) for f in files]
        xs = {i: load(os.path.join(CLIPS, f"{layer}_{i}.wav")) for i in ids}
        mets = {i: metrics(xs[i]) for i in ids}
        for i in ids:
            mets[i]["score"] = score(layer, mets[i])
        order = chain(layer, ids, mets, need)
        y = stitch([xs[i] for i in order])
        sf.write(os.path.join(OUT, f"gen_{layer}.wav"), y, SR)
        report[layer] = {"order": order, "seconds": round(len(y) / SR, 1),
                         "clips": {i: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in mets[i].items()
                                       if k != "chroma"} for i in ids}}
        print(layer, "->", order, f"{len(y) / SR:.1f}s", flush=True)
        for i in ids:
            mm = mets[i]
            print(f"   clip {i}: score {mm['score']:.2f} pres {mm['presence_1_4k']:.3f} std {mm['loud_std_db']:.1f} "
                  f"rise {mm['max_rise_db_per_s']:.1f} silent {mm['silent_frac']:.2f} pulse {mm['pulse']:.2f}"
                  f"@{mm['pulse_period_s']:.2f}s slope {mm['slope_db_per_s']:.2f}{'  BROKEN' if broken(mm) else ''}")
    json.dump(report, open(os.path.join(OUT, "selection.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
