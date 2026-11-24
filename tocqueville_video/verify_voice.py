"""Post-process every line, then check median F0 (Praat, 75-300 Hz) on the processed audio and ASR read-back.
Writes /tmp/claude-0/work/tts/verify.json and prints failures.
usage: python verify_voice.py [id prefixes...]   (default: all)
"""
import sys, os, json
import numpy as np, soundfile as sf, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
import voice_post
from asr_check import check, norm

PROC = "/tmp/claude-0/work/tts/proc"
RAW = "/tmp/claude-0/work/tts/raw"
OUTP = "/tmp/claude-0/work/tts/verify.json"


def f0(path):
    x, sr = sf.read(path)
    p = parselmouth.Sound(x, sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300).selected_array["frequency"]
    p = p[p > 0]
    return float(np.median(p)) if len(p) else 0.0


def main():
    pre = sys.argv[1:] or [""]
    res = json.load(open(OUTP)) if os.path.exists(OUTP) else {}
    bad = []
    for d in all_lines():
        if not any(d["id"].startswith(p) for p in pre):
            continue
        if not os.path.exists(f"{RAW}/{d['id']}.wav"):
            print("MISSING", d["id"]); bad.append(d["id"]); continue
        voice_post.process(d)
        hz = f0(f"{PROC}/{d['id']}.wav")
        hyp, per = check(f"{PROC}/{d['id']}.wav", d["say"])
        ok_p = 85 <= hz <= 105
        ok_a = per <= 0.08
        res[d["id"]] = dict(f0=round(hz, 1), per=round(per, 3), hyp=norm(hyp), ok=ok_p and ok_a)
        flag = "OK " if ok_p and ok_a else "BAD"
        print(f"{flag} {d['id']} f0={hz:.1f} per={per:.2f}" + ("" if ok_a else f"\n    want {norm(d['say'])}\n    got  {norm(hyp)}"), flush=True)
        if not (ok_p and ok_a):
            bad.append(d["id"])
    json.dump(res, open(OUTP, "w"), ensure_ascii=False, indent=1)
    print("FAILED:", " ".join(bad))


if __name__ == "__main__":
    main()
