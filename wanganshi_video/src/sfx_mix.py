# -*- coding: utf-8 -*-
"""Sound design + final mix.
SFX (all synthesized here): copper-coin cascade (opening hook), 惊堂木 gavel crack (headline slam / title),
low bell for the closing question mark.
Mix: narration placed per timeline; music ducked under voice (~21-23 dB below speech, lifted in pauses);
two-pass loudnorm to -15 LUFS / -1.5 dBTP. Also writes a no-music version.
usage: python sfx_mix.py <timeline.json> <music.wav> <outdir>
"""
import sys, os, json, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WORK}/tts/proc"


def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def room(x, t60=0.5, wet=0.25, seed=0):
    rng = np.random.default_rng(seed)
    n = int(SR * t60)
    ir = rng.normal(0, 1, n) * np.exp(-6.9 * np.arange(n) / n)
    ir = bp(ir, 200, 6000)
    ir /= np.abs(ir).sum() ** 0.5 * 8
    y = fftconvolve(x, ir)[:len(x) + n]
    out = np.zeros(len(y)); out[:len(x)] += x
    return out + wet * y / (np.abs(y).max() + 1e-9) * np.abs(x).max()


def coin_clink(rng, dur=0.5, base=1.0):
    t = np.arange(int(SR * dur)) / SR
    parts = [(2930, 0.18), (4410, 0.11), (6120, 0.08), (7890, 0.06), (9370, 0.04)]
    y = np.zeros_like(t)
    for f, d in parts:
        f = f * base * rng.uniform(0.97, 1.03)
        y += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / (d * rng.uniform(0.8, 1.2))) * rng.uniform(0.6, 1.0)
    click = rng.normal(0, 1, len(t)) * np.exp(-t / 0.002)
    y = y + 0.6 * bp(click, 3000, 12000)
    return y / np.abs(y).max()


def coin_cascade(seed=1):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(SR * 2.0)); pos = 0.0
    gaps = [0.0, 0.16, 0.12, 0.10, 0.09, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04, 0.05, 0.07, 0.10]
    for i, g in enumerate(gaps):
        pos += g
        c = coin_clink(rng, 0.45, rng.uniform(0.85, 1.15)) * (0.9 - 0.03 * i) * rng.uniform(0.6, 1.0)
        a = int(pos * SR); out[a:a + len(c)] += c[:len(out) - a]
    # final settle into a cloth bag: soft thump
    t = np.arange(int(0.25 * SR)) / SR
    th = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05) * 0.5
    a = int((pos + 0.05) * SR); out[a:a + len(th)] += th[:len(out) - a]
    out = room(out, 0.4, 0.2, seed)
    return out / np.abs(out).max()


def gavel(seed=2):
    rng = np.random.default_rng(seed)
    t = np.arange(int(0.6 * SR)) / SR
    crack = bp(rng.normal(0, 1, len(t)), 600, 4500) * np.exp(-t / 0.012)
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.04) + 0.6 * np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.07)
    wood = np.sin(2 * np.pi * 820 * t) * np.exp(-t / 0.025) * 0.5
    y = crack * 1.2 + body + wood
    y = room(y, 0.9, 0.35, seed)
    return y / np.abs(y).max()


def low_bell(seed=3):
    t = np.arange(int(4.0 * SR)) / SR
    parts = [(110, 1.0, 2.2), (220.7, 0.5, 1.6), (331.5, 0.3, 1.1), (552, 0.18, 0.7), (847, 0.1, 0.4)]
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in parts)
    y *= np.minimum(1, t / 0.004)
    y = room(y, 1.5, 0.3, seed)
    return y / np.abs(y).max()


def place(buf, x, t, gain_db, pan=0.0):
    a = int(t * SR)
    if a >= len(buf):
        return
    g = 10 ** (gain_db / 20)
    n = min(len(x), len(buf) - a)
    if buf.ndim == 2:
        buf[a:a + n, 0] += x[:n] * g * (1 - max(0, pan))
        buf[a:a + n, 1] += x[:n] * g * (1 + min(0, pan))
    else:
        buf[a:a + n] += x[:n] * g


def env_follow(v, att=0.05, rel=0.45):
    """speech activity envelope 0..1 from mono voice track."""
    hop = int(0.01 * SR)
    m = len(v) // hop
    rms = np.sqrt((v[:m * hop].reshape(m, hop) ** 2).mean(1))
    act = (20 * np.log10(rms + 1e-9) > -45).astype(float)
    e = np.zeros(m); s = 0.0
    a1, a2 = 1 - np.exp(-0.01 / att), 1 - np.exp(-0.01 / rel)
    for i in range(m):
        s += (act[i] - s) * (a1 if act[i] > s else a2)
        e[i] = s
    return np.repeat(e, hop)[:len(v)] if m else np.zeros(len(v))


def loudnorm(inp, out, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", inp, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-af", af, "-c:a", "pcm_s24le", out], check=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    s = r[r.rfind("Summary"):]
    I = float(s.split("I:")[1].split("LUFS")[0]); TPk = float(s.split("Peak:")[1].split("dBFS")[0])
    return I, TPk


def main():
    tl = json.load(open(sys.argv[1])); music_p = sys.argv[2]; od = sys.argv[3]
    os.makedirs(od, exist_ok=True)
    N = int((tl["total"] + 0.5) * SR)
    voice = np.zeros(N)
    for l in tl["lines"]:
        x, sr = sf.read(f"{PROC}/{l['id']}.wav"); assert sr == SR
        a = int(l["start"] * SR); voice[a:a + len(x)] += x[:N - a]
    sf.write(f"{od}/narration_dry.wav", voice, SR, subtype="PCM_24")
    # SFX
    sfx = np.zeros((N, 2))
    place(sfx, coin_cascade(), 0.0, -9, 0.15)
    l2 = next(l for l in tl["lines"] if l["id"] == "s01_02")
    place(sfx, gavel(), l2["start"] + 0.9, -6)
    title = next(s for s in tl["scenes"] if s["id"] == "title")
    place(sfx, gavel(5), title["start"] + 0.05, -8)
    lq = [l for l in tl["lines"] if l["scene"] == "s35"]
    q = lq[5] if len(lq) > 5 else lq[-1]
    place(sfx, low_bell(), q["start"] + 1.6, -14)
    # music + ducking
    m, msr = sf.read(music_p); assert msr == SR
    if m.ndim == 1: m = np.stack([m, m], 1)
    mm = np.zeros((N, 2)); n = min(N, len(m)); mm[:n] = m[:n]
    # fade music tail
    endT = tl["total"]
    fo = int(3.0 * SR); e0 = max(0, int(endT * SR) - fo)
    mm[e0:e0 + fo] *= np.linspace(1, 0, min(fo, N - e0))[:, None]
    mm[e0 + fo:] = 0
    # levels: voice integrated ~ -18 dBFS RMS speech; music target ~ -21 dB under speech when talking, -16 dB in pauses
    v_rms = np.sqrt((voice[np.abs(voice) > 1e-4] ** 2).mean())
    # slow leveller: music short-term RMS (3 s windows, smoothed) -> constant, boost capped at +6 dB
    hop = int(0.1 * SR); m_ = N // hop
    mono = mm[:m_ * hop].mean(1).reshape(m_, hop)
    st = np.sqrt((mono ** 2).mean(1)) + 1e-7
    k = 30; st = np.sqrt(np.convolve(st ** 2, np.ones(k) / k, mode="same")) + 1e-7
    ref = np.median(st[st > np.percentile(st, 20)])
    lev = np.clip(ref / st, 10 ** (-12 / 20), 10 ** (6 / 20))
    lev = np.repeat(lev, hop); lev = np.pad(lev, (0, N - len(lev)), mode="edge")
    mm = mm * lev[:, None]
    m_rms = np.sqrt((mm ** 2).mean())
    base = v_rms / m_rms
    e = env_follow(voice)
    e = np.pad(e, (0, N - len(e)), mode='edge')
    g = base * 10 ** ((-17 + (-22.5 - -17) * e) / 20)
    music = mm * g[:, None]
    # open: music sits a bit higher before first words? keep same; hook sfx carries it
    for name, mix in [("mix_music", np.stack([voice, voice], 1) + music + sfx), ("mix_nomusic", np.stack([voice, voice], 1) + sfx)]:
        raw = f"{od}/{name}_raw.wav"
        sf.write(raw, mix / max(1.0, np.abs(mix).max()) * 0.95, SR, subtype="FLOAT")
        loudnorm(raw, f"{od}/{name}.wav")
        os.remove(raw)
        print(name, "LUFS/TP", lufs(f"{od}/{name}.wav"))
    sf.write(f"{od}/music_bed.wav", music, SR, subtype="PCM_24")
    # report music-under-voice gap during speech
    hop = int(0.4 * SR); gaps = []
    for a in range(0, N - hop, hop):
        if e[a:a + hop].mean() > 0.9:
            vr = np.sqrt((voice[a:a + hop] ** 2).mean()); mr = np.sqrt((music[a:a + hop] ** 2).mean())
            if vr > 1e-4 and mr > 1e-6:
                gaps.append(20 * np.log10(vr / mr))
    json.dump(dict(music_below_voice_db_median=float(np.median(gaps)), p10=float(np.percentile(gaps, 10)), p90=float(np.percentile(gaps, 90))),
              open(f"{od}/mix_report.json", "w"), indent=1)
    print("music below voice (speech windows): median %.1f dB, p10 %.1f, p90 %.1f" % (np.median(gaps), np.percentile(gaps, 10), np.percentile(gaps, 90)))


if __name__ == "__main__":
    main()
