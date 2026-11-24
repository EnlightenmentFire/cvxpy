"""Pre-export audio checks (配乐规范 §五):
  - ASR error rate per chapter: narration only vs. final mix vs. final mix through a simulated phone speaker
  - export the climax excerpt for a separate listen

usage: python qa_audio.py MIXDIR OUT_JSON CLIMAX_M4A
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly

VOICE = "/tmp/claude-0/-home-user-cvxpy/78685b54-039d-5b0e-946b-2cbac616b0ef/scratchpad/voice"
sys.path.insert(0, VOICE)
from asr import model as asr_model   # noqa: E402
from tts import to_pinyin, edit       # noqa: E402
from script_data import SEGMENTS      # noqa: E402

SR = 48000


def phone(x):
    """Small loudspeaker: mono, nothing below ~300 Hz, rolled off above ~6.5 kHz."""
    m = x.mean(1) if x.ndim == 2 else x
    sos = butter(4, [300, 6500], btype="bandpass", fs=SR, output="sos")
    return sosfiltfilt(sos, m).astype(np.float32)


def to16k(m):
    return resample_poly(m, 1, 3).astype(np.float32)


def transcribe(m16):
    segs, _ = asr_model().transcribe(m16, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。", vad_filter=False)
    return "".join(s.text for s in segs)


def main(mixdir, out_json, climax_m4a):
    rep = json.load(open(os.path.join(mixdir, "mix_report.json")))
    lines = rep["lines"]
    seg_text = {}
    seg_span = {}
    for ln in lines:
        seg_text[ln["seg"]] = seg_text.get(ln["seg"], "") + next(l["tts"] for s in SEGMENTS for l in s["lines"] if l["id"] == ln["id"])
        a, b = seg_span.get(ln["seg"], (1e9, 0))
        seg_span[ln["seg"]] = (min(a, ln["start"]), max(b, ln["end"]))
    sources = {"voice_only": "stem_voice.wav", "mix": "mix.wav"}
    audio = {k: sf.read(os.path.join(mixdir, v), dtype="float32", always_2d=True)[0] for k, v in sources.items()}
    audio["mix_phone"] = audio["mix"]
    out = {}
    tot = {k: [0, 0] for k in audio}
    for seg, (a, b) in seg_span.items():
        ref = to_pinyin(seg_text[seg])
        row = {}
        for k, x in audio.items():
            chunk = x[int((a - 0.3) * SR): int((b + 0.3) * SR)]
            m = phone(chunk) if k == "mix_phone" else chunk.mean(1)
            hyp = to_pinyin(transcribe(to16k(m)))
            e = edit(ref, hyp)
            row[k] = round(e / max(1, len(ref)), 4)
            tot[k][0] += e
            tot[k][1] += len(ref)
        out[seg] = row
        print(seg, row, flush=True)
    out["_overall"] = {k: round(v[0] / max(1, v[1]), 4) for k, v in tot.items()}
    print("overall", out["_overall"])
    json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=1)
    # climax excerpt
    mk = rep["marks"]
    t0, t1 = mk["t_diff"] - 4.0, mk["t_doubt"] + 6.0
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.2f}", "-t", f"{t1 - t0:.2f}", "-i", os.path.join(mixdir, "mix.wav"),
                    "-af", "afade=t=in:d=0.5,afade=t=out:st=%.2f:d=1.0" % (t1 - t0 - 1.0), "-c:a", "aac", "-b:a", "192k", climax_m4a], check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
