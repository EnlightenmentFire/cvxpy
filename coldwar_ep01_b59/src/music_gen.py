"""Select and stitch MusicGen clips into per-layer beds (配乐规范, priority 1: local AI generation).

For each layer: measure every generated 30 s clip on objective "stays under the voice" metrics
(1-4 kHz presence share, loudness steadiness, sudden rises, dropouts, percussion where none was asked
for, anything a speech detector mistakes for a voice), reject broken clips, then chain as many as the
edit needs with 3.5 s equal-power crossfades. Clips are ordered so neighbours are harmonically close
(chroma cosine similarity), and the first clip of a layer is chosen to sit well against the last clip
of the layer before it (they cross-fade in the film). In the drum layer the incoming clip is shifted
so its low-drum hits land on the outgoing clip's hits inside the crossfade (no flams at the joins).

Writes 48 kHz stereo layer files <OUT>/gen_<layer>.wav and <OUT>/selection.json.
Run in the qwen312 venv:  python music_gen.py
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
CLIPS = os.path.join(SCR, "musicgen/clips")
OUT = os.path.join(SCR, "musicgen/layers")
SR = 48000
XF = 3.5                      # crossfade seconds between clips inside a layer
DEFAULT_TRIM = (0.6, 0.6)     # trim clip edges (MusicGen onsets / cut-off tails)
TRIM = {"climax": (0.0, 0.15)}  # the climax is used whole: its end is aligned to the flash
PULSE_LAYERS = set()         # layers whose joins are beat-aligned (none in use: see "build" below)
MAX_LAG = 2.0                 # seconds the incoming clip may be shifted to line up the drum hits
# timeline order. 推进 is the "tension" layer (tremolo strings, dive -> launch) under the synthesized lub-dub
# heartbeat (music.py). Two drum prompts were tried and dropped: "build" gave drones with no audible drum,
# "drum" gave one steady 120-bpm clip, one syncopated groove and scattered booms that read as depth charges.
ORDER = ["bed", "tension", "climax", "post", "ending"]
SOURCES = {}                  # layer -> clip-name prefixes to draw from (default: the layer's own name)
LINKED = {"tension": "bed", "ending": "post"}  # layers that cross-fade into each other in the film
NO_PERC = {"bed", "tension", "post", "ending"}


def need_seconds():
    """seconds each stitched layer must cover on the final timeline (from music.plan_gen), +2 s margin."""
    os.environ.setdefault("SCORE_SOURCE", "gen")
    import music
    tl = json.load(open(os.path.join(SCR, "edit/timeline.json")))
    T = {s["id"]: s["start"] for s in tl["shots"]}
    need = {}
    for seg in music.plan_gen(T):
        if seg["name"].startswith("gen_"):
            a = seg["t0"] - seg["fin"] / 2 if seg["t0"] > 0 else 0.0
            b = min(tl["duration"], seg["t1"] + seg["fout"] / 2)
            need[seg["name"][4:]] = round(b - a + 2.0, 2)
    return need


def load(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    return x


def onset_env(x):
    """low-band (< 150 Hz) onset strength at 1 kHz: where the low drum hits."""
    m = x.mean(1) if x.ndim == 2 else x
    lb = signal.sosfilt(signal.butter(4, 150 / (SR / 2), "low", output="sos"), m)
    n = len(lb) // 48 * 48
    e = np.abs(lb[:n]).reshape(-1, 48).max(1)
    e = np.convolve(e, np.ones(8) / 8, "same")
    return np.maximum(0.0, np.diff(e, prepend=e[0]))


def chroma_vec(x):
    import librosa
    m = librosa.resample(x.mean(1), orig_sr=SR, target_sr=22050)
    c = librosa.feature.chroma_cqt(y=m, sr=22050, hop_length=1024, fmin=librosa.note_to_hz("C1"), n_octaves=6)
    v = c.mean(1)
    return v / (np.linalg.norm(v) + 1e-12)


def perc_ratio(x):
    import librosa
    m = librosa.resample(x.mean(1), orig_sr=SR, target_sr=22050)
    S = np.abs(librosa.stft(m, n_fft=2048, hop_length=512))
    H, P = librosa.decompose.hpss(S)
    return float((P ** 2).sum() / ((H ** 2).sum() + (P ** 2).sum() + 1e-12))


def speech_frac(x):
    """fraction of the clip a speech detector (Silero VAD) calls voice: MusicGen sometimes hums/choirs."""
    import librosa
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    m = librosa.resample(x.mean(1), orig_sr=SR, target_sr=16000)
    m = m / (np.abs(m).max() + 1e-9) * 0.5
    ts = get_speech_timestamps(m, VadOptions(threshold=0.5, min_speech_duration_ms=250))
    return float(sum(s["end"] - s["start"] for s in ts) / len(m))


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
    # chroma (12 pitch classes, C=0) from a constant-Q transform: low drones need log-frequency resolution
    chroma = chroma_vec(x)
    # onset regularity (pulse) in the low band
    env = onset_env(x)
    env = env - env.mean()
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    ac /= ac[0] + 1e-12
    lag = np.arange(len(ac)) / 1000.0
    win = (lag > 0.4) & (lag < 2.0)
    pulse = float(ac[win].max()) if win.any() else 0.0
    pulse_period = float(lag[win][np.argmax(ac[win])]) if win.any() else 0.0
    slope = float(np.polyfit(np.arange(len(db)) * 0.1, db, 1)[0])
    # booms: low-band hits that stick out > 12 dB above the local (2 s) median - drums or thuds
    lb = signal.sosfilt(signal.butter(4, 150 / (SR / 2), "low", output="sos"), m)
    ldb = 10 * np.log10(np.mean(lb[: len(lb) // 480 * 480].reshape(-1, 480) ** 2, 1) + 1e-12)
    pk, _ = signal.find_peaks(ldb, prominence=20, distance=15)
    stick = np.array([ldb[p] - np.median(ldb[max(0, p - 100): p + 100]) for p in pk])
    booms = int((stick > 12).sum()) if len(pk) else 0
    return {"rms_db": float(10 * np.log10(np.mean(m ** 2) + 1e-12)), "presence_1_4k": float(pres),
            "low_share": float(low), "loud_std_db": float(np.std(sec)), "max_rise_db_per_s": rise,
            "silent_frac": float(1 - act.mean()), "pulse": pulse, "pulse_period_s": pulse_period,
            "slope_db_per_s": slope, "end_minus_start_db": float(np.mean(db[-60:]) - np.mean(db[:60])),
            "perc": perc_ratio(x), "booms": booms, "speech": speech_frac(x), "chroma": chroma.tolist()}


def score(layer, m):
    s = -40 * m["presence_1_4k"] - 0.25 * m["loud_std_db"] - 0.15 * max(0, m["max_rise_db_per_s"] - 4)
    s -= 8 * m["silent_frac"] + 10 * m["speech"]
    if layer in NO_PERC:
        s -= 8 * max(0.0, m["perc"] - 0.10) + 0.25 * m["booms"]
    if layer in PULSE_LAYERS:
        s += 2.0 * m["pulse"]
        if m["pulse_period_s"] < 0.7:       # wants a sparse beat, not a busy one
            s -= 1.0
    if layer == "climax":
        s += 1.2 * m["slope_db_per_s"] + 0.05 * m["max_rise_db_per_s"] + 0.1 * m["end_minus_start_db"]
        s += 20 * m["presence_1_4k"]        # full orchestra may have presence (the voice pauses there)
    return float(s)


def broken(m):
    return m["silent_frac"] > 0.12 or m["rms_db"] < -50 or m["speech"] > 0.15


def chroma_sim(a, b):
    return float(np.dot(np.array(a), np.array(b)))


HEAD_MAX = 5.0     # longest quiet lead-in that is skipped
BODY_DB = -20.0    # every clip's body is set to this median 1 s level before stitching (no gain drift)


def short_db(x, win=1.0):
    m = x.mean(1)
    hop = int(0.1 * SR)
    n = len(m) // hop
    db = 10 * np.log10(np.mean(m[: n * hop].reshape(n, hop) ** 2, 1) + 1e-12)
    k = int(win / 0.1)
    return 10 * np.log10(np.convolve(10 ** (db / 10), np.ones(k) / k, "valid") + 1e-12)


def prep(layer, x):
    """trim the edges; skip a quiet swell-in and flatten the clip's overall crescendo (MusicGen clips tend to
    start low and grow, which would give a saw-tooth level at every join - an underscore should stay level);
    set the body to BODY_DB. The climax keeps its shape: its build is the point.
    Returns (clip, skipped head seconds, removed trend dB over the clip)."""
    t0, t1 = TRIM.get(layer, DEFAULT_TRIM)
    x = x[int(t0 * SR): len(x) - int(t1 * SR)]
    head, trend = 0.0, 0.0
    if layer != "climax":
        sec = short_db(x)
        head = min(HEAD_MAX, float(np.argmax(sec >= np.median(sec) - 6.0)) * 0.1)
        x = x[int(head * SR):]
        sec = short_db(x)
        tt = np.arange(len(sec)) * 0.1 + 0.5
        slope = float(np.polyfit(tt, sec, 1)[0])
        dur = len(x) / SR
        ramp = np.clip(-slope * (np.arange(len(x)) / SR - dur / 2), -6.0, 6.0)
        x = x * (10 ** (ramp / 20))[:, None]
        trend = slope * dur
    x = x * 10 ** ((BODY_DB - float(np.median(short_db(x)))) / 20)
    return x.astype(np.float32), head, trend


def chain(layer, ids, mets, lens, need, prev_last=None):
    """pick and order clips: start from the best (or, for a layer that cross-fades out of another one,
    the best-scoring clip that also sits well against that layer's last clip), then the harmonically
    closest clips, until the stitched length covers `need`."""
    usable = [i for i in ids if not broken(mets[i])]
    usable.sort(key=lambda i: -mets[i]["score"])
    if layer == "climax":
        return usable[:1]
    if prev_last is not None:
        first = max(usable[:3], key=lambda i: mets[i]["score"] + 3.0 * chroma_sim(prev_last, mets[i]["chroma"]))
    else:
        first = usable[0]
    order = [first]
    total = lens[first]
    rest = [i for i in usable if i != first]
    while total < need and rest:
        last = mets[order[-1]]["chroma"]
        nxt = max(rest, key=lambda i: chroma_sim(last, mets[i]["chroma"]) + 0.05 * mets[i]["score"])
        order.append(nxt)
        rest.remove(nxt)
        total += lens[nxt] - XF - (MAX_LAG / 2 if layer in PULSE_LAYERS else 0.0)
    return order


def stitch(clips, layer):
    out, joins = None, []
    n = int(XF * SR)
    a = np.cos(0.5 * np.pi * np.linspace(0, 1, n))[:, None]
    b = np.sin(0.5 * np.pi * np.linspace(0, 1, n))[:, None]
    for x in clips:
        if out is None:
            out = x.copy()
            continue
        shift, corr = 0, None
        if layer in PULSE_LAYERS:   # line the incoming low-drum hits up with the outgoing ones
            ea = onset_env(out[-n:])
            eb = onset_env(x[: n + int(MAX_LAG * SR)])
            best = -2.0
            for lag in range(0, int(MAX_LAG * 1000)):
                seg = eb[lag: lag + len(ea)]
                if len(seg) < len(ea):
                    break
                c = float(np.dot(ea - ea.mean(), seg - seg.mean()) /
                          (np.linalg.norm(ea - ea.mean()) * np.linalg.norm(seg - seg.mean()) + 1e-12))
                if c > best:
                    best, shift = c, lag
            corr = round(best, 3)
            x = x[int(shift * SR / 1000):]
        lv = lambda v: 10 * math.log10(float(np.mean(v ** 2)) + 1e-12)
        joins.append({"at_s": round((len(out) - n) / SR, 2), "shift_ms": shift, "drum_corr": corr,
                      "tail_db": round(lv(out[-n:]), 1), "head_db": round(lv(x[:n]), 1)})
        out = np.concatenate([out[:-n], out[-n:] * a + x[:n] * b, x[n:]])
    return out.astype(np.float32), joins


def main():
    os.makedirs(OUT, exist_ok=True)
    need_all = need_seconds()
    report, last_chroma = {"need_s": need_all, "body_db": BODY_DB}, {}
    for layer in ORDER:
        need = need_all.get(layer)
        ids = sorted(f[:-4] for f in os.listdir(CLIPS) if f.endswith(".wav")
                     and f.rsplit("_", 1)[0] in SOURCES.get(layer, (layer,)))
        if not ids:
            print("no clips for", layer)
            continue
        xs, heads, trends = {}, {}, {}
        for i in ids:
            xs[i], heads[i], trends[i] = prep(layer, load(os.path.join(CLIPS, f"{i}.wav")))
        lens = {i: len(xs[i]) / SR for i in ids}
        mets = {i: metrics(xs[i]) for i in ids}
        for i in ids:
            mets[i]["score"] = score(layer, mets[i])
            mets[i]["head_skipped_s"] = heads[i]
            mets[i]["trend_removed_db"] = round(trends[i], 1)
        prev = last_chroma.get(LINKED.get(layer))
        order = chain(layer, ids, mets, lens, need, prev)
        if layer == "ending":   # the last clip is the one heard alone before the black: put the best one there
            order = order[::-1]
        y, joins = stitch([xs[i] for i in order], layer)
        spare = [i for i in sorted(ids, key=lambda i: -mets[i]["score"]) if i not in order and not broken(mets[i])]
        while len(y) / SR < need and spare and layer != "climax":   # alignment shifts ate the margin
            order.append(spare.pop(0))
            y, joins = stitch([xs[i] for i in order], layer)
        last_chroma[layer] = mets[order[-1]]["chroma"]
        peak = float(np.abs(y).max())
        if peak > 0.89:
            y = y * (0.89 / peak)
        sf.write(os.path.join(OUT, f"gen_{layer}.wav"), y, SR, subtype="FLOAT")
        sims = [round(chroma_sim(mets[p]["chroma"], mets[q]["chroma"]), 3) for p, q in zip(order, order[1:])]
        report[layer] = {"order": order, "seconds": round(len(y) / SR, 1), "need_s": need, "joins": joins,
                         "join_chroma_sim": sims,
                         "link_chroma_sim": (round(chroma_sim(prev, mets[order[0]]["chroma"]), 3) if prev else None),
                         "clips": {i: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in mets[i].items()
                                       if k != "chroma"} for i in ids}}
        ok = "OK" if len(y) / SR >= need or layer == "climax" else "SHORT"
        print(f"{layer} -> {order}  {len(y) / SR:.1f}s (need {need:.1f}s) {ok}  sims {sims}"
              f"  link {report[layer]['link_chroma_sim']}", flush=True)
        print("   joins", [(j["at_s"], j["tail_db"], j["head_db"]) for j in joins])
        for i in ids:
            mm = mets[i]
            print(f"   {i}: score {mm['score']:.2f} head {heads[i]:.1f}s trend {trends[i]:+.1f}dB pres {mm['presence_1_4k']:.3f} "
                  f"std {mm['loud_std_db']:.1f} rise {mm['max_rise_db_per_s']:.1f} silent {mm['silent_frac']:.2f} "
                  f"perc {mm['perc']:.2f} booms {mm['booms']} speech {mm['speech']:.2f} pulse {mm['pulse']:.2f}@{mm['pulse_period_s']:.2f}s "
                  f"slope {mm['slope_db_per_s']:.2f}{'  BROKEN' if broken(mm) else ''}")
    json.dump(report, open(os.path.join(OUT, "selection.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
