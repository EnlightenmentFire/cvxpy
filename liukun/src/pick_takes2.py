# -*- coding: utf-8 -*-
"""可疑句多版本择优：对 vo_alt/nXXX_seed.wav 与原版逐一 ASR，取拼音误差最小者写回 vo_raw/nXXX.wav"""
import glob, json, os, re, shutil, sys
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = {l["id"]: l for l in json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf8"))}
CHANGED = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio", "todo_v2.json"))))     # 文本改过，原版作废
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
han = lambda s: re.sub(r"[^一-鿿]", "", s)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
def score(f, ref):
    segs, _ = m.transcribe(f, language="zh", beam_size=5, initial_prompt="以下是普通话的句子，讲西晋刘琨、祖逖、石勒、刘聪、段匹磾的历史。", condition_on_previous_text=False)
    hyp = "".join(s.text for s in segs); a, b = lazy_pinyin(han(ref)), lazy_pinyin(han(hyp)); return ed(a, b) / max(1, len(a)), hyp
ids = sorted({os.path.basename(f).split("_")[0] for f in glob.glob(os.path.join(ROOT, "audio", "vo_alt2", "n*_*.wav"))})
log = []
for i in ids:
    ref = lines[i]["tts"]; cands = sorted(glob.glob(os.path.join(ROOT, "audio", "vo_alt2", i + "_*.wav")))
    if i not in CHANGED: cands = [os.path.join(ROOT, "audio", "vo_raw2", i + ".wav")] + cands
    res = [(score(f, ref), f) for f in cands]; res.sort(key=lambda r: r[0][0])
    (e, hyp), best = res[0]
    print(i, " | ".join("%s=%.2f" % (os.path.basename(f)[:-4], s[0]) for s, f in res), "->", os.path.basename(best), "|", han(hyp), flush=True)
    log.append(dict(id=i, chosen=os.path.basename(best), err=e, hyp=hyp, all={os.path.basename(f): s[0] for s, f in res}))
    if os.path.abspath(best) != os.path.abspath(os.path.join(ROOT, "audio", "vo_raw2", i + ".wav")):
        shutil.copy(best, os.path.join(ROOT, "audio", "vo_raw2", i + ".wav"))
json.dump(log, open(os.path.join(ROOT, "audio", "pick_takes_v2.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
