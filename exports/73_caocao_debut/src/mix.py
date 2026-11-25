# -*- coding: utf-8 -*-
"""Assemble narration from processed lines on the timeline, mix with music (ducked, ~-21 dB under voice) and SFX.
outputs: out/narration.wav, out/mix_music.wav (final), out/mix_nomusic.wav, out/mix_report.json"""
import json, sys, subprocess, re
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import uniform_filter1d
sys.path.insert(0, "/tmp/claude-0/w73/proj")
import timeline

W = "/tmp/claude-0/w73"; OUT = f"{W}/out"
SR = 48000
TL = timeline.build()
N = int((TL["total"]) * SR)
meter = pyln.Meter(SR)


def lufs(x):
    return meter.integrated_loudness(x if x.ndim == 2 else np.stack([x, x], 1))


def place(buf, seg, t0):
    a = int(round(t0 * SR)); b = min(len(buf), a + len(seg))
    buf[a:b] += seg[:b - a]


nar = np.zeros(N, np.float32)
for r in TL["lines"]:
    x, sr = sf.read(f"{W}/tts/proc/{r['id']}.wav", dtype="float32")
    assert sr == SR
    place(nar, x, r["t0"])
g = 10 ** ((-15.0 - lufs(nar)) / 20); nar *= g
nar2 = np.stack([nar, nar], 1)

mus, _ = sf.read(f"{OUT}/music.wav", dtype="float32"); mus = mus[:N]
if len(mus) < N: mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
sfx, _ = sf.read(f"{OUT}/sfx.wav", dtype="float32"); sfx = sfx[:N]
if len(sfx) < N: sfx = np.pad(sfx, ((0, N - len(sfx)), (0, 0)))

# speech activity envelope from the timeline (lines), smoothed -> duck music in speech, lift in gaps
act = np.zeros(N, np.float32)
for r in TL["lines"]:
    a, b = int((r["t0"] - 0.15) * SR), int((r["t1"] + 0.1) * SR)
    act[max(a, 0):b] = 1
act = uniform_filter1d(act, int(0.6 * SR))
UNDER = float(sys.argv[1]) if len(sys.argv) > 1 else 21.0     # music below voice (dB) while speaking
mus_l = lufs(mus)
base_gain_db = (-15.0 - UNDER) - mus_l
gain_db = base_gain_db + 4.0 * (1 - act)        # +4 dB in pauses
# opening: before the first line, music a bit fuller under the SFX hook
t_first = TL["lines"][0]["t0"]
gain_db[:int(t_first * SR)] += 2.0
mus_g = mus * (10 ** (gain_db / 20))[:, None]
sfx_g = sfx * (10 ** (-3.0 / 20))

full = nar2 + mus_g + sfx_g
nomus = nar2 + sfx_g


def finalize(x, path):
    sf.write(path + ".pre.wav", x, SR, subtype="FLOAT")
    # two-pass loudnorm to -15 LUFS / -1.5 dBTP
    p1 = subprocess.run(["ffmpeg", "-nostats", "-i", path + ".pre.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    j = json.loads(p1[p1.rfind("{"):p1.rfind("}") + 1])
    af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path + ".pre.wav", "-af", af, "-c:a", "pcm_s24le", path], check=True)
    return j


j1 = finalize(full, f"{OUT}/mix_music.wav")
j2 = finalize(nomus, f"{OUT}/mix_nomusic.wav")
sf.write(f"{OUT}/narration.wav", nar, SR, subtype="PCM_24")

# measure music-under-voice per line (RMS dB difference)
diffs = []
for r in TL["lines"]:
    a, b = int(r["t0"] * SR), int(r["t1"] * SR)
    v = np.sqrt((nar[a:b] ** 2).mean() + 1e-12); m = np.sqrt((mus_g[a:b] ** 2).mean() + 1e-12)
    diffs.append(20 * np.log10(v / m))
rep = dict(under_db_median=float(np.median(diffs)), under_db_min=float(np.min(diffs)), under_db_max=float(np.max(diffs)),
           loudnorm_full=j1, loudnorm_nomusic=j2, total=TL["total"])
json.dump(rep, open(f"{OUT}/mix_report.json", "w"), indent=1)
print(f"music under voice: median {rep['under_db_median']:.1f} dB (min {rep['under_db_min']:.1f}, max {rep['under_db_max']:.1f})")
