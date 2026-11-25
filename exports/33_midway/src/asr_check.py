# -*- coding: utf-8 -*-
"""ASR read-back: faster-whisper small on each processed line; compare toneless pinyin.
usage: python asr_check.py [lines|final]   final = cut lines out of the final mix by timeline"""
import sys, os, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from pypinyin import lazy_pinyin
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from faster_whisper import WhisperModel

WORK = "/tmp/claude-0/work"
NUM = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}


def norm(s):
    s = s.upper().replace("AF", "诶夫")
    s = re.sub(r"\d", lambda m: NUM[m.group()], s)
    return [p for p in lazy_pinyin(re.sub(r"[^一-鿿]", "", s))]


def to16(x, sr):
    if x.ndim > 1:
        x = x.mean(1)
    g = np.gcd(sr, 16000)
    return resample_poly(x, 16000 // g, sr // g).astype(np.float32)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "lines"
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    tl = json.load(open(f"{WORK}/timeline.json"))
    L = {l["id"]: l for l in tl["lines"]}
    if mode == "final":
        mixp = sys.argv[2]
        X, sr = sf.read(mixp)
    rep, bad = [], 0
    for d in all_lines():
        if mode == "lines":
            x, sr = sf.read(f"{WORK}/tts/proc/{d['id']}.wav")
        else:
            l = L[d["id"]]; x = X[int((l["s0"] - 0.05) * sr):int((l["s1"] + 0.1) * sr)]
        segs, _ = m.transcribe(to16(x, sr), language="zh", beam_size=5, initial_prompt="以下是普通话的句子，关于中途岛海战。")
        hyp = "".join(s.text for s in segs)
        a, b = norm(d["say"]), norm(hyp)
        sm = SequenceMatcher(None, a, b)
        err = 1 - sm.ratio()
        rep.append(dict(id=d["id"], ref=d["say"], hyp=hyp, err=round(err, 3)))
        if err > 0.08:
            bad += 1
            print(f"!! {d['id']} err={err:.2f}\n   REF {d['say']}\n   HYP {hyp}", flush=True)
    tot = np.mean([r["err"] for r in rep])
    json.dump(rep, open(f"{WORK}/asr_{mode}.json", "w"), ensure_ascii=False, indent=1)
    print(f"mean pinyin err {tot:.3f}; lines over 8%: {bad}/{len(rep)}")


if __name__ == "__main__":
    main()
