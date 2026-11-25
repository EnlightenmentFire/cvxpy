# -*- coding: utf-8 -*-
"""Whole-file ASR read-back; pinyin-level CER against the full narration text.
usage: python asr_full.py <model_dir> <audio.wav> [label]"""
import sys, os, json, difflib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice"))
from asr_check import load16, py, digits
import script
from tts import to_tts
from faster_whisper import WhisperModel

def ref_text():
    return "".join(to_tts(l) for s in script.SEGMENTS for l in s["lines"] if l.get("k") != "en")

def main():
    model_dir, path = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(path)
    m = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("ASR_THREADS", "4")))
    segs, _ = m.transcribe(load16(path), language="zh", beam_size=5, vad_filter=True,
                           initial_prompt="以下是普通话纪录片旁白，关于韦伯、卡里斯玛、维泰博、多纳图派、康茂德。")
    hyp = "".join(s.text for s in segs)
    a, b = py(ref_text()), py(digits(hyp))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    edits = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    res = dict(label=label, ref_syllables=len(a), hyp_syllables=len(b), cer=round(edits / len(a), 4))
    print(json.dumps(res, ensure_ascii=False), flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(path)), f"asr_{label}.json")
    json.dump(dict(res, hyp=hyp), open(out, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
