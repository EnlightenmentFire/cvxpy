"""Pre-export self-checks from the music spec (§五), done by measurement:
1. ASR on voice-only vs. full mix vs. a simulated phone loudspeaker (band-limited mono):
   syllable error rate against the script must not get noticeably worse with music.
2. Music never 'jumps out' under speech: ducked-music level jumps while the narration talks.
3. Writes the climax excerpt for a separate listen."""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tts"))
sys.path.insert(0, os.path.join(HERE, "..", "render"))
sys.path.insert(0, os.path.join(HERE, ".."))
import timeline  # noqa: E402
from audio_utils import per, transcribe  # noqa: E402

SR = 48000


def phone(path, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-af",
                    "highpass=f=300:poles=2,lowpass=f=7000:poles=2,acompressor=threshold=0.1:ratio=3,volume=-3dB",
                    out], check=True)


def seg_texts(segs):
    return [(s.key, s.start, s.end, "".join(e.say for e in s.events if e.kind != "robot")) for s in segs]


def asr_by_segment(path, segs):
    w, sr = sf.read(path, dtype="float32")
    if w.ndim > 1:
        w = w.mean(axis=1)
    res = {}
    for key, s0, s1, ref in seg_texts(segs):
        a = w[int(s0 * sr): int(s1 * sr)]
        hyp = transcribe(a, sr)
        res[key] = (round(per(ref, hyp), 4), hyp)
    return res


def jumps_under_speech(duck_path, segs, win=0.4):
    m, sr = sf.read(duck_path, dtype="float32")
    m = m.mean(axis=1) if m.ndim > 1 else m
    hop = int(win * sr)
    db = np.array([20 * np.log10(np.sqrt(np.mean(m[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(m) - hop, hop)])
    speech = np.zeros(len(db), bool)
    for s in segs:
        for e in s.events:
            speech[int(np.ceil(e.start / win)): int(e.end / win)] = True   # whole windows inside a sentence
    bad = []
    for i in range(5, len(db)):
        if speech[i] and speech[i - 5:i].all():
            base = np.median(db[i - 5:i])
            if db[i] - base > 6:
                bad.append(round(i * win, 1))
    return bad


if __name__ == "__main__":
    voice_dir, robot, stems = sys.argv[1:4]
    segs, total = timeline.build(voice_dir, robot, None)
    report = {}
    phone(os.path.join(stems, "mix.wav"), os.path.join(stems, "mix_phone.wav"))
    for name in ("voice.wav", "mix.wav", "mix_phone.wav"):
        r = asr_by_segment(os.path.join(stems, name), segs)
        report[name] = {k: v[0] for k, v in r.items()}
        report[name]["_mean"] = round(float(np.mean([v[0] for v in r.values()])), 4)
        print(name, report[name], flush=True)
    report["music_jumps_under_speech_s"] = jumps_under_speech(os.path.join(stems, "music_ducked.wav"), segs)
    ev = timeline.ev_by_id(segs)
    a, b = ev["c10_14"].start - 6, ev["c11_1"].start + 4
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i",
                    os.path.join(stems, "mix.wav"), "-c:a", "libmp3lame", "-b:a", "192k",
                    os.path.join(stems, "climax_excerpt.mp3")], check=True)
    report["climax_excerpt"] = [round(a, 2), round(b, 2)]
    json.dump(report, open(os.path.join(stems, "checks.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, dict)}, ensure_ascii=False))
