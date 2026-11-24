"""Background score per 配乐规范: MusicGen (facebook/musicgen-stereo-medium), generated layer by layer.

Category (规范 一): 商业/组织 -> low-key electronic pulse or minimal piano + light percussion,
forward motion but never hype.  Layers (规范 二): 铺底 / 推进 / 高潮, plus release and an ending that
resolves to a single instrument.  Each layer: 2 candidates, scored for "doesn't fight the voice",
the best one is extended by audio-prompted continuation so the next layer stays in key and tempo.

python music_gen.py candidates   # generate 2 candidates per layer (continuing from the previous choice)
python music_gen.py report       # print candidate scores
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf

WORK = os.environ.get("EP_WORK", "/tmp/claude-0/-home-user-cvxpy/23149d0a-3dd1-5cf6-8dec-2980a0f4c270/scratchpad/work")
MODEL = os.path.join(WORK, "models/musicgen-stereo-medium")
OUT = os.path.join(WORK, "musicgen")
os.makedirs(OUT, exist_ok=True)
SR = 32000

BASE = "no vocals, no singing"
LAYERS = [
    # name, prompt, candidate length (s), extend to (s)
    ("L1_base", "minimal ambient soft piano and warm analog synth pad, sparse, long sustained notes, calm, "
                "thoughtful, slow, D minor, no drums, " + BASE, 22, 66),
    ("L2_drive", "minimal modern electronic pulse with soft piano, light ticking percussion like a quiet machine, "
                 "steady, thoughtful, gently building tension, D minor, 90 bpm, " + BASE, 22, 66),
    ("L3_peak", "cinematic minimal electronic, driving low synth pulse, low strings swelling, soft piano motif, "
                "light percussion, tense and serious, climax, not aggressive, D minor, 90 bpm, " + BASE, 22, 44),
    ("L4_release", "warm intimate piano with soft strings pad, reflective, calm, slow, no drums, D minor, " + BASE, 22, 44),
    ("L5_end", "solo soft piano, slow, gentle, reflective ending, single notes ringing out, fading, " + BASE, 18, 28),
]

_m = {}


def model():
    if "m" not in _m:
        import torch
        torch.set_num_threads(4)
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
        _m["p"] = AutoProcessor.from_pretrained(MODEL)
        _m["m"] = MusicgenForConditionalGeneration.from_pretrained(MODEL, dtype=torch.bfloat16)
        # the EnCodec audio encoder stays in float32 so audio prompts (float32) can be encoded
        _m["m"].audio_encoder.to(torch.float32)
        _m["m"].eval()
    return _m["p"], _m["m"]


def generate(prompt, seconds, seed, prompt_audio=None, guidance=3.0):
    """Returns float32 array (2, n) at 32 kHz. prompt_audio: (2, n) to continue from (returned audio excludes it)."""
    import torch
    proc, m = model()
    torch.manual_seed(seed)
    if prompt_audio is None:
        inputs = proc(text=[prompt], padding=True, return_tensors="pt")
        new_tokens = int(seconds * 50)
    else:
        inputs = proc(audio=[prompt_audio], sampling_rate=SR, text=[prompt], padding=True, return_tensors="pt")
        new_tokens = int(seconds * 50)
    with torch.no_grad():
        out = m.generate(**inputs, do_sample=True, guidance_scale=guidance, max_new_tokens=new_tokens)
    a = out[0].float().cpu().numpy()  # (channels, samples)
    if prompt_audio is not None:
        a = a[:, prompt_audio.shape[1]:]
    return a.astype(np.float32)


# ------------------------------------------------------------------ scoring: "felt, not heard"
def score(a):
    import librosa
    mono = a.mean(axis=0)
    S = np.abs(librosa.stft(mono, n_fft=2048, hop_length=512)) ** 2
    f = librosa.fft_frequencies(sr=SR, n_fft=2048)
    tot = S.sum() + 1e-12
    presence = S[(f >= 1000) & (f <= 4000)].sum() / tot        # energy where the voice lives (lower = better)
    hop = SR // 2
    fr = mono[: len(mono) // hop * hop].reshape(-1, hop)
    st = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    st = st[1:-1] if len(st) > 3 else st
    steadiness = float(np.std(st))                              # dB spread of 0.5 s loudness (lower = steadier)
    jumps = float(np.max(np.diff(st))) if len(st) > 2 else 0.0  # biggest sudden rise between half-seconds
    onset = librosa.onset.onset_strength(y=mono, sr=SR)
    ac = librosa.autocorrelate(onset - onset.mean(), max_size=200)
    pulse = float(np.max(ac[10:]) / (ac[0] + 1e-9)) if ac[0] > 0 else 0.0
    return dict(presence=round(float(presence), 4), steadiness=round(steadiness, 2), jump=round(jumps, 2),
                pulse=round(pulse, 3), rms_db=round(float(20 * np.log10(np.sqrt(np.mean(mono ** 2)) + 1e-9)), 1))


def vocal_check(path):
    """Use the ASR model as a crude singing detector: confident words => reject."""
    sys.path.insert(0, os.path.join(WORK, "voice"))
    from asr import model as asr_model
    import librosa
    y, sr = sf.read(path, dtype="float32", always_2d=True)
    y = librosa.resample(y.mean(axis=1), orig_sr=sr, target_sr=16000)
    segs, info = asr_model().transcribe(y, vad_filter=True, beam_size=1)
    words = [s for s in segs if s.no_speech_prob < 0.5 and s.avg_logprob > -0.7 and len(s.text.strip()) > 3]
    return len(words) == 0, " | ".join(s.text for s in words)[:80]


def total_score(name, sc):
    # lower is better; drive/peak layers should still have a pulse
    s = sc["presence"] * 40 + sc["steadiness"] * 0.6 + max(0.0, sc["jump"] - 4) * 0.8
    if name in ("L2_drive", "L3_peak"):
        s -= sc["pulse"] * 3
    return round(s, 3)


def generate_batch(prompts, seconds, seed, prompt_audio=None, guidance=3.0):
    """Batched generation (decoding on CPU is memory-bound, so a batch costs little more than one).
    prompt_audio: list of (2, n) arrays of equal length, or None. Returns list of (2, m) arrays."""
    import torch
    proc, m = model()
    torch.manual_seed(seed)
    if prompt_audio is None:
        inputs = proc(text=prompts, padding=True, return_tensors="pt")
    else:
        inputs = proc(audio=list(prompt_audio), sampling_rate=SR, text=prompts, padding=True, return_tensors="pt")
    with torch.no_grad():
        out = m.generate(**inputs, do_sample=True, guidance_scale=guidance, max_new_tokens=int(seconds * 50))
    res = []
    for k in range(out.shape[0]):
        a = out[k].float().cpu().numpy()
        if prompt_audio is not None:
            a = a[:, prompt_audio[k].shape[1]:]
        res.append(a.astype(np.float32))
    return res


def _pick(name, cands):
    for c in cands:
        sc = score(c["audio"])
        ok_voc, voc = vocal_check(c["path"])
        sc["no_vocals"] = ok_voc
        sc["vocal_text"] = voc
        sc["total"] = total_score(name, sc) + (0 if ok_voc else 100)
        c["score"] = sc
        print(f"  {name} {os.path.basename(c['path'])}: {sc}", flush=True)
    return min(cands, key=lambda c: c["score"]["total"])


def _load_rep():
    rep_path = os.path.join(OUT, "report.json")
    return (json.load(open(rep_path)) if os.path.exists(rep_path) else {}), rep_path


def stage_a(n_cand=2, seg=22):
    """Base layer from text alone (small batch: safe to run next to the TTS job)."""
    rep, rep_path = _load_rep()
    prompts = {l[0]: l[1] for l in LAYERS}
    t0 = time.time()
    outs = generate_batch([prompts["L1_base"]] * n_cand, seg, 101)
    cands = []
    for k, a in enumerate(outs):
        p = os.path.join(OUT, f"L1_base_c{k}.wav"); sf.write(p, a.T, SR)
        cands.append(dict(path=p, audio=a))
    print(f"stage A {time.time() - t0:.0f}s", flush=True)
    best = _pick("L1_base", cands)
    rep["L1_base"] = dict(prompt=prompts["L1_base"], candidates=[dict(path=c["path"], score=c["score"]) for c in cands],
                          chosen=best["path"])
    json.dump(rep, open(rep_path, "w"), ensure_ascii=False, indent=1)


def stage_b(n_cand=2, seg=22, batch=4):
    """Other layers continue from the chosen base (keeps key and tempo related)."""
    rep, rep_path = _load_rep()
    names = [l[0] for l in LAYERS]
    prompts = {l[0]: l[1] for l in LAYERS}
    base = sf.read(rep["L1_base"]["chosen"], dtype="float32")[0].T
    tail = base[:, -8 * SR:]
    jobs = [(n, k) for n in names[1:] for k in range(n_cand)]
    outs = []
    for j in range(0, len(jobs), batch):
        part = jobs[j:j + batch]
        t0 = time.time()
        outs += generate_batch([prompts[n] for n, _ in part], seg, 202 + j, prompt_audio=[tail] * len(part))
        print(f"stage B batch {j // batch}: {time.time() - t0:.0f}s", flush=True)
    for n in names[1:]:
        cands = []
        for (nn, k), a in zip(jobs, outs):
            if nn != n:
                continue
            p = os.path.join(OUT, f"{n}_c{k}.wav"); sf.write(p, a.T, SR)
            cands.append(dict(path=p, audio=a))
        best = _pick(n, cands)
        rep[n] = dict(prompt=prompts[n], candidates=[dict(path=c["path"], score=c["score"]) for c in cands], chosen=best["path"])
        json.dump(rep, open(rep_path, "w"), ensure_ascii=False, indent=1)


def stage_ext(seg=22):
    """Extend every chosen layer by continuation until it reaches its target length."""
    rep, rep_path = _load_rep()
    names = [l[0] for l in LAYERS]
    prompts = {l[0]: l[1] for l in LAYERS}
    target = {l[0]: l[3] for l in LAYERS}
    chosen = {n: sf.read(rep[n]["chosen"], dtype="float32")[0].T for n in names}
    rnd = 0
    while True:
        need = [n for n in names if chosen[n].shape[1] < target[n] * SR]
        if not need:
            break
        t0 = time.time()
        outs = generate_batch([prompts[n] for n in need], seg, 303 + rnd, prompt_audio=[chosen[n][:, -8 * SR:] for n in need])
        for n, a in zip(need, outs):
            chosen[n] = np.concatenate([chosen[n], a], axis=1)
        rnd += 1
        print(f"extend round {rnd}: {need} {time.time() - t0:.0f}s", flush=True)
    for n in names:
        full = os.path.join(OUT, f"{n}_full.wav")
        sf.write(full, chosen[n].T, SR)
        rep[n]["chosen_full"] = full
        rep[n]["seconds"] = round(chosen[n].shape[1] / SR, 1)
    json.dump(rep, open(rep_path, "w"), ensure_ascii=False, indent=1)
    print("done", {n: rep[n]["seconds"] for n in names}, flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "a"
    if cmd == "a":
        stage_a()
    elif cmd == "b":
        stage_b()
    elif cmd == "ext":
        stage_ext()
    elif cmd == "speedtest":
        t0 = time.time()
        a = generate(LAYERS[0][1], 5, 1)
        print("5s audio in", round(time.time() - t0, 1), "s; shape", a.shape)
        sf.write(os.path.join(OUT, "speedtest.wav"), a.T, SR)
    elif cmd == "report":
        print(json.dumps(json.load(open(os.path.join(OUT, "report.json"))), ensure_ascii=False, indent=1))
