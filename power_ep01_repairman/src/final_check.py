"""Pre-export self-check (配乐规范 五 + 配音校验):

1. Loudness / true peak of the final mix (ffmpeg ebur128).
2. Music level under the voice: ducked music vs narration while the narrator speaks (target 15–18 dB lower).
3. ASR on every Chinese line: dry narration vs final mix vs a phone-speaker simulation of the mix
   (band-pass 300 Hz–7 kHz). The mix must not be noticeably worse than the dry voice.

python final_check.py MIX.wav DRY_VOICE.wav [DUCKED_MUSIC.wav]
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from script_data import LINES
from timeline import build, load_durations
from tts import WORK

sys.path.insert(0, os.path.join(WORK, "voice"))


def ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    summ = r[r.rindex("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    LRA = float(re.search(r"LRA:\s+(-?[\d.]+) LU", summ).group(1))
    TP = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    return I, TP, LRA


def phone(y, sr):
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, [300 / (sr / 2), 7000 / (sr / 2)], btype="band", output="sos")
    return sosfiltfilt(sos, y)


def main():
    mix_p, dry_p = sys.argv[1], sys.argv[2]
    duck_p = sys.argv[3] if len(sys.argv) > 3 else None
    I, TP, LRA = ebur128(mix_p)
    print(f"loudness: I={I:.1f} LUFS  true-peak={TP:.1f} dBTP  LRA={LRA:.1f} LU   (target -16 / <= -1.5)")
    tl = build(load_durations(os.path.join(WORK, "tts/durations.json")))
    mix, sr = sf.read(mix_p, dtype="float32", always_2d=True)
    dry, sr2 = sf.read(dry_p, dtype="float32", always_2d=True)
    mix, dry = mix.mean(1), dry.mean(1)
    if duck_p:
        duck, _ = sf.read(duck_p, dtype="float32", always_2d=True)
        duck = duck.mean(1)
        diffs = []
        for ln in LINES:
            if ln["id"] in tl["lines"] and ln["tts"]:
                s, e = tl["lines"][ln["id"]]
                a, b = int(s * sr), int(e * sr)
                v = np.sqrt(np.mean(dry[a:b] ** 2)) + 1e-9
                m = np.sqrt(np.mean(duck[a:b] ** 2)) + 1e-9
                if m > 1e-6:
                    diffs.append(20 * np.log10(v / m))
        if diffs:
            print(f"music under voice: median {np.median(diffs):.1f} dB below (p10 {np.percentile(diffs, 10):.1f}, "
                  f"p90 {np.percentile(diffs, 90):.1f})   (target 15–18)")
    from asr import pinyin_err, transcribe
    import librosa
    rows = []
    for ln in LINES:
        if ln["lang"] != "Chinese" or not ln["tts"] or ln["id"] not in tl["lines"]:
            continue
        s, e = tl["lines"][ln["id"]]
        a, b = int(max(0, s - 0.1) * sr), int((e + 0.1) * sr)
        errs = []
        for y in (dry[a:b], mix[a:b], phone(mix[a:b], sr)):
            y16 = librosa.resample(np.ascontiguousarray(y), orig_sr=sr, target_sr=16000).astype("float32")
            errs.append(pinyin_err(ln["tts"], transcribe(y16)))
        rows.append((ln["id"], *errs))
        if errs[1] > errs[0] + 0.05 or errs[2] > errs[0] + 0.08:
            print(f"  worse in mix: {ln['id']} dry={errs[0]:.3f} mix={errs[1]:.3f} phone={errs[2]:.3f}")
    arr = np.array([r[1:] for r in rows])
    print(f"ASR pinyin error (mean over {len(rows)} lines): dry {arr[:, 0].mean():.3f}  mix {arr[:, 1].mean():.3f}  "
          f"phone-speaker {arr[:, 2].mean():.3f}")
    json.dump(dict(I=I, TP=TP, LRA=LRA, asr=[list(map(lambda x: x if isinstance(x, str) else round(float(x), 3), r)) for r in rows]),
              open(os.path.join(WORK, "final_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
