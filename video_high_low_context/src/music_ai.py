# -*- coding: utf-8 -*-
"""Background music per 配乐规范.md:
  - source: local MusicGen (facebook/musicgen-stereo-medium), 20-30 s clips per layer,
    2-4 versions each, scored and picked automatically, then cross-faded together;
  - 题材情绪: 思想类 (warm piano + strings pad) for the bed, 商业/职场类 (minimal pulse +
    soft piano) for the drive, 悬疑类 (low drone + sparse heartbeat drum) for 1945;
  - 三层起伏: 铺底 -> 推进 -> 高潮 (+ a short swell at the 反转 moment), ending on solo piano.

usage:
  python music_ai.py gen  out_dir            # generate candidate clips (slow, CPU)
  python music_ai.py score out_dir           # score candidates -> out_dir/scores.json
  python music_ai.py build out_dir durations.json music.wav
"""
import json
import math
import os
import sys
import time

import numpy as np
import soundfile as sf

SR_OUT = 48000
S = "/tmp/claude-0/-home-user-cvxpy/3146234e-c880-5dd6-b7f5-20b7a9aa7973/scratchpad"

LAYERS = {
    # 铺底 —— 思想类：钢琴 + 柔和弦乐 pad，温暖安静
    "bed": dict(n=3, sec=30, prompt="warm intimate piano with soft strings pad, reflective, calm, slow, sparse, "
                                    "gentle long notes, no drums, no vocals"),
    # 推进 —— 商业/职场类：极简电子脉冲 + 柔和钢琴 + 轻打击，有推进感但不打鸡血
    "drive": dict(n=3, sec=30, prompt="minimal modern electronic pulse with soft piano and light percussion, "
                                      "steady, thoughtful, understated, 90 bpm, no vocals"),
    # 1945 —— 悬疑类：低频 drone + 稀疏心跳式低鼓
    "tension": dict(n=2, sec=30, prompt="dark low frequency drone with sparse heartbeat-like low drum, tense, "
                                        "slow, cinematic, D minor, no melody, no vocals"),
    # 高潮 —— 全编制但克制温暖（本片题材不是战争，不用悲壮大鼓）
    "climax": dict(n=2, sec=22, prompt="cinematic emotional swell, full warm strings and piano, hopeful, "
                                       "reflective, slow build, 80 bpm, no vocals"),
    # 尾声 —— 收成单个乐器
    "outro": dict(n=2, sec=15, prompt="solo piano, gentle, reflective, slow, soft final chord with long "
                                      "sustain, no vocals"),
}


# ------------------------------------------------------------------ generation
def gen(out):
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    torch.set_num_threads(int(os.environ.get("MG_THREADS", "4")))
    os.makedirs(out, exist_ok=True)
    mdir = f"{S}/models/musicgen-stereo-medium"
    proc = AutoProcessor.from_pretrained(mdir)
    model = MusicgenForConditionalGeneration.from_pretrained(mdir, torch_dtype=torch.float32)
    model.eval()
    sr = model.config.audio_encoder.sampling_rate
    fps = model.config.audio_encoder.frame_rate
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    for name, L in LAYERS.items():
        if only and name not in only:
            continue
        for v in range(L["n"]):
            path = os.path.join(out, f"{name}_v{v}.wav")
            if os.path.exists(path):
                continue
            torch.manual_seed(1000 + 17 * v + len(name))
            inp = proc(text=[L["prompt"]], padding=True, return_tensors="pt")
            t0 = time.time()
            with torch.no_grad():
                audio = model.generate(**inp, do_sample=True, guidance_scale=3.0,
                                       max_new_tokens=int(L["sec"] * fps) + 4)
            a = audio[0].cpu().numpy().T  # (samples, channels)
            sf.write(path, a, sr)
            print(f"{name} v{v}: {a.shape[0] / sr:.1f}s audio in {time.time() - t0:.0f}s", flush=True)


# ------------------------------------------------------------------ scoring
def band_ratio(a, sr, lo=1000, hi=4000):
    x = a.mean(1) if a.ndim > 1 else a
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    tot = spec[(f > 40) & (f < 12000)].sum() + 1e-12
    return float(spec[(f >= lo) & (f <= hi)].sum() / tot)


def short_loud(a, sr, win=1.0):
    x = a.mean(1) if a.ndim > 1 else a
    n = int(win * sr)
    m = len(x) // n
    r = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r)


def score(out):
    from faster_whisper import WhisperModel
    import librosa
    wm = WhisperModel(f"{S}/models/faster-whisper-medium", device="cpu", compute_type="int8", cpu_threads=4)
    res = {}
    for f in sorted(os.listdir(out)):
        if not f.endswith(".wav"):
            continue
        a, sr = sf.read(os.path.join(out, f), dtype="float32")
        body = a[int(0.5 * sr): len(a) - int(1.0 * sr)]
        ld = short_loud(body, sr)
        voc = band_ratio(body, sr)
        jumps = float(np.max(np.abs(np.diff(ld)))) if len(ld) > 1 else 0.0
        silent = float((ld < ld.max() - 35).mean())
        # vocal check: does Whisper hear words with confidence?
        a16 = librosa.resample(body.mean(1), orig_sr=sr, target_sr=16000)
        segs, info = wm.transcribe(a16, beam_size=1, vad_filter=True)
        words = "".join(s.text for s in segs if s.no_speech_prob < 0.5).strip()
        badness = voc * 10 + jumps * 0.15 + float(np.std(ld)) * 0.1 + silent * 5 + (5 if len(words) > 6 else 0)
        res[f] = dict(voice_band=round(voc, 3), loud_std=round(float(np.std(ld)), 2), max_jump=round(jumps, 2),
                      silent=round(silent, 2), heard=words[:60], badness=round(badness, 3),
                      dur=round(len(a) / sr, 1))
        print(f, res[f], flush=True)
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1, ensure_ascii=False)


# ------------------------------------------------------------------ assembly
def load48(path):
    from scipy.signal import resample_poly
    a, sr = sf.read(path, dtype="float32")
    if a.ndim == 1:
        a = np.stack([a, a], 1)
    if sr != SR_OUT:
        g = math.gcd(sr, SR_OUT)
        a = resample_poly(a, SR_OUT // g, sr // g, axis=0).astype(np.float32)
    return a


def lufs_gain(a, target):
    """Approximate gain to bring a clip to `target` (K-weighting skipped; RMS of active parts)."""
    ld = short_loud(a, SR_OUT, 0.4)
    act = ld[ld > ld.max() - 25]
    cur = 10 * np.log10(np.mean(10 ** (act / 10)) + 1e-12)
    return 10 ** ((target - cur) / 20)


def xfade_concat(clips, xf):
    """Equal-power cross-fade concatenation."""
    n = int(xf * SR_OUT)
    out = clips[0].copy()
    for c in clips[1:]:
        k = min(n, len(out), len(c))
        t = np.linspace(0, 1, k)[:, None]
        mix = out[-k:] * np.cos(t * np.pi / 2) + c[:k] * np.sin(t * np.pi / 2)
        out = np.concatenate([out[:-k], mix, c[k:]])
    return out


def section(clips, dur, xf=3.0):
    """Fill `dur` seconds by cycling through clips (trimmed), cross-faded; varied entry points."""
    parts, total, i = [], 0.0, 0
    while total < dur + xf:
        c = clips[i % len(clips)]
        # skip MusicGen's first 0.3 s and the last 0.8 s (endings can be abrupt)
        off = int((0.3 + (i // len(clips)) * 2.5) * SR_OUT) % max(1, len(c) // 3)
        seg = c[off: len(c) - int(0.8 * SR_OUT)]
        parts.append(seg)
        total += len(seg) / SR_OUT - (xf if parts[:-1] else 0)
        i += 1
    out = xfade_concat(parts, xf)
    return out[: int((dur + xf) * SR_OUT)]


LEVEL = {"bed": -31.0, "drive": -29.0, "tension": -29.5, "climax": -25.0, "outro": -29.0}


def build(out, dur_path, music_path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    tl, _ = render.make(dur_path)
    scores = json.load(open(os.path.join(out, "scores.json")))
    pick = {}
    for name in LAYERS:
        cands = sorted([(v["badness"], f) for f, v in scores.items() if f.startswith(name + "_")])
        keep = [f for b, f in cands if not scores[f]["heard"] or len(scores[f]["heard"]) <= 6][:2]
        pick[name] = keep or [cands[0][1]]
    print("picked", pick)
    clips = {k: [load48(os.path.join(out, f)) for f in v] for k, v in pick.items()}
    for k in clips:
        clips[k] = [c * lufs_gain(c, LEVEL[k]) for c in clips[k]]
    seg = {s["id"]: s for s in tl["segs"]}
    total = tl["total"]
    T = lambda sid: seg[sid]["t0"]
    # cue sheet: (start, end, layer)
    rev = seg["s06"]["trig"].get("reversal_swell", T("s06") + 1.3)
    cp = seg["s11"]["trig"].get("climax_pause", seg["s11"]["t1"] - 8)
    ec = seg["s11"]["trig"].get("endcard", total - 6)
    cues = [
        (0.0, T("s04"), "bed"),                # 铺底：开场 → 背景交代（冷启动、反过来、起名字）
        (T("s04"), T("s06"), "drive"),         # 推进：尺子、小词典
        (T("s06") - 0.5, rev + 7.0, "climax"),  # 反转：短促上全编制，旁白停约 2 秒
        (rev + 7.0, T("s08"), "drive"),        # 推进：反转后半、中文那一边
        (T("s08"), T("s10"), "tension"),       # 1945：低频 drone + 心跳鼓
        (T("s10"), T("s11"), "drive"),         # 推进：为什么是美国
        (T("s11") - 1.0, ec + 0.5, "climax"),  # 高潮：收尾三句（含 1.8 秒留白）
        (ec, total, "outro"),                  # 尾声：独奏钢琴余音
    ]
    xf = 3.0
    n = int((total + 1) * SR_OUT)
    mus = np.zeros((n, 2), np.float32)
    for (a, b, layer) in cues:
        d = b - a
        sig = section(clips[layer], d, xf)
        i0 = int(max(0.0, a - xf / 2) * SR_OUT)
        k = int(xf * SR_OUT)
        env = np.ones(len(sig), np.float32)
        ramp = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
        env[:k] = ramp
        env[-k:] = np.minimum(env[-k:], ramp[::-1])
        if layer == "outro":
            env[-k:] = 1.0
        j = min(n, i0 + len(sig))
        mus[i0:j] += sig[: j - i0] * env[: j - i0, None]
    # 开头淡入 2 秒，结尾淡出 3 秒
    fi, fo = int(2 * SR_OUT), int(3 * SR_OUT)
    mus[:fi] *= np.linspace(0, 1, fi)[:, None]
    e = int(total * SR_OUT)
    mus[e - fo:e] *= np.linspace(1, 0, fo)[:, None]
    mus[e:] = 0
    sf.write(music_path, mus[:e], SR_OUT, subtype="FLOAT")
    json.dump(dict(pick=pick, cues=cues), open(os.path.join(out, "cues.json"), "w"), indent=1, ensure_ascii=False)
    print("music", music_path, round(e / SR_OUT, 1), "s")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        gen(sys.argv[2])
    elif cmd == "score":
        score(sys.argv[2])
    elif cmd == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4])
