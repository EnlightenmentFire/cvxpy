# -*- coding: utf-8 -*-
"""Build the score per 配乐规范:
  三层: L1 铺底(pad) -> L2 推进(gentle pulse) -> [COLD: Disney freeze] -> L2 (Apple) -> L3 高潮 -> OUT (solo piano)
  每段由选中的 20 s 候选 + MusicGen 续写(audio prompt)延长，段间 3 s 交叉淡化，不循环。
usage:
  python build_music.py plan                      -> sections.json
  python build_music.py extend <model> <choice.json>   -> stems/<section>.wav (32 kHz stereo)
  python build_music.py arrange <out.wav>         -> 48 kHz stereo music bed
"""
import os, sys, json, time
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
XF = 3.0          # crossfade between sections (spec: 2–4 s)

def seg_times():
    tl = json.load(open(os.path.join(ROOT, "timeline.json")))
    S = {s["id"]: s for s in tl["segments"]}
    def cue(sid, name):
        s = S[sid]
        for ln in s["lines"]:
            if ln.get("cue") == name:
                return ln["t0"]
        raise KeyError(name)
    return tl, S, cue

def plan():
    tl, S, cue = seg_times()
    segs = tl["segments"]
    def gap_mid(a, b):
        return (S[a]["t1"] + S[b]["t0"]) / 2
    t_push = cue("routine", "extinguish")
    never = [ln for ln in S["apple"]["lines"] if ln.get("cue") == "never_ask"][0]
    t_climb = cue("apple", "cook")
    t_out = S["end"]["lines"][-1]["t0"]
    total = tl["total"]
    B = [  # name, layer, t0, t1, gain_db, starts_with_candidate
        ("L1a", "L1", 0.0, gap_mid("title", "weber"), -6.5, True),
        ("L1b", "L1", gap_mid("title", "weber"), gap_mid("weber", "routine"), -5.5, False),
        ("L1c", "L1", gap_mid("weber", "routine"), t_push, -5.0, False),
        ("L2a", "L2", t_push, gap_mid("lot", "designate"), -4.0, True),
        ("L2b", "L2", gap_mid("lot", "designate"), gap_mid("designate", "elect"), -3.5, False),
        ("L2c", "L2", gap_mid("designate", "elect"), gap_mid("elect", "blood"), -3.5, False),
        ("L2d", "L2", gap_mid("elect", "blood"), gap_mid("blood", "ottoman"), -3.0, False),
        ("L2e", "L2", gap_mid("blood", "ottoman"), gap_mid("ottoman", "office"), -3.0, False),
        ("L2f", "L2", gap_mid("ottoman", "office"), gap_mid("donatist", "disney"), -3.5, False),
        ("COLD", "COLD", gap_mid("donatist", "disney"), gap_mid("disney", "apple"), -7.0, False),
        ("L2g", "L2", gap_mid("disney", "apple"), t_climb, -4.0, False),
        ("L3", "L3", t_climb, t_out, 0.0, True),
        ("OUT", "OUT", t_out, total, -3.0, False),
    ]
    sections = []
    for name, layer, t0, t1, g, cand in B:
        sections.append(dict(name=name, layer=layer, t0=round(t0, 3), t1=round(t1, 3), gain_db=g, cand=cand,
                             need=round(t1 - t0 + XF + 1.0, 2)))
    json.dump(dict(sections=sections, peak=never["t1"], total=total), open(os.path.join(HERE, "sections.json"), "w"), indent=1)
    for s in sections:
        print(s["name"], round(s["t0"], 1), "->", round(s["t1"], 1), "need", s["need"])
    print("peak pause at", round(never["t1"], 1), "total", total, "new audio needed ~",
          round(sum(s["need"] for s in sections) - 60, 0), "s")

def xfade_concat(a, b, n):
    """a,b: (2,N) arrays; equal-power crossfade of n samples"""
    if n <= 0 or a.shape[1] < n:
        return np.concatenate([a, b], 1)
    t = np.linspace(0, 1, n)
    fo, fi = np.cos(t * np.pi / 2), np.sin(t * np.pi / 2)
    mid = a[:, -n:] * fo + b[:, :n] * fi
    return np.concatenate([a[:, :-n], mid, b[:, n:]], 1)

def extend(model_path, choice_path, group=5):
    from mg import MG, PROMPTS, SR_MG, gen_batch
    plan_ = json.load(open(os.path.join(HERE, "sections.json")))
    choice = json.load(open(choice_path))
    os.makedirs(os.path.join(HERE, "stems"), exist_ok=True)
    mg = MG(model_path, int(os.environ.get("MG_THREADS", "4")))
    PROMPT_S, NEW_S = 6.0, 24.0
    def load32(p):
        a, _ = sf.read(os.path.join(HERE, p), dtype="float32"); return a.T
    seed_audio = {k: load32(v) for k, v in choice.items()}
    seed_audio["COLD"] = seed_audio["L1"]       # cold pad grows out of the pad layer
    seed_audio["OUT"] = seed_audio["L3"]        # solo piano grows out of the climax
    chains = {}
    for s in plan_["sections"]:
        out = os.path.join(HERE, "stems", s["name"] + ".wav")
        if os.path.exists(out):
            continue
        part = os.path.join(HERE, "stems", "partial", s["name"] + ".wav")
        if os.path.exists(part):
            chains[s["name"]] = dict(s=s, audio=load32(os.path.relpath(part, HERE)),
                                     prompt=seed_audio[s["layer"]][:, -int(PROMPT_S * SR_MG):])
        elif s["cand"]:
            chains[s["name"]] = dict(s=s, audio=seed_audio[s["layer"]].copy(), prompt=None)
        else:
            chains[s["name"]] = dict(s=s, audio=np.zeros((2, 0), np.float32),
                                     prompt=seed_audio[s["layer"]][:, -int(PROMPT_S * SR_MG):])
    rnd = 0
    while True:
        todo = [k for k, c in chains.items() if c["audio"].shape[1] / SR_MG < c["s"]["need"]]
        if not todo:
            break
        # longest remaining first, in groups
        todo.sort(key=lambda k: -(chains[k]["s"]["need"] - chains[k]["audio"].shape[1] / SR_MG))
        grp = todo[:group]
        prompts, aps = [], []
        for k in grp:
            c = chains[k]
            aps.append(c["audio"][:, -int(PROMPT_S * SR_MG):] if c["audio"].shape[1] >= PROMPT_S * SR_MG else c["prompt"])
            prompts.append(PROMPTS[c["s"]["layer"]])
        remain = max(chains[k]["s"]["need"] - chains[k]["audio"].shape[1] / SR_MG for k in grp)
        secs = min(NEW_S, max(8.0, remain + 1.0))
        t = time.time()
        outs = gen_batch(mg, prompts, aps, secs, 1000 + rnd, guidance=float(os.environ.get("MG_GUIDANCE", "3.0")))
        for k, new in zip(grp, outs):
            c = chains[k]
            c["audio"] = xfade_concat(c["audio"], new, int(0.05 * SR_MG)) if c["audio"].shape[1] else new
            if c["audio"].shape[1] / SR_MG >= c["s"]["need"]:
                sf.write(os.path.join(HERE, "stems", k + ".wav"), c["audio"].T, SR_MG)
            else:
                os.makedirs(os.path.join(HERE, "stems", "partial"), exist_ok=True)
                sf.write(os.path.join(HERE, "stems", "partial", k + ".wav"), c["audio"].T, SR_MG)
        rnd += 1
        print(f"round {rnd}: {grp} +{secs:.0f}s in {time.time()-t:.0f}s; " +
              ", ".join(f"{k}={chains[k]['audio'].shape[1]/SR_MG:.0f}/{chains[k]['s']['need']:.0f}" for k in grp), flush=True)

def arrange(out_path):
    import subprocess
    plan_ = json.load(open(os.path.join(HERE, "sections.json")))
    SR = 48000
    total = plan_["total"]
    N = int(total * SR) + SR
    bus = np.zeros((2, N), np.float32)
    for s in plan_["sections"]:
        src = os.path.join(HERE, "stems", s["name"] + ".wav")
        tmp = src.replace(".wav", "_48k.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", str(SR), tmp], check=True)
        a, _ = sf.read(tmp, dtype="float32"); a = a.T
        # loudness-match stems (RMS) before applying the section gain
        rms = np.sqrt(np.mean(a ** 2)) + 1e-9
        a = a / rms * 10 ** (-20 / 20) * 10 ** (s["gain_db"] / 20)
        h = XF / 2
        start = max(0.0, s["t0"] - h) if s["t0"] > 0 else 0.0
        stop = s["t1"] + h if s["t1"] < total - 0.5 else total
        i0 = int(start * SR)
        L = min(a.shape[1], int((stop - start) * SR), N - i0)
        seg = a[:, :L].copy()
        nx = int(XF * SR)
        if s["t0"] > 0:                       # equal-power fade in, centred on the boundary
            t = np.linspace(0, 1, nx); seg[:, :nx] *= np.sin(t * np.pi / 2)
        if s["t1"] < total - 0.5 and L >= nx:  # equal-power fade out into the next section
            t = np.linspace(0, 1, nx); seg[:, L - nx:L] *= np.cos(t * np.pi / 2)
        bus[:, i0:i0 + L] += seg
    # spec: fade in 2 s at the head, fade out 3 s at the tail
    n2, n3 = int(2 * SR), int(3 * SR)
    bus[:, :n2] *= np.linspace(0, 1, n2)
    end = int(total * SR)
    bus[:, end - n3:end] *= np.linspace(1, 0, n3)
    bus[:, end:] = 0
    sf.write(out_path, bus.T, SR)
    print("music bed", out_path, round(total, 1), "s")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plan":
        plan()
    elif cmd == "extend":
        extend(sys.argv[2], sys.argv[3])
    elif cmd == "arrange":
        arrange(sys.argv[2])
