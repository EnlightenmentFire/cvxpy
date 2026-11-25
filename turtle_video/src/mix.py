"""Final mix per the house 配乐规范.

  voice  : narration lines on the timeline
  music  : MusicGen takes arranged in three layers (bed -> build -> climax), resolving to solo piano
  sfx    : typewriter / ticks / fax / stamp (sound design, not music)

  ffmpeg: music EQ (-4 dB @ 3 kHz), 2 s fade-in / 3 s fade-out, sidechaincompress keyed on the
  narration (attack 15 ms, release 500 ms), amix normalize=0; then loudness to -16 LUFS with a
  true-peak ceiling below -1.5 dBTP.

usage: python mix.py LINES_DIR TAKES_DIR OUTDIR
writes OUTDIR/mix.wav (with music), OUTDIR/mix_nomusic.wav, stems, OUTDIR/mix_report.json
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from audio import (SR, add, db, sfx_key, sfx_ding, sfx_tick, sfx_stamp, sfx_boom, sfx_swell, sfx_paper, sfx_fax,
                   typing_events, RNG)
from compose import build_timeline
from scenes import Ctx, streak_times

XFADE = 3.0
# target RMS (dBFS, before ducking) per layer
LEVEL = {"bed": -28.5, "build": -26.0, "drop": -30.5, "climax": -22.0, "reflect": -27.5, "end": -27.0}
SC = dict(threshold=0.035, ratio=4.0, attack=15, release=500)


# ------------------------------------------------------------------ helpers
def load_takes(takes_dir, names):
    out = []
    for nm in names:
        x, sr = sf.read(os.path.join(takes_dir, nm + ".wav"), dtype="float32", always_2d=True)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, 1)
        y = resample_poly(x, SR // math.gcd(sr, SR), sr // math.gcd(sr, SR), axis=0).astype(np.float32)
        out.append(y)
    return out


def rms_db(x):
    m = x.mean(1) if x.ndim == 2 else x
    hop = int(0.4 * SR)
    n = len(m) // hop
    r = np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    act = r > r.max() * 10 ** (-30 / 20)
    return 20 * math.log10(np.sqrt((r[act] ** 2).mean()) + 1e-12)


def set_level(x, target):
    return x * db(target - rms_db(x))


def eqp(n):
    t = np.linspace(0, 1, n)
    return np.sin(t * np.pi / 2), np.cos(t * np.pi / 2)


def chain(takes, dur, trim_head=0.4, trim_tail=0.6):
    """Concatenate takes in rotation with equal-power crossfades until dur seconds."""
    n_need = int(dur * SR)
    xf = int(XFADE * SR)
    out = np.zeros((0, 2), np.float32)
    k = 0
    while len(out) < n_need:
        t = takes[k % len(takes)]
        t = t[int(trim_head * SR): len(t) - int(trim_tail * SR)]
        if len(out) == 0:
            out = t.copy()
        else:
            fi, fo = eqp(xf)
            head = out[:-xf]
            mid = out[-xf:] * fo[:, None] + t[:xf] * fi[:, None]
            out = np.concatenate([head, mid, t[xf:]])
        k += 1
    return out[:n_need]


def region(buf, x, t0, fade_in=XFADE, fade_out=XFADE):
    x = x.copy()
    a, b = int(fade_in * SR), int(fade_out * SR)
    if a:
        x[:a] *= eqp(a)[0][:, None]
    if b:
        x[-b:] *= eqp(b)[1][:, None]
    add(buf, x, t0, 0.0)


def env_gain(n, points):
    """Piecewise-linear gain (dB) envelope from [(t, dB), ...]."""
    ts = np.array([p[0] for p in points])
    gs = np.array([p[1] for p in points])
    t = np.arange(n) / SR
    return db(np.interp(t, ts, gs)).astype(np.float32)


def peak_time(x, win=6.0):
    m = x.mean(1)
    hop = int(0.5 * SR)
    n = len(m) // hop
    r = np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    w = int(win / 0.5)
    sm = np.convolve(r, np.ones(w) / w, mode="valid")
    return (int(np.argmax(sm)) + w / 2) * 0.5


# ------------------------------------------------------------------ arrangement
def arrange(items, total, takes_dir, choice):
    n = int(total * SR) + SR
    buf = np.zeros((n, 2), np.float32)
    T = {}
    for it in items:
        if it["kind"] == "chapter":
            T["card_" + it["seg"]] = it["start"]
        else:
            T["scene_" + it["seg"]] = it["start"]
            for k, (a, b) in it["cues"].items():
                T[k] = (it["start"] + a, it["start"] + b)
    t_ch4 = T["card_hard"]
    t_fax = T["t_end"][0]
    t_diff = T["t_diff"][0]
    t_bet_end = T["t_bet"][1]
    t_doubt = T["card_doubt"]
    t_end = T["scene_end"]
    hard = next(i for i in items if i["seg"] == "hard" and i["kind"] == "scene")
    _, tb0, _ = streak_times(Ctx(0, 0, hard["cues"]))
    t_big = hard["start"] + tb0

    L = {k: [set_level(t, LEVEL[k]) for t in load_takes(takes_dir, v)] for k, v in choice.items()}

    # 1) bed: opening through the rules
    region(buf, chain(L["bed"], t_ch4 + 1.5), 0.0, fade_in=2.0)
    # 2) build: conflict (why it is hard, divergence, first part of 1988), with a lift on the big win
    b = chain(L["build"], t_fax + 1.5 - (t_ch4 - 1.5))
    rel = t_big - (t_ch4 - 1.5)
    b *= env_gain(len(b), [(0, 0), (rel - 0.4, 0), (rel + 0.2, 5.0), (rel + 3.0, 5.0), (rel + 6.0, 0), (len(b) / SR, 0)])[:, None]
    region(buf, b, t_ch4 - 1.5)
    # 3) drop: the programme ends; almost nothing but a low drone under the fax
    climax = L["climax"][0]
    pk = peak_time(climax)
    t_peak = t_bet_end + 0.9                     # the music's fullest moment lands in the narration pause
    c_start = max(t_diff - 1.5, t_peak - pk)
    region(buf, chain(L["drop"], c_start + XFADE - (t_fax - 1.5)), t_fax - 1.5)
    # 4) climax: rises under the last lines of the chapter, stands alone in the pause, then recedes (never looped)
    take_len = (len(climax) / SR) - 0.6
    c_len = min((t_doubt + 2.5 + XFADE) - c_start, take_len)
    c = chain([climax], c_len, trim_head=0.0)
    rp = t_peak - c_start
    c *= env_gain(len(c), [(0, -9), (rp - 9, -5), (rp - 1.6, 0), (rp + 1.4, 0), (rp + 4.5, -6), (len(c) / SR, -10)])[:, None]
    region(buf, c, c_start)
    # 6) end: the solo-piano take is placed so its natural decay finishes 2 s before the last frame
    end_take = L["end"][0]
    end_len = len(end_take) / SR - 1.0
    e_start = max(t_end - 1.5, total - 2.0 - end_len)
    # 5) reflect: is following the rules always right? (from the climax's tail to the ending)
    r0 = min(t_doubt + 2.5, c_start + c_len - XFADE)
    region(buf, chain(L["reflect"], (e_start + XFADE) - r0), r0)
    e = chain(L["end"], min(total - e_start, end_len))
    region(buf, e, e_start, fade_out=0.8)
    marks = dict(t_ch4=t_ch4, t_big=t_big, t_fax=t_fax, t_diff=t_diff, t_peak=t_peak, t_doubt=t_doubt, t_end=t_end)
    return buf[:n], marks


# ------------------------------------------------------------------ stems
def build_stems(lines_dir):
    durs, voice = {}, {}
    for f in os.listdir(lines_dir):
        if f.endswith(".wav") and not f.startswith("."):
            y, sr = sf.read(os.path.join(lines_dir, f), dtype="float32")
            voice[f[:-4]] = y
            durs[f[:-4]] = len(y) / SR
    items, lines, total = build_timeline(durs)
    n = int(total * SR) + SR
    vbuf = np.zeros((n, 2), np.float32)
    missing = [ln["id"] for ln in lines if ln["id"] not in voice]
    if missing:
        print(f"WARNING: {len(missing)} narration lines missing (test mix only): {missing[:5]}...")
    for ln in lines:
        if ln["id"] in voice:
            add(vbuf, voice[ln["id"]], ln["start"], 0.0)
    fx = np.zeros((n, 2), np.float32)
    keys = [sfx_key(s) for s in range(12)]
    ding, tick, stamp = sfx_ding(), sfx_tick(), sfx_stamp()
    for tt, kind in typing_events(items):
        if kind == "key":
            add(fx, keys[int(RNG.integers(0, 12))], tt, -24 + RNG.uniform(-2, 2), pan=RNG.uniform(-0.3, 0.3))
        elif kind == "softkey":
            add(fx, keys[int(RNG.integers(0, 12))], tt, -31 + RNG.uniform(-2, 2), pan=RNG.uniform(-0.3, 0.3))
        elif kind == "ding":
            add(fx, ding, tt, -23, pan=0.35)
        elif kind == "stamp":
            add(fx, stamp, tt, -14)
    for it in items:
        if it["kind"] == "chapter":
            add(fx, sfx_swell(2.4), it["start"] + 0.05, -32)
        if it["kind"] != "scene":
            continue
        x = Ctx(0, 0, it["cues"])
        if it["seg"] == "title":
            add(fx, sfx_boom(), it["start"] + 0.75, -14)
        if it["seg"] == "hard":
            t_loss, tb0, _ = streak_times(x)
            for k, tl in enumerate(t_loss):
                add(fx, tick, it["start"] + tl, -25 + k * 0.6)
            add(fx, sfx_boom(), it["start"] + tb0, -22)
        if it["seg"] == "t88":
            add(fx, sfx_fax(), it["start"] + x.s("t_end") + 0.4, -21)
        if it["seg"] == "out":
            add(fx, sfx_paper(14, 2.3), it["start"] + x.s("o_apps") - 0.3, -33)
    return items, lines, total, vbuf[:n], fx[:n]


# ------------------------------------------------------------------ ffmpeg sidechain + loudness
UNDER_VOICE_DB = 14.5      # music level under narration, below the narration's median level
SC_T_DB = -50.0            # compressor threshold (dBFS) for the key signal
SC_RATIO = 20.0


def voice_mask(vbuf, gap_hold=0.65, pad=0.06, thr_db=-45.0):
    """1 while narration is speaking; gaps shorter than gap_hold (breaths, commas, line breaks) are bridged."""
    from scipy.ndimage import binary_closing, binary_dilation
    hop = int(0.01 * SR)
    m = vbuf.mean(1)
    n = len(m) // hop
    r = 20 * np.log10(np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-12)
    act = r > thr_db
    act = binary_closing(act, structure=np.ones(int(gap_hold / 0.01)))
    act = binary_dilation(act, structure=np.ones(int(2 * pad / 0.01) + 1))
    mask = np.repeat(act.astype(np.float32), hop)
    mask = np.pad(mask, (0, len(m) - len(mask)))
    k = int(0.02 * SR)   # 20 ms ramps
    return np.convolve(mask, np.ones(k) / k, mode="same").astype(np.float32)


def duck_key(mus, mask, voice_med_db):
    """Key for sidechaincompress: present only while narration speaks; its level is chosen so the
    compressor pulls the music to (voice median - UNDER_VOICE_DB), whatever layer is playing."""
    hop = int(0.05 * SR)
    m = mus.mean(1)
    n = len(m) // hop
    lv = 20 * np.log10(np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-12)
    lv = np.convolve(lv, np.ones(10) / 10, mode="same")            # 0.5 s smoothing
    target = voice_med_db - UNDER_VOICE_DB
    gr = np.clip(lv - target, 0.0, 40.0)
    k_db = SC_T_DB + gr / (1 - 1 / SC_RATIO)
    amp = 10 ** (k_db / 20) * np.sqrt(2)                            # sine peak for that RMS
    amp = np.interp(np.arange(len(m)), np.arange(n) * hop + hop / 2, amp)
    t = np.arange(len(m)) / SR
    key = (mask[: len(m)] * amp * np.sin(2 * np.pi * 3000 * t)).astype(np.float32)
    return np.stack([key, key], 1)


def ffmpeg_sidechain(vpath, mpath, fpath, kpath, total, out_mix, out_duck):
    thr = 10 ** (SC_T_DB / 20)
    flt = (f"[1:a]equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2,afade=t=out:st={total - 5:.3f}:d=3[m];"
           f"[m][3:a]sidechaincompress=threshold={thr:.6f}:ratio={SC_RATIO}:knee=1:attack=15:release=500:detection=rms[duck];"
           f"[duck]asplit=2[d1][d2];"
           f"[0:a][d1][2:a]amix=inputs=3:duration=first:normalize=0[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-i", mpath, "-i", fpath, "-i", kpath, "-filter_complex", flt,
                    "-map", "[out]", "-c:a", "pcm_f32le", out_mix, "-map", "[d2]", "-c:a", "pcm_f32le", out_duck], check=True)


def true_peak(x, chunk=480000):
    """Per-sample true-peak estimate (4x oversampled), computed in chunks."""
    out = np.empty(len(x), np.float32)
    for i in range(0, len(x), chunk):
        seg = x[max(0, i - 64): i + chunk + 64]
        up = resample_poly(seg, 4, 1, axis=0)
        tp = np.abs(up).max(1)
        tp = tp[: (len(tp) // 4) * 4].reshape(-1, 4).max(1)
        off = i - max(0, i - 64)
        out[i: i + chunk] = tp[off: off + min(chunk, len(x) - i)]
    return out


def true_peak_limit(x, ceiling_dbtp=-1.7, release=0.08):
    """True-peak limiter: 1 ms blocks, 2 ms lookahead, one-pole release; touches only the peaks."""
    from scipy.ndimage import minimum_filter1d
    thr = db(ceiling_dbtp)
    tp = true_peak(x)
    g = np.minimum(1.0, thr / np.maximum(tp, 1e-9))
    if g.min() >= 1.0:
        return x
    B = 48
    nb = len(g) // B + 1
    gb = np.ones(nb)
    gp = np.pad(g, (0, nb * B - len(g)), constant_values=1.0).reshape(nb, B).min(1)
    gp = minimum_filter1d(gp, size=5)
    a = math.exp(-1 / (release * 1000))
    s = 1.0
    for i in range(nb):
        s = gp[i] if gp[i] < s else a * s + (1 - a) * gp[i]
        gb[i] = s
    gs = np.interp(np.arange(len(g)), np.arange(nb) * B + B / 2, gb)
    gs = np.minimum(gs, g)
    return x * gs[:, None].astype(np.float32)


def finish_loudness(x, target=-16.0):
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(x)
    y = x * db(target - lufs)
    y = true_peak_limit(y, -1.7)
    return y.astype(np.float32), lufs


def ebur128(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    vals = {}
    for key, tag in (("I", "I:"), ("LRA", "LRA:"), ("TP", "Peak:")):
        i = txt.find(tag)
        if i >= 0:
            vals[key] = float(txt[i + len(tag):].split()[0])
    return vals


# ------------------------------------------------------------------ checks
def window_db(x, win=0.4):
    m = x.mean(1) if x.ndim == 2 else x
    hop = int(win * SR)
    n = len(m) // hop
    r = np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r)


def ratio_report(vbuf, duck, mask, marks):
    v = window_db(vbuf)
    m = window_db(duck)
    hop = int(0.4 * SR)
    mk = mask[: (len(mask) // hop) * hop].reshape(-1, hop).mean(1)
    n = min(len(v), len(m), len(mk))
    v, m, mk = v[:n], m[:n], mk[:n]
    vmed = float(np.median(v[mk > 0.99]))
    act = (mk > 0.99) & (v > vmed - 12)            # windows fully inside narration with real speech energy
    diff = v[act] - m[act]
    t = np.arange(n) * 0.4
    climax = (t > marks["t_peak"] - 3) & (t < marks["t_peak"] + 3)
    lift = (t > marks["t_big"] - 0.5) & (t < marks["t_big"] + 5)
    pause = mk < 0.01
    over = [round(float(t[i]), 1) for i in np.where(pause & ~climax & ~lift & (m > vmed - 3))[0]]
    return dict(voice_median_db=round(vmed, 1),
                voice_minus_music_db_median=round(float(np.median(diff)), 1),
                voice_minus_music_db_p05=round(float(np.percentile(diff, 5)), 1),
                voice_minus_music_db_p95=round(float(np.percentile(diff, 95)), 1),
                music_in_pauses_max_rel_voice_db=round(float(np.max(m[pause & ~climax] - vmed)) if (pause & ~climax).any() else -99, 1),
                music_at_climax_rel_voice_db=round(float(np.max(m[climax] - vmed)), 1),
                pause_windows_music_within_3db_of_voice=over[:20])


def main(lines_dir, takes_dir, outdir, choice_json=None):
    os.makedirs(outdir, exist_ok=True)
    choice = json.load(open(choice_json)) if choice_json else json.load(open(os.path.join(takes_dir, "choice.json")))
    items, lines, total, vbuf, fx = build_stems(lines_dir)
    mus, marks = arrange(items, total, takes_dir, choice)
    n = len(vbuf)
    mus = mus[:n]
    p = lambda name: os.path.join(outdir, name)
    sf.write(p("stem_voice.wav"), vbuf, SR, subtype="FLOAT")
    sf.write(p("stem_music_raw.wav"), mus, SR, subtype="FLOAT")
    sf.write(p("stem_sfx.wav"), fx, SR, subtype="FLOAT")
    mask = voice_mask(vbuf)
    vd = window_db(vbuf)
    vmed = float(np.median(vd[vd > -35]))
    sf.write(p("stem_key.wav"), duck_key(mus, mask, vmed), SR, subtype="FLOAT")
    ffmpeg_sidechain(p("stem_voice.wav"), p("stem_music_raw.wav"), p("stem_sfx.wav"), p("stem_key.wav"), total,
                     p("mix_raw.wav"), p("stem_music_ducked.wav"))
    mix, _ = sf.read(p("mix_raw.wav"), dtype="float32")
    duck, _ = sf.read(p("stem_music_ducked.wav"), dtype="float32")
    final, lufs_in = finish_loudness(mix[: int(total * SR)])
    sf.write(p("mix.wav"), final, SR, subtype="FLOAT")
    nm, _ = finish_loudness((vbuf + fx)[: int(total * SR)])
    sf.write(p("mix_nomusic.wav"), nm, SR, subtype="FLOAT")
    rep = dict(total=round(total, 2), marks={k: round(v, 2) for k, v in marks.items()},
               sidechain=dict(key="narration presence, 0.65 s hold", threshold_db=SC_T_DB, ratio=SC_RATIO, attack_ms=15,
                              release_ms=500, under_voice_db=UNDER_VOICE_DB),
               ratio=ratio_report(vbuf, duck, mask, marks), loud_mix=ebur128(p("mix.wav")), loud_nomusic=ebur128(p("mix_nomusic.wav")))
    json.dump(dict(rep, lines=lines), open(p("mix_report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
