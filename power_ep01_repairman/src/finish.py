"""Post-production, end to end: calibrate music level -> full mix -> self-check -> encode both versions.

python finish.py
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from timeline import build, load_durations
from tts import WORK

FINAL = os.path.join(WORK, "final")
PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MUSIC = os.path.join(FINAL, "组织里的权力01_维修工_配乐版.mp4")
OUT_NOMUSIC = os.path.join(FINAL, "组织里的权力01_维修工_无配乐版.mp4")
TARGET_DIFF = 16.5   # 规范: music 15–18 dB under the voice while the narrator speaks


def run(args, **kw):
    print("$", " ".join(os.path.basename(a) if os.path.isabs(a) else a for a in args), flush=True)
    return subprocess.run(args, check=True, capture_output=True, text=True, cwd=HERE, **kw)


def mix(out, gain, t_end=None):
    args = [PY, "mix.py", out] + ([str(t_end)] if t_end else []) + [f"--music-gain={gain:.4f}"]
    r = run(args)
    print(r.stdout.strip().splitlines()[-1], flush=True)
    stems = re.search(r"stems in (\S+)", r.stdout).group(1)
    return stems


def music_under_voice(stems, tl):
    v, sr = sf.read(os.path.join(stems, "voice.wav"), dtype="float32", always_2d=True)
    m, _ = sf.read(os.path.join(stems, "ducked_music.wav"), dtype="float32", always_2d=True)
    v, m = v.mean(1), m.mean(1)
    diffs = []
    for lid, (s, e) in tl["lines"].items():
        a, b = int(s * sr), min(len(v), int(e * sr))
        if b - a < sr // 2 or b > len(m):
            continue
        vr = np.sqrt(np.mean(v[a:b] ** 2)) + 1e-9
        mr = np.sqrt(np.mean(m[a:b] ** 2)) + 1e-9
        if mr > 1e-5:
            diffs.append(20 * np.log10(vr / mr))
    return float(np.median(diffs)), float(np.percentile(diffs, 10)), float(np.percentile(diffs, 90))


def main():
    tl = build(load_durations(os.path.join(WORK, "tts/durations.json")))
    video = os.path.join(FINAL, "video_noaudio.mp4")
    assert os.path.exists(video), "video not rendered"
    # 1) calibrate the music bus on the first five minutes (covers 铺底 and 推进)
    gain = 1.0
    for it in range(3):
        stems = mix(os.path.join(FINAL, "_calib.wav"), gain, t_end=300)
        med, p10, p90 = music_under_voice(stems, tl)
        print(f"calibration {it}: gain {gain:.3f} -> music {med:.1f} dB under voice (p10 {p10:.1f}, p90 {p90:.1f})", flush=True)
        if abs(med - TARGET_DIFF) < 0.6:
            break
        gain *= 10 ** ((med - TARGET_DIFF) / 20)
    # 2) full mix with music
    audio = os.path.join(FINAL, "audio_music.wav")
    stems = mix(audio, gain)
    med, p10, p90 = music_under_voice(stems, tl)
    print(f"FULL MIX: music {med:.1f} dB under voice (p10 {p10:.1f}, p90 {p90:.1f}); bus gain {gain:.3f}", flush=True)
    json.dump(dict(gain=gain, under_voice_median=med, p10=p10, p90=p90, stems=stems),
              open(os.path.join(FINAL, "mix_info.json"), "w"), indent=1)
    # 3) encode both versions under 95 MB
    for aud, out in ((audio, OUT_MUSIC), (os.path.join(FINAL, "audio_nomusic.wav"), OUT_NOMUSIC)):
        r = run([PY, "encode.py", video, aud, out, "--max-mb=95"])
        print(r.stdout.strip(), flush=True)
    # 4) the climax on its own, for a separate listen (规范 五)
    L = tl["lines"]
    a, b = L["s6_04"][0] - 2.0, L["s6_06"][0] + 6.0
    clip = os.path.join(FINAL, "高潮段_单独试听.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", OUT_MUSIC,
                    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-b:a", "160k", clip], check=True)
    print("climax clip", clip, flush=True)
    # 5) self-check (loudness, ASR dry vs mix vs phone speaker)
    r = run([PY, "final_check.py", audio, os.path.join(stems, "voice.wav"), os.path.join(stems, "ducked_music.wav")])
    print(r.stdout, flush=True)
    print("FINISH_OK", flush=True)


if __name__ == "__main__":
    main()
