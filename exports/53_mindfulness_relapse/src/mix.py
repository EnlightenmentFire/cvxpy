# -*- coding: utf-8 -*-
"""Build the narration stem from the timeline, mix music (ducked under the voice) + SFX, normalise to -15 LUFS /
-1.5 dBTP, and report levels. Also writes a no-music mix (voice + SFX).
usage: python mix.py
"""
import json, os, re, subprocess
import numpy as np, soundfile as sf

WORK = "/tmp/claude-0/work"
ST = f"{WORK}/stems"
PROC = f"{WORK}/tts/proc"
SR = 48000
TARGET = -15.0
MUSIC_UNDER = 21.0     # music level under the narration while speaking (dB, spec: 20-24)
PAUSE_LIFT = 4.0       # music may rise this much in pauses >= 0.8 s


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, float(tp[-1]) if tp else None


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    N = int((tl["total"] + 0.5) * SR)
    voice = np.zeros(N, np.float32)
    for l in tl["lines"]:
        x, sr = sf.read(f"{PROC}/{l['id']}.wav", dtype="float32")
        i = int(round(l["start"] * SR))
        voice[i:i + len(x)] += x[:N - i]
    sf.write(f"{ST}/voice.wav", voice, SR, subtype="FLOAT")
    mus, _ = sf.read(f"{ST}/music.wav", dtype="float32"); mus = mus[:N]
    fx, _ = sf.read(f"{ST}/sfx.wav", dtype="float32"); fx = fx[:N]
    if len(mus) < N:
        mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
    if len(fx) < N:
        fx = np.pad(fx, ((0, N - len(fx)), (0, 0)))
    # speech activity from the timeline (exact), smoothed into a ducking envelope
    act = np.zeros(N, np.float32)
    for l in tl["lines"]:
        a, b = int((l["start"] - 0.15) * SR), int((l["end"] + 0.25) * SR)
        act[max(0, a):b] = 1
    # pauses shorter than 0.8 s count as speech
    hop = SR // 100
    a100 = act[::hop].copy()
    run = 0
    for i in range(len(a100)):
        if a100[i] == 0:
            run += 1
        else:
            if 0 < run < 80:
                a100[i - run:i] = 1
            run = 0
    # smooth (attack 0.3 s, release 0.8 s)
    env = np.zeros_like(a100); e = 1.0
    for i, v in enumerate(a100):
        k = 0.033 if v > e else 0.0125
        e += (v - e) * k; env[i] = e
    env = np.interp(np.arange(N) / hop, np.arange(len(env)), env).astype(np.float32)
    # voice speech level
    vs = voice[act > 0]
    v_db = rms_db(vs)
    m_db = rms_db(mus.mean(1))
    g_speech = 10 ** ((v_db - MUSIC_UNDER - m_db) / 20)
    gain = g_speech * (10 ** (PAUSE_LIFT / 20)) ** (1 - env)
    # very start: let the opening bowl strike ring above the bed for the first 0.3 s
    music = mus * gain[:, None]
    vo = np.stack([voice, voice], 1)
    full = vo + music + fx * 0.55
    nomus = vo + fx * 0.55
    for name, mix in [("mix_full", full), ("mix_nomusic", nomus)]:
        p = f"{ST}/{name}_pre.wav"
        sf.write(p, mix.astype(np.float32), SR, subtype="FLOAT")
        # linear gain to target, then a transparent peak limiter (4x oversampled) -> no dynamic loudnorm pumping
        I0, _ = lufs(p)
        g = TARGET - I0
        out = f"{ST}/{name}.wav"
        for _ in range(3):
            af = (f"volume={g:.2f}dB,aresample=192000,alimiter=limit=0.80:attack=3:release=60:level=false:asc=1,"
                  "aresample=48000")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", af, "-c:a", "pcm_s24le", out], check=True)
            I1, tp1 = lufs(out)
            if abs(I1 - TARGET) < 0.15 and tp1 <= -1.4:
                break
            g += TARGET - I1
        m = {"normalization_type": f"gain {g:+.1f} dB + limiter"}
        I, tp = lufs(out)
        print(f"{name}: {I:.1f} LUFS, true peak {tp} dBTP (linear={m.get('normalization_type')})")
    # music vs voice report (speech regions and pauses)
    md = music.mean(1)
    sp = act > 0
    print(f"music under narration while speaking: {v_db - rms_db(md[sp]):.1f} dB; in pauses: {v_db - rms_db(md[~sp]):.1f} dB below speech level")


if __name__ == "__main__":
    main()
