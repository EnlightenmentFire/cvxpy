"""ASR 回读：faster-whisper（small，CPU int8）逐句识别处理后的旁白，与稿子按无调拼音比对。
usage: python asr_check.py [id 前缀...]   -> asr_report.json，打印相似度 < 阈值的句子
"""
import sys, os, json, re, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import soundfile as sf, numpy as np
from scipy.signal import resample_poly

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WORK}/tts/proc"
TH = float(os.environ.get("ASR_TH", 0.85))


def py(s):
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return [p for p in lazy_pinyin(s) if p.strip()]


def main():
    pre = sys.argv[1:]
    m = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=4)
    rep, bad = [], []
    for d in all_lines():
        if pre and not any(d["id"].startswith(p) for p in pre):
            continue
        p = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p)
        x = resample_poly(x, 1, sr // 16000).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        r = difflib.SequenceMatcher(None, a, b).ratio()
        rep.append(dict(id=d["id"], ref=d["say"], hyp=hyp, sim=round(r, 3)))
        flag = "" if r >= TH else "  <<<"
        print(f"{d['id']} {r:.3f}{flag}\n   稿: {d['say']}\n   读: {hyp}", flush=True)
        if r < TH:
            bad.append(d["id"])
    old = {}
    if os.path.exists(f"{WORK}/asr_report.json"):
        old = {x["id"]: x for x in json.load(open(f"{WORK}/asr_report.json"))}
    for x in rep:
        old[x["id"]] = x
    json.dump(list(old.values()), open(f"{WORK}/asr_report.json", "w"), ensure_ascii=False, indent=1)
    print("low:", bad)


if __name__ == "__main__":
    main()
