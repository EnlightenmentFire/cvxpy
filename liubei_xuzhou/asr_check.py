# -*- coding: utf-8 -*-
"""faster-whisper 回读每句旁白，按无调拼音和送进 TTS 的文本比对。输出 asr_report.json。
python asr_check.py [ids...]
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import L, tts_text

LINES = "/tmp/claude-0/work/tts/lines"
MODEL = "/tmp/claude-0/models/faster-whisper-small"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asr_report.json")
NUM = "零一二三四五六七八九"


def py(text):
    from pypinyin import lazy_pinyin, Style
    import cn2an
    t = re.sub(r"\d+", lambda m: "".join(NUM[int(c)] for c in m.group()) if len(m.group()) == 4 or len(m.group()) == 3 else cn2an.an2cn(m.group()), text)
    hz = "".join(re.findall(r"[一-鿿]", t))
    return lazy_pinyin(hz, style=Style.NORMAL)


def main():
    from faster_whisper import WhisperModel
    m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("ASR_THREADS", 2)))
    want = set(sys.argv[1:])
    rep = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for d in L:
        if want and d["id"] not in want:
            continue
        p = f"{LINES}/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        import soundfile as sf
        from scipy.signal import resample_poly
        x, sr = sf.read(p)
        x = resample_poly(x, 1, 3).astype("float32") if sr == 48000 else x.astype("float32")
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。三国，刘备，陶谦，徐州。")
        hyp = "".join(s.text for s in segs)
        exp = tts_text(d.get("say", d["t"]))
        a, b = py(exp), py(hyp)
        sim = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        rep[d["id"]] = dict(sim=round(sim, 3), hyp=hyp, exp=d["t"])
        flag = "" if sim >= 0.9 else "  <<<"
        print(f"{d['id']} {sim:.3f} {hyp}{flag}", flush=True)
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1)
    bad = {k: v for k, v in rep.items() if v["sim"] < 0.9}
    print("lines", len(rep), "below 0.9:", len(bad), sorted(bad))


if __name__ == "__main__":
    main()
