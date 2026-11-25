"""Mix voices + music + SFX on the master timeline. Ducks music ~12 dB under voices, silent beats before punchlines,
then loudness-normalises to -16 LUFS / -1.5 dBTP."""
import json, subprocess, sys
import numpy as np, soundfile as sf
import synth as S
from synth import SR, place

tl = json.load(open("timeline.json"))
LI = {l["id"]: l for l in tl["lines"]}
SC = {s["scene"]: s for s in tl["scenes"]}
TOT = tl["total"]
N = int((TOT + 0.5) * SR)


def ln(lid):
    return LI[lid]["start"], LI[lid]["end"]


def s0(n):
    return SC[n]["start"]


def rel(lid, scene):
    a, b = ln(lid)
    return a - s0(scene), b - s0(scene)


# ---------------------------------------------------------------- voices
voice = np.zeros(N, np.float32)
env_by_spk = {k: np.zeros(N, np.float32) for k in ("PETE", "ZOE", "RIGGY")}
for l in tl["lines"]:
    y, sr = sf.read(f"audio/voice/{l['id']}.wav", dtype="float32")
    assert sr == SR
    # level match: speech RMS (active part) to target, shouts a bit hotter
    act = y[np.abs(y) > 0.02]
    rms = np.sqrt((act ** 2).mean()) if len(act) else 0.1
    tgt = 0.12 * (1.35 if l["style"] == "shout" else 1.0) * (1.08 if l["speaker"] == "RIGGY" else 1.0)
    y = y * (tgt / max(rms, 1e-4))
    place(voice, y, l["start"])
    place(env_by_spk[l["speaker"]], np.abs(y), l["start"])

# mouth envelopes for the animator (30 fps, 0..1)
FPS = 30
envs = {}
for k, e in env_by_spk.items():
    hop = SR // FPS
    nfr = int(TOT * FPS) + 2
    a = np.array([e[i * hop:(i + 1) * hop].mean() if i * hop < len(e) else 0 for i in range(nfr)])
    a = a / (np.percentile(a[a > 0.005], 95) if (a > 0.005).any() else 1)
    envs[k] = np.clip(a, 0, 1).round(3).tolist()
json.dump(envs, open("envelopes.json", "w"))

# ---------------------------------------------------------------- music
music = np.zeros(N, np.float32)
gain = np.zeros(N, np.float32)


def seg(a, b, fade=0.15):
    i0, i1 = int(max(0, a) * SR), int(min(TOT + 0.5, b) * SR)
    g = np.ones(i1 - i0, np.float32)
    f = int(fade * SR)
    if f and len(g) > 2 * f:
        g[:f] = np.linspace(0, 1, f)
        g[-f:] = np.linspace(1, 0, f)
    return i0, i1, g


# Scene 1 western
a, b = s0(1), SC[1]["end"]
w = S.western(b - a + 0.2)
i0, i1, g = seg(a, b - 0.6, 0.05)
music[i0:i1] += w[:i1 - i0] * g * 0.85
# Scenes 2..7 adventure (continuous so the beat never restarts), with hot variant in scene 5
a = s0(2) + 0.75
b = SC[7]["end"]
adv = S.adventure(b - a + 0.5)
hot = S.adventure(b - a + 0.5, intensity=1.3)
i0 = int(a * SR)
n = int((b - a) * SR)
mixsel = np.zeros(n, np.float32)
h0, h1 = int((s0(5) - a) * SR), int((SC[5]["end"] - a) * SR)
mixsel[h0:h1] = 1.0
k = int(0.3 * SR)
mixsel = np.convolve(mixsel, np.ones(k) / k, mode="same").astype(np.float32)
track = adv[:n] * (1 - mixsel) + hot[:n] * mixsel
fadein = np.clip(np.arange(n) / (0.2 * SR), 0, 1)
fadeout = np.clip((n - np.arange(n)) / (0.4 * SR), 0, 1)
music[i0:i0 + n] += track * fadein * fadeout * 0.8
# Scene 8 slow western
a, b = s0(8), SC[8]["end"]
w = S.western(b - a + 0.2, slow=True)
i0 = int(a * SR)
music[i0:i0 + len(w)][:len(w)] += w[:min(len(w), N - i0)] * 0.85 * np.clip(np.arange(min(len(w), N - i0)) / (0.6 * SR), 0, 1)

# silent beats before punchlines ("...Where's the dirt?" and "...Well.")
mute = np.ones(N, np.float32)


def silence(a, b, fin=0.3):
    i0, i1 = int(a * SR), int(b * SR)
    f = int(0.06 * SR)
    mute[i0 - f:i0] = np.minimum(mute[i0 - f:i0], np.linspace(1, 0, f))
    mute[i0:i1] = 0
    fi = int(fin * SR)
    seg_ = mute[i1:i1 + fi]
    mute[i1:i1 + fi] = np.minimum(seg_, np.linspace(0, 1, fi)[:len(seg_)])


p2 = ln("s2_pete2")
silence(p2[0] - 0.85, p2[1] + 0.05)
pa, pb = ln("s8_pete2a"), ln("s8_pete2b")
r8 = ln("s8_riggy1")
silence(pa[0] - 0.95, TOT + 0.4)   # music stays out from "...Well." to the end; game-over jingle takes over
music *= mute

# ducking: smooth voice activity
from scipy.ndimage import maximum_filter1d, uniform_filter1d
act = (uniform_filter1d(np.abs(voice), int(0.02 * SR)) > 0.01).astype(np.float32)
act = maximum_filter1d(act, int(0.25 * SR))           # hold
act = uniform_filter1d(act, int(0.12 * SR))            # attack/release smoothing
duck_db = -12.0
music *= (1 - act * (1 - 10 ** (duck_db / 20)))
music *= 0.42   # base music level relative to voices

# ---------------------------------------------------------------- SFX cues (mirrors scenes.py timings)
sfx = np.zeros(N, np.float32)
_cache = {}


def fx(name, at, g=1.0):
    if name not in _cache:
        _cache[name] = S.SFX[name]() if name in S.SFX else EXTRA[name]()
    place(sfx, _cache[name], at, g)


def sigh():
    d = 0.9
    t = S.t_(d)
    x = S.bandpass(S.noise(d, 1), 300, 1400) * np.exp(-t * 3) * np.clip(t * 10, 0, 1) * 0.5
    return x.astype(np.float32)


EXTRA = {"sigh": sigh}

# S1
s = s0(1)
l0, l1 = rel("s1_pete", 1)
fx("ding", s + 0.65, 0.5)
fx("buzz_short", s + 0.85, 0.35)
fx("whoosh", s + 1.45, 0.6)
fx("clang", s + 1.55, 0.8)
fx("sigh", s + 1.95, 0.9)
portal_t = l1 + 0.2
fx("zap", s + portal_t, 0.6)
fx("whoosh", s + portal_t + 0.4, 0.7)
fx("warp", s + portal_t + 0.85, 1.0)
# S2
s = s0(2)
fx("thud", s + 0.75, 1.1)
fx("heehaw", s + 0.9, 0.6)
p1 = rel("s2_pete1", 2)
fx("select", s + p1[0] + 0.1, 0.4)
r1 = rel("s2_riggy1", 2)
fx("levelup", s + r1[0] - 0.05, 0.35)
p2r = rel("s2_pete2", 2)
fx("whoosh", s + p2r[0] - 0.85, 0.35)
z2 = rel("s2_zoe2", 2)
fx("select", s + z2[0] + 0.9, 0.5)
# S3
s = s0(3)
fx("whoosh", s + 0.05, 0.6)
z1 = rel("s3_zoe1", 3)
for k in range(4):
    fx("select", s + z1[0] + 0.8 + k * 0.8, 0.22)
fx("buzz_short", s + z1[0] + 3.3, 0.5)
p1 = rel("s3_pete1", 3)
fx("pop", s + p1[0] - 0.05, 0.6)
fx("thud", s + p1[0] + 1.3, 0.45)
z2 = rel("s3_zoe2", 3)
fx("whoosh", s + z2[0] + 1.0, 0.5)
fx("ding", s + z2[0] + 1.65, 0.5)
# S4
s = s0(4)
z1 = rel("s4_zoe1", 4)
seg_ = z1[1] - z1[0]
fx("buzz_short", s + z1[0] + seg_ * 0.62, 0.45)
fx("buzz_short", s + z1[0] + seg_ * 0.75, 0.45)
fx("select", s + z1[0] + seg_ * 0.88, 0.5)
r1 = rel("s4_riggy1", 4)
z2 = rel("s4_zoe2", 4)
# WRONG storm: sad buzzers accelerating into a blur
t = r1[1] - 0.2
while t < z2[0] - 0.05:
    dt = t - (r1[1] - 0.2)
    gap = max(0.035, 0.3 * np.exp(-dt * 1.6))
    loud = 0.55 if dt < 1.0 else 0.22
    fx("buzz_short", s + t, loud)
    t += gap
r2 = rel("s4_riggy2", 4)
jack = r2[0] - 1.4
fx("drumroll", s + jack - 0.9, 0.5)
fx("fanfare", s + jack + 0.15, 0.8)
for k in range(10):
    fx("coin", s + jack + 0.4 + k * 0.17 + (k % 3) * 0.03, 0.45)
fx("levelup", s + r2[1] + 0.2, 0.5)
# S5
s = s0(5)
p1 = rel("s5_pete1", 5)
transform_t = p1[1] + 0.2
fx("roar", s + transform_t, 1.0)
fx("roar", s + transform_t + 0.7, 0.5)
fx("roar", s + transform_t + 1.6, 0.35)
z1 = rel("s5_zoe1", 5)
fx("levelup", s + z1[0] + 1.2, 0.5)
z2 = rel("s5_zoe2", 5)
fx("ding", s + z2[0] + 1.6, 0.5)
# S6
s = s0(6)
z1 = rel("s6_zoe1", 6)
wd = max(0.5, z1[0] - 0.5)
place(sfx, S.sfx_whir(wd), s + 0.5, 0.7)
fx("fire", s + z1[0], 0.7)
fx("unroll", s + z1[0] + 0.3, 0.8)
p2 = rel("s6_pete2", 6)
fx("pop", s + p2[0] + 0.05, 0.5)
fx("heehaw", s + p2[0] + 0.4, 0.8)
fx("thud", s + p2[0] + 0.8, 0.8)
r1 = rel("s6_riggy1", 6)
fx("steam", s + r1[0], 0.8)
tub_t = r1[1] + 0.3
fx("splash", s + tub_t + 0.15, 1.0)
fx("levelup", s + tub_t + 0.35, 0.45)
# S7
s = s0(7)
e7 = SC[7]["end"] - s
k = 0
while k / 4.5 < e7 - 0.4:
    tt = k / 4.5 + 0.03
    fx("key", s + tt, 0.8)
    fx("buzz_short", s + tt + 0.04, 0.18)
    k += 1
z1 = rel("s7_zoe1", 7)
fx("ding", s + z1[0] + 1.2, 0.5)
p2 = rel("s7_pete2", 7)
fx("levelup", s + p2[0] + 1.8, 0.55)
# S8
s = s0(8)
r1 = rel("s8_riggy1", 8)
fx("zap", s + r1[0] - 0.12, 0.6)
fx("gameover", s + r1[1] + 0.1, 0.9)
fx("coin", s + r1[1] + 0.6, 0.5)

# SFX dip lightly under dialogue so lines stay clear
sfx *= (1 - act * (1 - 10 ** (-5 / 20)))

mix = voice + music + sfx * 0.9
mix = mix[:int(TOT * SR)]
peak = np.abs(mix).max()
sf.write("audio/mix_pre.wav", (mix / peak * 0.7).astype(np.float32), SR)
sf.write("audio/stem_voice.wav", (voice[:len(mix)] / peak * 0.7).astype(np.float32), SR)

# two-pass loudnorm to -16 LUFS, -1.5 dBTP
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "audio/mix_pre.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
m = json.loads(js)
af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000,alimiter=limit=0.76:attack=2:release=50:level=false")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "audio/mix_pre.wav", "-af", af, "-ar", "48000", "audio/mix_final.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "audio/mix_final.wav", "-af", "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
print("final loudness I=", js["input_i"], "LUFS  TP=", js["input_tp"], "dBTP  duration", TOT)
