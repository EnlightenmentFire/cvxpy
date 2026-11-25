"""ASR 回读：faster-whisper small 逐句转写，按无调拼音和稿子比对。
usage: python asr_check.py OUT.txt [id 前缀...]"""
import sys, os, re, difflib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
VOICE = os.environ.get("VOICE_DIR", f"{WORK}/tts/proc")
NUM = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六", "7": "七", "8": "八", "9": "九", ".": "点", "%": ""}


def norm_py(s):
    s = re.sub(r"[^一-鿿0-9.%]", "", s)
    s = "".join(NUM.get(c, c) for c in s)
    return lazy_pinyin(s)


def main():
    out = sys.argv[1]
    pre = sys.argv[2:]
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("THREADS", 2)))
    rows, scores = [], []
    for d in all_lines():
        if pre and not any(d["id"].startswith(p) for p in pre):
            continue
        w, sr = sf.read(f"{VOICE}/{d['id']}.wav", dtype="float32")
        if w.ndim > 1:
            w = w.mean(1)
        w = resample_poly(w, 1, sr // 16000).astype(np.float32) if sr != 16000 else w
        seg, _ = m.transcribe(w, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in seg)
        a, b = norm_py(d["tts"]), norm_py(hyp)
        r = difflib.SequenceMatcher(None, a, b).ratio()
        scores.append(r)
        flag = "  <-- 查" if r < 0.85 else ""
        rows.append(f"{d['id']}\t{r:.2f}\t稿：{d['say']}\n\t\tASR：{hyp}{flag}")
        print(rows[-1], flush=True)
    with open(out, "w") as f:
        f.write(f"# ASR 回读（faster-whisper small，无调拼音比对）  平均 {np.mean(scores):.3f}，"
                f"<0.85 共 {sum(s < 0.85 for s in scores)} 句\n\n" + "\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
