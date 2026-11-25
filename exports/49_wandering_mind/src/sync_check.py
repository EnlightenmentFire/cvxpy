# -*- coding: utf-8 -*-
"""A/V + subtitle sync spot-check on the encoded film: start, middle, end windows.
For every narration line starting inside a window, compare the ASR onset of speech with the line's
timeline start (which also drives the subtitle cue), and save a frame grab at that moment.
usage: python sync_check.py film.mp4 outdir
"""
import os, sys, json, subprocess
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def main():
    film, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    tl = json.load(open(f"{WORK}/timeline.json"))
    T = tl["total"]
    wins = [("开头", 0.0, 40.0), ("中段", T / 2 - 20, T / 2 + 20), ("结尾", T - 45, T)]
    wav = f"{WORK}/film16k.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", film, "-ac", "1", "-ar", "16000", wav], check=True)
    x, sr = sf.read(wav, dtype="float32")
    m = WhisperModel("medium", device="cpu", compute_type="int8", download_root=f"{WORK}/models/whisper")
    rep = []
    for name, a, b in wins:
        seg = x[int(a * sr):int(b * sr)]
        segs, _ = m.transcribe(seg, language="zh", word_timestamps=True, vad_filter=False,
                               initial_prompt="以下是普通话的句子，使用简体中文。")
        words = [(w.start + a, w.end + a, w.word) for s in segs for w in s.words]
        for d in tl["lines"]:
            if a + 0.5 <= d["t0"] <= b - 3:
                near = [w for w in words if abs(w[0] - d["t0"]) < 1.0]
                onset = min(near, key=lambda w: abs(w[0] - d["t0"]))[0] if near else None
                diff = None if onset is None else round(onset - d["t0"], 3)
                grab = os.path.join(outdir, f"sync_{name}_{d['id']}.jpg")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{d['t0'] + 0.5:.2f}", "-i", film,
                                "-frames:v", "1", "-vf", "scale=540:-1", grab], check=True)
                rep.append(dict(window=name, id=d["id"], t0=d["t0"], asr_onset=onset, diff_s=diff,
                                first_word=next((w[2] for w in words if w[0] == onset), None)))
                print(rep[-1], flush=True)
    json.dump(rep, open(os.path.join(outdir, "sync_report.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
