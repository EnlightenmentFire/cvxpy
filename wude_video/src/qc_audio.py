"""配乐规范 §五 self-check, done by measurement (I cannot listen):
  * loudness: integrated LUFS and true peak of the final mix
  * ducking: music 15-18 dB under the voice while narrating; level in long pauses
  * pop-outs: music jumping up while the voice is speaking
  * intelligibility: per-line ASR on voice-only vs. mix vs. phone-speaker simulation
usage: qc_audio.py <audio_dir>   (expects voice.wav, duck.wav, mix.wav)
"""
import json
import os
import subprocess
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, os.path.dirname(__file__))
from timeline import Timeline
import final_mix as F
import tts_worker as T

BUILD = "/home/user/wude_build"
SR = 48000


def true_peak(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null",
                        "-"], capture_output=True, text=True)
    lines = [l for l in r.stderr.splitlines() if "Peak:" in l]
    return float(lines[-1].split()[1]) if lines else None


def phone(x):
    sos = butter(4, [300, 7000], btype="bandpass", fs=SR, output="sos")
    return sosfiltfilt(sos, x)


def main():
    d = sys.argv[1]
    segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
    tl = Timeline(segs, json.load(open(f"{BUILD}/voice_post/durations.json")))
    mix, _ = sf.read(f"{d}/mix.wav")
    voice, _ = sf.read(f"{d}/voice.wav")
    meter = pyln.Meter(SR)
    rep = dict(mix_lufs=float(meter.integrated_loudness(mix)), mix_true_peak_dbtp=true_peak(f"{d}/mix.wav"),
               voice_lufs=float(meter.integrated_loudness(voice)))
    rep["ducking"] = F.ducking_report(tl, f"{d}/voice.wav", f"{d}/duck.wav")
    # pop-outs: music 400 ms level rising > 6 dB above its own previous 2 s while the voice speaks
    m, _ = sf.read(f"{d}/duck.wav")
    m = m.mean(1)
    v = voice.mean(1)
    hop = int(0.1 * SR)
    lv = np.array([10 * np.log10(np.mean(m[i:i + 4 * hop] ** 2) + 1e-12) for i in range(0, len(m) - 4 * hop, hop)])
    vv = np.array([10 * np.log10(np.mean(v[i:i + 4 * hop] ** 2) + 1e-12) for i in range(0, len(v) - 4 * hop, hop)])
    pops = []
    for i in range(20, min(len(lv), len(vv))):
        if vv[i] > -35 and lv[i] - np.median(lv[i - 20:i]) > 6:
            t = i * 0.1
            if not pops or t - pops[-1] > 2:
                pops.append(round(t, 1))
    rep["music_popouts_while_speaking"] = pops
    # ASR: voice-only vs mix vs phone simulation
    asr = T.ASR()
    rows = []
    for ln in tl.lines:
        a, b = int((ln["t0"] - 0.1) * SR), int((ln["t1"] + 0.15) * SR)
        exp = T.pinyin_seq(ln["tts"])
        res = {}
        for name, sig in (("voice", v[a:b]), ("mix", mix[a:b].mean(1)), ("phone", phone(mix[a:b].mean(1)))):
            got = T.pinyin_seq(asr(sig.astype(np.float32), SR))
            res[name] = 1 - T.edit_distance(exp, got) / max(1, len(exp))
        rows.append(dict(id=ln["id"], **res))
        print(ln["id"], {k: round(x, 3) for k, x in res.items()}, flush=True)
    for k in ("voice", "mix", "phone"):
        rep[f"asr_{k}_mean_acc"] = float(np.mean([r[k] for r in rows]))
    rep["asr_lines_worse_by_5pct"] = [r["id"] for r in rows if r["voice"] - r["mix"] > 0.05]
    json.dump(dict(report=rep, lines=rows), open(f"{d}/qc.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
