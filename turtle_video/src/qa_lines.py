"""Per-line ASR on the final mix (full band and simulated phone speaker), same pinyin metric as the narration QA."""
import json, sys
import numpy as np, soundfile as sf
sys.path.insert(0, "/tmp/claude-0/-home-user-cvxpy/78685b54-039d-5b0e-946b-2cbac616b0ef/scratchpad/voice")
from qa_audio import phone, to16k, transcribe
from tts import per
from script_data import SEGMENTS

def main(mixdir, out_json):
    rep = json.load(open(mixdir + "/mix_report.json"))
    tts = {l["id"]: l["tts"] for s in SEGMENTS for l in s["lines"]}
    x, sr = sf.read(mixdir + "/mix.wav", dtype="float32", always_2d=True)
    v, _ = sf.read(mixdir + "/stem_voice.wav", dtype="float32", always_2d=True)
    res = {}
    for ln in rep["lines"]:
        a, b = int((ln["start"] - 0.15) * sr), int((ln["end"] + 0.15) * sr)
        row = {}
        for name, sig in (("voice_only", v[a:b].mean(1)), ("mix", x[a:b].mean(1)), ("mix_phone", phone(x[a:b]))):
            hyp = transcribe(to16k(sig))
            row[name] = round(per(tts[ln["id"]], hyp), 3)
            if row[name] > 0.08:
                row[name + "_asr"] = hyp
        res[ln["id"]] = row
    summ = {k: dict(mean=round(float(np.mean([r[k] for r in res.values()])), 4),
                    lines_over_8pct=[i for i, r in res.items() if r[k] > 0.08]) for k in ("voice_only", "mix", "mix_phone")}
    json.dump(dict(summary=summ, lines=res), open(out_json, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    for i, r in res.items():
        if r["mix"] > 0.08 or r["mix_phone"] > 0.08:
            print(i, {k: v for k, v in r.items()})

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
