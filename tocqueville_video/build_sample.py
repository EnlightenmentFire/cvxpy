"""~1 minute voice sample (segment 二 · 路被堵了): dry voice + a version with music bed and SFX."""
import sys, os, json
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
from mixlib import SR, load, place, envelope, rms_db, fit_music, limiter
import sfx

PROC = "/tmp/claude-0/work/tts/proc"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/sample"
os.makedirs(OUT, exist_ok=True)
lines = [d for d in all_lines() if d["scene"] == "s02"]
t = 1.2
marks = {}
segs = []
for d in lines:
    x = load(f"{PROC}/{d['id']}.wav")
    segs.append((t, x, d))
    marks[d["id"]] = (t, t + len(x) / SR)
    t += len(x) / SR + max(0.35, d["gap"] + 0.1)
total = t + 1.5
voice = np.zeros(int(total * SR), np.float32)
for st, x, d in segs:
    place(voice, x, st)
sf.write(f"{OUT}/voice_dry.wav", voice, SR, subtype="PCM_24")
# music + sfx
mus = load("/tmp/claude-0/work/music/america.wav", stereo=True)
mus = fit_music(mus, total, 2.5, 3.0)
mus = mus / (10 ** (rms_db(mus.mean(1)) / 20)) * 10 ** (-27 / 20)
env = envelope(voice)
duck_db = -11.0 * env
mus = mus * (10 ** (duck_db / 20))[:, None]
fx = np.zeros(int(total * SR), np.float32)
place(fx, sfx.wind(total, level=-44), 0)
place(fx, sfx.birds(total, level=-46, n_chirps=7), 0)
a, b = marks["s02_02"]
place(fx, sfx.creak(1.3, level=-34), a + 3.4)
place(fx, sfx.crash(level=-25), a + 4.6)
a, b = marks["s02_04"]
place(fx, sfx.murmur(b - a + 1.5, level=-40), a - 0.3)
a, b = marks["s02_05"]
place(fx, sfx.saw(2.6, level=-32), a - 0.2)
place(fx, sfx.crash(seed=20, level=-34), b + 0.1)
mix = mus + (voice + fx)[:, None]
mix = limiter(mix)
sf.write(f"{OUT}/voice_sample_mix.wav", mix, SR, subtype="PCM_24")
json.dump({k: v for k, v in marks.items()}, open(f"{OUT}/marks.json", "w"), indent=1)
print("total", total, "voice rms", rms_db(voice[voice != 0]))
