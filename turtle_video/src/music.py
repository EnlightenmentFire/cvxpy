"""Background music per the house 配乐规范:
  - mood for 商业/交易: low-key electronic pulse / minimal piano + light percussion
  - three layers (bed -> build -> climax), resolve to a single instrument at the end
  - generated locally with MusicGen (facebook/musicgen-stereo-medium), 2-4 takes per layer,
    takes scored objectively (vocals, presence-band energy, stability, dropouts, key, tempo)

usage:
  python music.py gen  OUTDIR [layer ...]     # generate takes (resumable)
  python music.py score OUTDIR                # analyse takes -> OUTDIR/scores.json
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf

MODEL = "/opt/models/facebook_musicgen-stereo-medium"
SR_GEN = 32000

# prompts follow the spec's 商业类 example, adapted per layer; all in A minor so takes can be crossfaded
LAYERS = {
    "bed": dict(secs=22, takes=2, prompt="minimal ambient electronic pad, soft sustained analog synth chords, low warm drone, "
                                          "calm, thoughtful, no drums, no melody, A minor, 80 bpm, no vocals"),
    "build": dict(secs=22, takes=2, prompt="minimal modern electronic pulse with soft piano, steady low synth bass pulse, "
                                            "light percussion, thoughtful, slightly tense, A minor, 90 bpm, no vocals"),
    "climax": dict(secs=22, takes=2, prompt="cinematic modern electronic, full arrangement, deep pulsing synth bass, steady drums, "
                                             "soft piano, warm strings, emotional, solemn, rising, A minor, 90 bpm, no vocals"),
    "drop": dict(secs=22, takes=1, prompt="low frequency synth drone, sparse soft heartbeat-like low drum, tense, dark, minimal, "
                                           "slow, no melody, A minor, no vocals"),
    "reflect": dict(secs=22, takes=1, prompt="minimal solo piano, sparse gentle notes, reflective, melancholic, slow, soft reverb, "
                                              "A minor, no drums, no vocals"),
    "end": dict(secs=22, takes=1, prompt="solo piano, a few slow gentle single notes, resolving, fading out, long reverb tail, "
                                          "A minor, no drums, no vocals"),
}


def gen(outdir, layers, batch=2, dtype="float32"):
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    torch.set_num_threads(4)
    os.makedirs(outdir, exist_ok=True)
    proc = AutoProcessor.from_pretrained(MODEL)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL, torch_dtype=getattr(torch, dtype))
    model.eval()
    jobs = [(name, k) for name in layers for k in range(LAYERS[name]["takes"])
            if not os.path.exists(os.path.join(outdir, f"{name}_{k}.wav"))]
    print(f"{len(jobs)} takes to generate", flush=True)
    for i in range(0, len(jobs), batch):
        grp = jobs[i:i + batch]
        secs = max(LAYERS[n]["secs"] for n, _ in grp)
        torch.manual_seed(1983 + 31 * i)
        inputs = proc(text=[LAYERS[n]["prompt"] for n, _ in grp], padding=True, return_tensors="pt")
        t0 = time.time()
        with torch.inference_mode():
            audio = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=int(secs * 50) + 4)
        audio = audio.float().cpu().numpy()
        for (n, k), a_ in zip(grp, audio):
            a_ = a_[:, : int(LAYERS[n]["secs"] * SR_GEN)]
            sf.write(os.path.join(outdir, f"{n}_{k}.wav"), a_.T, SR_GEN, subtype="FLOAT")
        print(f"{[f'{n}_{k}' for n, k in grp]}: {secs}s in {time.time() - t0:.0f}s", flush=True)


# ------------------------------------------------------------------ analysis
KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def estimate_key(y, sr):
    import librosa
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    best = None
    for tonic in range(12):
        for mode, prof in (("major", KS_MAJ), ("minor", KS_MIN)):
            r = np.corrcoef(chroma, np.roll(prof, tonic))[0, 1]
            if best is None or r > best[0]:
                best = (r, tonic, mode)
    r, tonic, mode = best
    # semitone shift that brings the key to A minor (or its relative C major), smallest magnitude
    target = 9 if mode == "minor" else 0
    shift = (target - tonic + 6) % 12 - 6
    return f"{NOTES[tonic]} {mode}", int(shift), float(r)


def analyse(path):
    import librosa
    from scipy.signal import butter, sosfilt
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = x.mean(1)
    # presence band (1-4 kHz) share of energy: lower = less competition with the voice
    sos = butter(4, [1000, 4000], btype="bandpass", fs=sr, output="sos")
    pres = float(np.sum(sosfilt(sos, mono) ** 2) / (np.sum(mono ** 2) + 1e-12))
    hop = int(0.4 * sr)
    n = len(mono) // hop
    r = np.sqrt((mono[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r)
    body = db[3:-2] if n > 8 else db
    stab = float(np.std(body))
    pop = float(np.max(body) - np.median(body))
    dropout = float(np.mean(body < np.median(body) - 18))
    # real clipping = flat-topped plateaus (takes are float, so peaks above 1.0 are just loud, not clipped)
    a_ = np.abs(x)
    pk = a_.max()
    flat = sum(int(np.sum((np.abs(np.diff(x[:, ch])) < 1e-7) & (a_[1:, ch] > 0.95 * pk))) for ch in range(x.shape[1]))
    clip = flat / x.size
    key, shift, key_conf = estimate_key(mono, sr)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=mono, sr=sr)[0])[0])
    return dict(presence=round(pres, 4), stability_db=round(stab, 2), pop_db=round(pop, 2), dropout=round(dropout, 3),
                clip=round(clip, 5), key=key, shift=shift, key_conf=round(key_conf, 2), tempo=round(tempo, 1),
                rms_db=round(float(20 * np.log10(np.sqrt((mono ** 2).mean()) + 1e-12)), 1))


def vocal_check(path):
    """Run ASR over the take: recognisable words suggest a sung/spoken vocal."""
    sys.path.insert(0, os.environ.get("VOICE_DIR", "/tmp/claude-0/-home-user-cvxpy/78685b54-039d-5b0e-946b-2cbac616b0ef/scratchpad/voice"))
    from asr import model as asr_model, load16k
    segs, info = asr_model().transcribe(load16k(path), beam_size=5, vad_filter=True)
    words = []
    for s in segs:
        if s.no_speech_prob < 0.5 and s.avg_logprob > -0.9:
            words.append(s.text.strip())
    return " ".join(w for w in words if w)


def score(outdir):
    res = {}
    for f in sorted(os.listdir(outdir)):
        if not f.endswith(".wav") or "_" not in f:
            continue
        layer = f.rsplit("_", 1)[0]
        if layer not in LAYERS:
            continue
        a = analyse(os.path.join(outdir, f))
        a["vocals"] = vocal_check(os.path.join(outdir, f))
        # lower is better
        if layer == "climax":   # wants a clear swell, still not too bright in the voice band
            s = 25 * a["presence"] - 0.3 * a["pop_db"] + 30 * a["dropout"] + 2000 * a["clip"]
        else:                   # beds and builds: steady, unobtrusive
            s = 40 * a["presence"] + 0.6 * a["stability_db"] + 0.25 * a["pop_db"] + 30 * a["dropout"] + 2000 * a["clip"]
        a["shift"] = compat_shift(a["key"])
        s += 0.4 * abs(a["shift"])
        if a["vocals"]:
            s += 50
        if layer in ("build", "climax"):
            t = a["tempo"]
            s += 0.02 * min(abs(t - 90), abs(t / 2 - 90), abs(t * 2 - 90))
        a["score"] = round(s, 2)
        res[f[:-4]] = a
        print(f[:-4], a, flush=True)
    json.dump(res, open(os.path.join(outdir, "scores.json"), "w"), ensure_ascii=False, indent=1)


def compat_shift(key):
    """Smallest pitch shift into a key that blends with A minor / C major: keys one step away on the
    circle of fifths (G, F major; E, D minor) are left alone, everything else moves at most 2 semitones."""
    name, mode = key.split()
    tonic = NOTES.index(name)
    targets = (0, 7, 5) if mode == "major" else (9, 4, 2)
    best = min(((t - tonic + 6) % 12 - 6 for t in targets), key=abs)
    return int(best)


KEEP = {"bed": 2, "build": 2, "climax": 1, "drop": 1, "reflect": 1, "end": 1}


def choose(outdir):
    """Pick the best takes per layer, key-align to A minor, tempo-match rhythmic layers -> choice.json."""
    import subprocess
    sc = json.load(open(os.path.join(outdir, "scores.json")))
    choice = {}
    for layer in LAYERS:
        ranked = sorted([k for k in sc if k.rsplit("_", 1)[0] == layer], key=lambda k: sc[k]["score"])
        ranked = [k for k in ranked if not sc[k]["vocals"]] or ranked
        keep = ranked[: KEEP[layer]]
        ref_tempo = sc[keep[0]]["tempo"] if keep else None
        names = []
        for k in keep:
            shift = compat_shift(sc[k]["key"])
            tempo_ratio = 1.0
            if layer in ("build", "climax") and ref_tempo and sc[k]["tempo"] > 0:
                r = ref_tempo / sc[k]["tempo"]
                for cand in (r, r * 2, r / 2):
                    if 0.94 <= cand <= 1.06:
                        tempo_ratio = cand
                        break
            src = os.path.join(outdir, k + ".wav")
            if shift == 0 and abs(tempo_ratio - 1) < 0.01:
                names.append(k)
                continue
            dst = os.path.join(outdir, f"{k}_al.wav")
            cmd = ["rubberband", "-q", "-3", f"-p{shift}", f"-T{tempo_ratio:.4f}", src, dst]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            names.append(f"{k}_al")
        choice[layer] = names
        print(layer, "->", names, [(k, sc[k]["score"], sc[k]["key"], sc[k]["tempo"]) for k in keep])
    json.dump(choice, open(os.path.join(outdir, "choice.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd, outdir = sys.argv[1], sys.argv[2]
    if cmd == "gen":
        gen(outdir, sys.argv[3:] or ["climax", "end", "build", "bed", "reflect", "drop"],
            batch=int(os.environ.get("MG_BATCH", "2")), dtype=os.environ.get("MG_DTYPE", "float32"))
    elif cmd == "score":
        score(outdir)
    elif cmd == "choose":
        choose(outdir)
