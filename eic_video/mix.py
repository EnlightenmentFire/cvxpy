# -*- coding: utf-8 -*-
"""Build narration stem from processed lines + timeline, mix with music (ducked) and sfx, loudness-normalise.
Outputs in /tmp/claude-0/work/audio: narration.wav, mix.wav (music), mix_nomusic.wav, narration.srt, timeline_lines.json
"""
import json, os, subprocess, re
import numpy as np, soundfile as sf

WORK = "/tmp/claude-0/work"
A = f"{WORK}/audio"
SR = 48000
TL = json.load(open(f"{WORK}/timeline.json"))
MUSIC_BELOW = float(os.environ.get("MUSIC_BELOW", 21.0))   # dB below narration (integrated)


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])


def gain_to(path, out, target, ch=None):
    i, _ = lufs(path)
    x, sr = sf.read(path)
    x = x * 10 ** ((target - i) / 20)
    sf.write(out, x.astype(np.float32), sr, subtype="FLOAT")


def narration():
    n = int((TL["total"] + 1) * SR)
    v = np.zeros(n, np.float32)
    for ln in TL["lines"]:
        x, sr = sf.read(f"{WORK}/tts/proc/{ln['id']}.wav")
        i = int(round(ln["start"] * SR))
        v[i:i + len(x)] += x[:max(0, min(len(x), n - i))]
    sf.write(f"{A}/narration_raw.wav", v, SR, subtype="FLOAT")
    gain_to(f"{A}/narration_raw.wav", f"{A}/narration.wav", -16.0)


def srt():
    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
    out = []
    for k, ln in enumerate(TL["lines"], 1):
        out.append(f"{k}\n{ts(ln['start'])} --> {ts(ln['end'])}\n{ln['t']}\n")
    open(f"{A}/narration.srt", "w").write("\n".join(out))


def main():
    os.makedirs(A, exist_ok=True)
    narration()
    srt()
    vi, _ = lufs(f"{A}/narration.wav")
    # music level: integrated MUSIC_BELOW dB under narration, then sidechain ducking (extra ~3-5 dB while speaking)
    gain_to(f"{A}/music_raw.wav", f"{A}/music_lvl.wav", vi - MUSIC_BELOW + 3.0)
    gain_to(f"{A}/sfx.wav", f"{A}/sfx_lvl.wav", vi - 15.0)
    fc = ("[1:a]aformat=sample_fmts=fltp:channel_layouts=stereo,volume=1.0[m];"
          "[0:a]aformat=sample_fmts=fltp:channel_layouts=stereo,asplit=3[v1][v2][v3];"
          "[m][v1]sidechaincompress=threshold=0.03:ratio=3:attack=40:release=600:makeup=1[md];"
          "[2:a]aformat=sample_fmts=fltp:channel_layouts=stereo[s];"
          "[v2][md][s]amix=inputs=3:normalize=0:duration=longest[mx];"
          "[v3][s]amix=inputs=2:normalize=0:duration=longest[nm]")
    run(["ffmpeg", "-y", "-v", "error", "-i", f"{A}/narration.wav", "-i", f"{A}/music_lvl.wav", "-i", f"{A}/sfx_lvl.wav",
         "-filter_complex", fc, "-map", "[mx]", "-ar", "48000", "-c:a", "pcm_f32le", f"{A}/mix_pre.wav",
         "-map", "[nm]", "-ar", "48000", "-c:a", "pcm_f32le", f"{A}/nomusic_pre.wav"])
    for src, dst in ((f"{A}/mix_pre.wav", f"{A}/mix.wav"), (f"{A}/nomusic_pre.wav", f"{A}/mix_nomusic.wav")):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True)
        j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af + ",aresample=48000", "-c:a", "pcm_s24le", dst])
        print(dst, lufs(dst))
    # measure music-under-voice in speech regions
    v, _ = sf.read(f"{A}/narration.wav")
    m, _ = sf.read(f"{A}/music_lvl.wav")
    m = m.mean(1) if m.ndim > 1 else m
    L = min(len(v), len(m))
    win = SR // 2
    vs, ms = [], []
    for i in range(0, L - win, win):
        a = np.sqrt((v[i:i + win] ** 2).mean()); b = np.sqrt((m[i:i + win] ** 2).mean())
        if a > 0.02:
            vs.append(a); ms.append(b)
    print("music below voice in speech (pre-duck, RMS):", round(20 * np.log10(np.mean(vs) / np.mean(ms)), 1), "dB")


if __name__ == "__main__":
    main()
