"""The flat 'machine' reading of the generation-9 text (English), used once in the cold open.
Kokoro-82M (Apache-2.0) English male voice, then WORLD vocoder with a constant pitch
(no intonation at all) and a light bit-crush, so it sounds like a machine reciting."""
import os
import sys

import numpy as np
import pyworld as pw
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_utils import normalize_rms, transcribe  # noqa: E402

out = sys.argv[1]
voice = sys.argv[2] if len(sys.argv) > 2 else "am_michael"
TEXT = ("black-tailed jackrabbits, white-tailed jackrabbits, blue-tailed jackrabbits, "
        "red-tailed jackrabbits, yellow")

from kokoro import KPipeline  # noqa: E402

pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
chunks = [a.numpy() if hasattr(a, "numpy") else np.asarray(a) for _, _, a in pipe(TEXT, voice=voice, speed=0.92)]
wav = np.concatenate(chunks).astype(np.float64)
sr = 24000

# WORLD analysis -> constant F0 -> resynthesis (monotone, machine-like)
f0, t = pw.harvest(wav, sr, f0_floor=60, f0_ceil=300, frame_period=5.0)
sp = pw.cheaptrick(wav, f0, t, sr)
ap = pw.d4c(wav, f0, t, sr)
flat = np.where(f0 > 0, 104.0, 0.0)
y = pw.synthesize(flat, sp, ap, sr, frame_period=5.0)

# light bit-crush + sample-and-hold for a digital edge
step = 2 ** 7
y = np.round(y * step) / step
hold = 2
y = np.repeat(y[::hold], hold)[: len(y)]
y = y.astype(np.float32)
# abrupt end on "yellow" (the original text is cut off mid-word): short fade of 8 ms only
y[-int(0.008 * sr):] *= np.linspace(1, 0, int(0.008 * sr))
y = normalize_rms(y, sr, -20.0)
sf.write(out, y, sr)
print("robot:", out, round(len(y) / sr, 2), "s | ASR:", transcribe(y, sr, lang="en"))
