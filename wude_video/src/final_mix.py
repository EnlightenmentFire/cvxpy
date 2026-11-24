"""Final mix per 配乐规范 §四.

voice  : narration bus, integrated loudness -16 LUFS
music  : volume, 3 kHz cut (-4 dB, Q=1), fade in 2 s / out 3 s, sidechain-ducked by the voice
sfx    : event accents (磬 / 编钟 / 长音 …), same 3 kHz cut, lighter sidechain
master : amix (normalize=0) -> loudnorm I=-16 TP=-1.5 LRA=11 (two pass, linear when possible)

Also writes the ducked music bus alone so the ducking depth can be measured.
"""
import json
import os
import re
import subprocess

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

SR = 48000


def write_voice(tl, voice_dir, path, target_lufs=-16.0):
    n = int(tl.total * SR) + SR
    v = np.zeros(n)
    for ln in tl.lines:
        p = f"{voice_dir}/{ln['id']}.wav"
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        y, sr = sf.read(p)
        assert sr == SR
        i = int(round(ln["t0"] * SR))
        v[i:i + len(y)] += y[: n - i]
    v = v[: int(tl.total * SR)]
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(np.stack([v, v], 1))
    g = 10 ** ((target_lufs - lufs) / 20)
    v = tp_limit(v * g, -2.0)
    sf.write(path, np.stack([v, v], 1).astype(np.float32), SR, subtype="FLOAT")
    return lufs, 20 * np.log10(g)


def tp_limit(x, ceiling_db=-2.0, release=0.06):
    """Look-ahead peak limiter on the 4x-oversampled envelope (keeps true peak under the ceiling)."""
    from scipy.signal import resample_poly
    from scipy.ndimage import maximum_filter1d
    lim = 10 ** (ceiling_db / 20)
    up = np.abs(resample_poly(x, 4, 1))
    pk = up.reshape(-1, 4).max(axis=1)[: len(x)]
    if len(pk) < len(x):
        pk = np.pad(pk, (0, len(x) - len(pk)))
    need = np.minimum(1.0, lim / np.maximum(pk, 1e-9))
    la = int(0.002 * SR)
    need = -maximum_filter1d(-need, size=2 * la + 1)          # look-ahead: take the min around each sample
    # release smoothing (one-pole, only upwards)
    a = np.exp(-1 / (release * SR))
    g = np.empty_like(need)
    cur = 1.0
    for i in range(0, len(need), 256):
        blk = need[i:i + 256]
        tv = blk.min()
        cur = tv if tv < cur else tv + (cur - tv) * a ** 256
        g[i:i + 256] = np.minimum(cur, blk)
    return x * g


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:])
    return r


def graph(total, music_vol, th, ratio, sfx_vol, sfx_th, ln_params=None, duck_only=False):
    end = max(0.0, total - 3.0)
    g = (
        "[0:a]aformat=sample_fmts=fltp:channel_layouts=stereo,asplit=3[v][sc1][sc2];"
        f"[1:a]aformat=sample_fmts=fltp:channel_layouts=stereo,volume={music_vol},"
        "equalizer=f=3000:t=q:w=1:g=-4,"
        f"afade=t=in:d=2,afade=t=out:st={end:.3f}:d=3[m];"
        f"[m][sc1]sidechaincompress=threshold={th}:ratio={ratio}:attack=15:release=500[duck];"
        f"[2:a]aformat=sample_fmts=fltp:channel_layouts=stereo,volume={sfx_vol},"
        "equalizer=f=3000:t=q:w=1:g=-4[s];"
        f"[s][sc2]sidechaincompress=threshold={sfx_th}:ratio=4:attack=10:release=300[sd]"
    )
    if duck_only:
        return g + ";[v]anullsink;[sd]anullsink;[duck]anull[out]"
    g += ";[v][duck][sd]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.78:attack=2:release=60:level=0"
    if ln_params is None:
        g += ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[out]"
    else:
        p = ln_params
        g += (f",loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={p['input_i']}:measured_TP={p['input_tp']}:"
              f"measured_LRA={p['input_lra']}:measured_thresh={p['input_thresh']}:offset={p['target_offset']}:"
              "linear=true:print_format=json[out]")
    return g


def mix(voice, music, sfx, out_wav, total, music_vol=0.5, th=0.02, ratio=10, sfx_vol=1.0, sfx_th=0.05):
    base = ["ffmpeg", "-y", "-hide_banner", "-i", voice, "-i", music, "-i", sfx]
    # pass 1: measure
    r = run(base + ["-filter_complex", graph(total, music_vol, th, ratio, sfx_vol, sfx_th), "-map", "[out]",
                    "-f", "null", "-"])
    js = json.loads(re.findall(r"\{[^{}]+\}", r.stderr)[-1])
    # pass 2: apply (linear)
    r2 = run(base + ["-filter_complex", graph(total, music_vol, th, ratio, sfx_vol, sfx_th, js), "-map", "[out]",
                     "-ar", str(SR), "-c:a", "pcm_f32le", out_wav])
    js2 = json.loads(re.findall(r"\{[^{}]+\}", r2.stderr)[-1])
    return js, js2


def ducked_music(voice, music, sfx, out_wav, total, music_vol=0.5, th=0.02, ratio=10, sfx_vol=1.0, sfx_th=0.05):
    base = ["ffmpeg", "-y", "-hide_banner", "-i", voice, "-i", music, "-i", sfx]
    run(base + ["-filter_complex", graph(total, music_vol, th, ratio, sfx_vol, sfx_th, duck_only=True),
                "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_f32le", out_wav])


def ducking_report(tl, voice_wav, duck_wav):
    """Median voice-minus-music loudness during narration, and music level in long pauses."""
    v, _ = sf.read(voice_wav)
    m, _ = sf.read(duck_wav)
    n = min(len(v), len(m))
    v, m = v[:n].mean(1), m[:n].mean(1)

    def db(x):
        return 10 * np.log10(np.mean(x ** 2) + 1e-12)

    diffs = []
    for ln in tl.lines:
        a, b = int((ln["t0"] + 0.3) * SR), int((ln["t1"] - 0.2) * SR)
        if b - a < SR:
            continue
        diffs.append(db(v[a:b]) - db(m[a:b]))
    gaps = []
    for x, y in zip(tl.lines[:-1], tl.lines[1:]):
        if y["t0"] - x["t1"] >= 1.2:
            a, b = int((x["t1"] + 0.6) * SR), int((y["t0"] - 0.1) * SR)
            gaps.append(db(m[a:b]))
    return dict(voice_minus_music_median=float(np.median(diffs)),
                p10=float(np.percentile(diffs, 10)), p90=float(np.percentile(diffs, 90)),
                music_in_long_pauses_db=float(np.median(gaps)) if gaps else None,
                voice_speech_db=float(np.median([db(v[int((l['t0'] + .3) * SR):int((l['t1'] - .2) * SR)])
                                                 for l in tl.lines if l['dur'] > 1.5])))
