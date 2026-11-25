# -*- coding: utf-8 -*-
"""Audio pipeline.
  python audio.py post            raw TTS -> processed lines (trim, pause cap, HPF, -18 dBFS RMS, optional tempo)
  python audio.py stems           narration.wav + sfx.wav from timeline.json
  python audio.py mix             final mixes: mix_music.wav and mix_nomusic.wav (-15 LUFS, -1.5 dBTP)
"""
import sys, os, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = "/tmp/claude-0/work"
RAW, PROC, AUD = f"{WORK}/tts/raw", f"{WORK}/tts/proc", f"{WORK}/audio"
SR = 48000
TEMPO = float(os.environ.get("TEMPO", 1.0))
MAX_PAUSE = 0.42


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 40, -55)
    v = db > thr
    if not v.any():
        return x
    i0 = max(0, np.argmax(v) - 2); i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not v[k]:
            j = k
            while j < i1 and not v[j]:
                j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.008 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def post():
    os.makedirs(PROC, exist_ok=True)
    tot_c = tot_d = 0
    for d in all_lines():
        p = f"{RAW}/{d['id']}.wav"
        if not os.path.exists(p):
            print("MISSING", d["id"]); continue
        x, sr = sf.read(p); x = x.astype(np.float32)
        if x.ndim > 1:
            x = x.mean(1)
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
        x = trim_cap(x, SR)
        x = tempo(x, TEMPO)
        x = sosfiltfilt(butter(4, 60, "highpass", fs=SR, output="sos"), x).astype(np.float32)
        db, n = frame_db(x, SR); v = db > db.max() - 35
        rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
        x = x * (10 ** (-18 / 20) / (rms + 1e-9))
        pk = np.abs(x).max()
        if pk > 0.95:
            x *= 0.95 / pk
        sf.write(f"{PROC}/{d['id']}.wav", x, SR, subtype="PCM_24")
        c = len(re.sub(r"[^\u4e00-\u9fff]", "", d["say"]))
        tot_c += c; tot_d += len(x) / SR + d["p"]
    print(f"{tot_c} hanzi in {tot_d:.1f}s -> {tot_c / tot_d * 60:.0f} hanzi/min (incl. pauses)")


# ---------------------------------------------------------------- sfx synthesis
def _lp(x, fc, order=2):
    return sosfiltfilt(butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def boom(dur=3.0, f0=55, amp=1.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 400))
    sub = np.sin(2 * np.pi * (f0 * t - 8 * t ** 2)) * env
    nz = _lp(rng.standard_normal(len(t)), 400) * np.exp(-t * 3.0) * (1 - np.exp(-t * 300))
    crack = _lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 18)
    y = 0.9 * sub + 1.6 * nz / (np.abs(nz).max() + 1e-9) * 0.5 + 0.25 * crack / (np.abs(crack).max() + 1e-9)
    return (amp * y / np.abs(y).max()).astype(np.float32)


def drum(amp=1.0, f0=70, seed=1):
    t = np.arange(int(1.6 * SR)) / SR
    env = np.exp(-t * 5) * (1 - np.exp(-t * 800))
    y = np.sin(2 * np.pi * (f0 * t - 10 * t ** 2)) * env
    rng = np.random.default_rng(seed)
    y += 0.3 * _lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 30)
    return (amp * y / np.abs(y).max()).astype(np.float32)


def dive(dur=5.0, amp=0.6, seed=2):
    """Aircraft dive roar: engine buzz + wind noise rising in pitch/level."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    u = t / dur
    f = 90 + 160 * u ** 1.6
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = np.sign(np.sin(ph)) * 0.3 + np.sin(2 * ph) * 0.3
    buzz = _lp(buzz, 1500)
    wind = rng.standard_normal(len(t))
    lo, hi = 300, 2500
    wind = sosfiltfilt(butter(2, [lo, hi], "bandpass", fs=SR, output="sos"), wind)
    wind /= np.abs(wind).max()
    env = (u ** 1.8) * (1 - np.exp(-(1 - u) * 60))
    y = (0.6 * buzz + 0.8 * wind * (0.3 + u)) * env
    return (amp * y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += gain * x[:n]


def stems():
    tl = json.load(open(f"{WORK}/timeline.json"))
    N = int((tl["total"] + 1) * SR)
    nar = np.zeros(N, np.float32)
    for l in tl["lines"]:
        x, _ = sf.read(f"{PROC}/{l['id']}.wav"); place(nar, x.astype(np.float32), l["s0"])
    sf.write(f"{AUD}/narration.wav", nar, SR, subtype="PCM_24")
    sfx = np.zeros(N, np.float32)
    L = {l["id"]: l for l in tl["lines"]}
    # opening sound hook: war drum on frame 0, dive roar, three impacts timed with the flashes
    place(sfx, drum(1.0, 62), 0.0, 0.9)
    place(sfx, drum(0.8, 66, 3), 0.62, 0.6)
    hit0 = L["s00_02"]["s0"] + 0.3
    dv = dive(hit0 + 0.05, 0.55); place(sfx, dv, 0.0, 1.0)
    for k in range(3):
        place(sfx, boom(3.0, 50 + 6 * k, 1.0, k), hit0 + k * 0.9, 0.85)
    place(sfx, drum(0.9, 60, 5), L["s00_05"]["s0"] + 0.9, 0.8)  # stamp "编出来的"
    # 10:22 / 10:25 / 10:26 hits
    l5 = L["s05_05"]; d5 = max(3.0, l5["s1"] - l5["s0"])
    for k, f in enumerate((0.05, 0.5, 0.85)):
        place(sfx, boom(3.5, 48, 1.0, 10 + k), l5["s0"] + d5 * f, 0.8)
    l11 = L["s05_11"]
    for k in range(4):
        place(sfx, boom(3.0, 45 + 5 * k, 1.0, 20 + k), l11["s0"] + 0.6 + k * 0.7, 0.55)
    place(sfx, boom(3.0, 52, 1.0, 30), L["s07_02"]["s0"] + 0.8, 0.5)
    # section drums
    for s in tl["scenes"]:
        if s["id"] in ("s02", "s03", "s04", "s05", "s06", "s07"):
            place(sfx, drum(0.7, 64, 7), s["t0"] + 0.05, 0.55)
    sf.write(f"{AUD}/sfx.wav", sfx, SR, subtype="PCM_24")
    # speech activity envelope for music ducking
    act = np.zeros(int(tl["total"] * 100) + 200, np.float32)
    for l in tl["lines"]:
        act[int(l["s0"] * 100) - 15:int(l["s1"] * 100) + 25] = 1
    np.save(f"{AUD}/speech_act.npy", act)
    print("stems ok")


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); P = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    return I, P


def loudnorm(src, dst, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "48000", "-ac", "2", dst], check=True)


def mix():
    nar, _ = sf.read(f"{AUD}/narration.wav"); sfx, _ = sf.read(f"{AUD}/sfx.wav")
    mus, _ = sf.read(f"{AUD}/music.wav")
    N = len(nar)
    mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))[:N]
    # speech-only loudness of narration and music level, both via RMS over active speech
    act = np.load(f"{AUD}/speech_act.npy")
    idx = np.minimum((np.arange(N) / SR * 100).astype(int), len(act) - 1)
    a = act[idx] > 0.5
    v_db = 10 * np.log10((nar[a] ** 2).mean() + 1e-12)
    m_db = 10 * np.log10((mus[a] ** 2).mean() + 1e-12)
    REL = float(os.environ.get("MUS_REL", -21.0))
    g_speech = 10 ** ((v_db + REL - m_db) / 20)
    g_gap = g_speech * 10 ** (4.5 / 20)
    # smooth envelope (300 ms)
    env = np.where(act > 0.5, g_speech, g_gap).astype(np.float32)
    k = np.ones(30) / 30
    env = np.convolve(env, k, mode="same")
    genv = env[idx][:, None]
    nar2 = np.c_[nar, nar]; sfx2 = np.c_[sfx, sfx]
    out_m = nar2 + mus * genv + 0.7 * sfx2
    out_n = nar2 + 0.7 * sfx2
    for name, y in (("mix_music", out_m), ("mix_nomusic", out_n)):
        y = y / max(1.0, np.abs(y).max() / 0.98)
        sf.write(f"{AUD}/{name}_pre.wav", y.astype(np.float32), SR, subtype="FLOAT")
        loudnorm(f"{AUD}/{name}_pre.wav", f"{AUD}/{name}.wav")
        print(name, lufs(f"{AUD}/{name}.wav"))
    # report music-under-voice margin
    print(f"music under voice during speech: {REL:.1f} dB (gaps +4.5 dB)")


if __name__ == "__main__":
    dict(post=post, stems=stems, mix=mix)[sys.argv[1]]()
