# -*- coding: utf-8 -*-
"""Final mix, following the 配乐规范 chain:
  bed = music + gear clicks -> EQ -4 dB @ 3 kHz -> short fade-in (no fade-out: the film loops)
  -> sidechain-compressed by the narration (threshold 0.03, ratio 6, attack 10 ms, release 300 ms)
  -> + narration -> loudnorm two-pass (linear) to -16 LUFS, true peak <= -1.5 dBTP.
The bed gain is solved so that, while the narrator speaks, the ducked bed sits DUCK_TARGET dB under the voice.

Usage: python mix.py voice.wav music.wav sfx.wav timeline.json out_dir
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

SR = 48000
DUCK_TARGET = float(os.environ.get("DUCK_TARGET", "11.0"))   # dB below the voice while speaking (spec: 10-12)
SFX_GAIN_DB = float(os.environ.get("SFX_GAIN_DB", "-9.0"))   # clicks relative to the score inside the bed
L6_DIP_DB = float(os.environ.get("L6_DIP_DB", "-3.0"))
FADE_IN = 0.08            # spec: <= 0.3 s


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


def frames_db(x, win):
    n = len(x) // win
    x = x[: n * win].reshape(n, win, -1)
    return 10 * np.log10(np.mean(x ** 2, axis=(1, 2)) + 1e-12)


def main():
    vpath, mpath, spath, tlpath, out = sys.argv[1:6]
    os.makedirs(out, exist_ok=True)
    tl = json.load(open(tlpath))
    dur = tl["duration"]
    v, _ = sf.read(vpath, dtype="float32")
    if v.ndim == 1:
        v = v[:, None]
    nfr = int(round(dur * 30))
    n = int(round(nfr / 30 * SR))           # frame-exact length (851 frames) so audio and picture end together
    vv = np.zeros((n, 1), np.float32)
    vv[: min(n, len(v))] = v[:n]
    sf.write(f"{out}/voice_full.wav", vv, SR, subtype="FLOAT")
    m, _ = sf.read(mpath, dtype="float32")
    s, _ = sf.read(spath, dtype="float32")
    def fit(x):                              # wrap-pad from the start: the music is a loop
        if len(x) >= n:
            return x[:n]
        return np.concatenate([x, x[: n - len(x)]])
    bed = fit(m) + fit(s) * 10 ** (SFX_GAIN_DB / 20)
    # local dip under the key line L6 ("甲，永远碰不上丑"): -3 dB with 80 ms ramps, so its last word stays clear
    L = {l["id"]: l for l in tl["lines"]}
    tt = np.arange(n) / SR
    a0, a1, r = L["L6"]["start"] - 0.10, L["L6"]["end"] + 0.10, 0.08
    w = np.clip(np.minimum((tt - (a0 - r)) / r, ((a1 + r) - tt) / r), 0, 1)
    bed *= (1 - w * (1 - 10 ** (L6_DIP_DB / 20)))[:, None]
    sf.write(f"{out}/bed.wav", bed, SR, subtype="FLOAT")

    win = int(0.05 * SR)
    vdb = frames_db(vv, win)
    speaking = vdb > (np.max(vdb) - 30)

    gain_db = -3.0
    for it in range(5):
        g = 10 ** (gain_db / 20)
        fc = (f"[1:a]volume={g:.5f},equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d={FADE_IN}[m];"
              f"[0:a]aformat=channel_layouts=stereo,asplit=2[v][sc];"
              f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=10:release=300[duck];"
              f"[v]anullsink")
        run(["ffmpeg", "-y", "-i", f"{out}/voice_full.wav", "-i", f"{out}/bed.wav", "-filter_complex", fc,
             "-map", "[duck]", "-c:a", "pcm_f32le", "-ar", str(SR), f"{out}/bed_ducked.wav"])
        d, _ = sf.read(f"{out}/bed_ducked.wav", dtype="float32")
        ddb = frames_db(d[:n], win)[: len(vdb)]
        diff = np.median((vdb - ddb)[speaking[: len(ddb)]])
        print(f"iter {it}: bed gain {gain_db:+.2f} dB -> voice minus ducked bed while speaking = {diff:.2f} dB", flush=True)
        if abs(diff - DUCK_TARGET) < 0.3:
            break
        gain_db += diff - DUCK_TARGET
    # sum, then two-pass loudnorm (linear)
    run(["ffmpeg", "-y", "-i", f"{out}/voice_full.wav", "-i", f"{out}/bed_ducked.wav", "-filter_complex",
         "[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=first:normalize=0[o]",
         "-map", "[o]", "-c:a", "pcm_f32le", f"{out}/premix.wav"])
    err = run(["ffmpeg", "-i", f"{out}/premix.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
               "-f", "null", "-"])
    js = json.loads(err[err.rindex("{"): err.rindex("}") + 1])
    # linear gain to -16 LUFS, then a 4x-oversampled brickwall limiter so the true peak stays <= -1.5 dBTP
    g = -16.0 - float(js["input_i"])
    chain = (f"volume={g:.3f}dB,aresample={SR * 4},alimiter=limit={10 ** (-2.0 / 20):.4f}:attack=1:release=60:level=disabled,"
             f"aresample={SR},afade=t=in:d=0.004,afade=t=out:st={n / SR - 0.012:.4f}:d=0.012")   # de-click ramps only
    run(["ffmpeg", "-y", "-i", f"{out}/premix.wav", "-af", chain, "-c:a", "pcm_s24le", f"{out}/mix.wav"])
    err = run(["ffmpeg", "-i", f"{out}/mix.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js2 = json.loads(err[err.rindex("{"): err.rindex("}") + 1])
    rep = dict(bed_gain_db=round(float(gain_db), 2), duck_diff_db=round(float(diff), 2), premix=js,
               final_I=js2["input_i"], final_TP=js2["input_tp"], final_LRA=js2["input_lra"])
    json.dump(rep, open(f"{out}/mix_report.json", "w"), indent=1)
    print("final: I", js2["input_i"], "LUFS  TP", js2["input_tp"], "dBTP  LRA", js2["input_lra"])


if __name__ == "__main__":
    main()
