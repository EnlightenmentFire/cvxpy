"""ASR read-back: transcribe each line with faster-whisper and compare (pinyin-level CER)."""
import sys, json, os, re, difflib
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import zhconv
import soundfile as sf, librosa, numpy as np

def load16(f):
    y, sr = sf.read(f, dtype="float32")
    if y.ndim > 1: y = y.mean(1)
    return librosa.resample(y, orig_sr=sr, target_sr=16000).astype(np.float32)

def norm(s):
    s = zhconv.convert(s, "zh-cn")
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)

def py(s):
    return lazy_pinyin(norm(s))

def digits(s):
    import re
    from tts import num2zh, DIG
    s = re.sub(r"(\d{4})\s*年", lambda m: "".join(DIG[int(d)] for d in m.group(1)) + "年", s)
    s = re.sub(r"(\d+)%", lambda m: "百分之" + num2zh(m.group(1)), s)
    return re.sub(r"\d+", lambda m: num2zh(m.group(0)), s)

def cer(ref, hyp):
    a, b = py(ref), py(digits(hyp))
    sm = difflib.SequenceMatcher(None, a, b)
    edits = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    return edits / max(1, len(a))

def main():
    model_dir, meta_path = sys.argv[1], sys.argv[2]
    files = sys.argv[3:]
    meta = json.load(open(meta_path))
    m = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("ASR_THREADS","4")))
    out = {}
    for f in files:
        key = os.path.basename(f)[:-4]
        ref = meta[key]["text"]
        segs, _ = m.transcribe(load16(f), language="zh", beam_size=5, vad_filter=False,
                               initial_prompt="以下是普通话的句子，关于韦伯、卡里斯玛、维泰博、多纳图派、康茂德。")
        hyp = "".join(s.text for s in segs)
        e = cer(ref, hyp)
        out[key] = dict(ref=ref, hyp=zhconv.convert(hyp, "zh-cn"), cer=round(e, 3))
        print(f"{key} CER={e:.3f} | {zhconv.convert(hyp,'zh-cn')}", flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(meta_path), "asr.json"), "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
