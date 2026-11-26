"""Step 3: clean up each narration take.
trim + cap pauses at 0.4 s -> rubberband tempo (formants preserved) to the target pace ->
50 Hz high-pass -> active-speech RMS to -18 dBFS -> ASR read-back of the processed audio."""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from audio_utils import cer, per, highpass, median_f0, normalize_rms, tempo, transcribe, trim_and_squeeze  # noqa: E402
from script_data import all_lines  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--voice", required=True, help="dir with raw/ and takes.json")
ap.add_argument("--ids", default="")
ap.add_argument("--narr-rate", type=float, default=5.0, help="target spoken chars per second for narration")
ap.add_argument("--quote-rate", type=float, default=4.3)
ap.add_argument("--slow-rate", type=float, default=4.0)
ap.add_argument("--max-factor", type=float, default=1.32)
ap.add_argument("--no-asr", action="store_true")
args = ap.parse_args()

lines = {l["id"]: l for l in all_lines()}
takes = json.load(open(os.path.join(args.voice, "takes.json")))
ids = [i for i in (args.ids.split(",") if args.ids else list(takes)) if i in lines]
os.makedirs(os.path.join(args.voice, "proc"), exist_ok=True)
report_path = os.path.join(args.voice, "proc_report.json")
report = json.load(open(report_path)) if os.path.exists(report_path) else {}


def spoken_chars(s):
    return len(re.sub(r"[\s，。、；：！？“”‘’《》（）「」…—,.;:!?A-Za-z]", "", s)) + len(re.findall(r"[A-Za-z]+", s))


for lid in ids:
    ln = lines[lid]
    w, sr = sf.read(os.path.join(args.voice, "raw", f"{lid}.wav"), dtype="float32")
    w = trim_and_squeeze(w, sr, max_pause=0.4)
    n = spoken_chars(ln["say"])
    rate0 = n / (len(w) / sr)
    style = ln.get("style", "")
    target = args.quote_rate if ln["kind"] == "quote" else (args.slow_rate if style == "slow" else args.narr_rate)
    if style == "smile":
        target = min(target, 4.9)
    factor = float(np.clip(target / rate0, 1.0, args.max_factor))
    y = tempo(w, sr, factor)
    y = trim_and_squeeze(y, sr, max_pause=0.4)
    y = highpass(y, sr, 50)
    y = normalize_rms(y, sr, -18.0)
    out = os.path.join(args.voice, "proc", f"{lid}.wav")
    sf.write(out, y, sr)
    f50, _, _ = median_f0(y, sr)
    r = dict(id=lid, rate_raw=round(rate0, 2), factor=round(factor, 3), rate=round(n / (len(y) / sr), 2),
             dur=round(len(y) / sr, 2), f0=round(f50, 1))
    if not args.no_asr:
        hyp = transcribe(y, sr)
        r["asr"] = hyp
        r["cer"] = round(float(cer(ln["say"], hyp)), 3)
        r["per"] = round(float(per(ln["say"], hyp)), 3)
    report[lid] = r
    print(json.dumps(r, ensure_ascii=False), flush=True)
json.dump(report, open(report_path, "w"), ensure_ascii=False, indent=1)
