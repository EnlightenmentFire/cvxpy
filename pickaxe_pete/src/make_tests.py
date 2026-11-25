"""15-second Scene 4 voice tests per engine (same character FX applied to Kokoro and Chatterbox; Dia raw)."""
import os, subprocess, sys, numpy as np, soundfile as sf, librosa
from select_takes import FX
from script_data import LINES
out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
SPK = {l[0]: l[2] for l in LINES}
ids = ["s4_zoe1", "s4_riggy1", "s4_pete1", "s4_zoe2", "s4_riggy2"]
def fxit(path, spk):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", FX[spk] + ",aresample=44100", "-ac", "1", "/tmp/_fx.wav"], check=True)
    y, _ = librosa.load("/tmp/_fx.wav", sr=44100); return y
def build(name, paths):
    parts = []
    for lid, p in paths:
        y, sr = librosa.load(p, sr=44100); y, _ = librosa.effects.trim(y, top_db=38)
        sf.write("/tmp/_t.wav", y, 44100)
        y = fxit("/tmp/_t.wav", SPK[lid]) if lid else y
        parts += [y / (np.abs(y).max() + 1e-6) * 0.8, np.zeros(int(0.3 * 44100))]
    sf.write("/tmp/_c.wav", np.concatenate(parts), 44100)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/_c.wav", "-b:a", "160k", f"{out_dir}/scene4_test_{name}.mp3"], check=True)
    print(name, round(sum(len(p) for p in parts) / 44100, 1), "s")
build("kokoro", [(i, f"tts/kokoro/{i}.wav") for i in ids])
build("chatterbox", [(i, f"tts/chatterbox/{i}.wav") for i in ids])
build("dia", [(None, "tts/dia/s4_dialog.wav"), (None, "tts/dia/s4_riggy.wav")])
