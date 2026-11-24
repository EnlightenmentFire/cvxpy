import re, sys, os
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
_W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_model = None
def model():
    global _model
    if _model is None:
        _model = WhisperModel(os.path.join(_W, "models/faster-whisper-large-v3-turbo-ct2"), device="cpu", compute_type="int8", cpu_threads=4)
    return _model
def load16k(path):
    import soundfile as sf, librosa, numpy as np
    y, sr = sf.read(path, dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
    return y.astype("float32")
def transcribe(path, lang="zh", prompt="以下是普通话的句子。"):
    segs, info = model().transcribe(load16k(path) if isinstance(path, str) else path, language=lang, beam_size=5, initial_prompt=prompt if lang == "zh" else None, vad_filter=False, word_timestamps=False)
    return "".join(s.text for s in segs).strip()
_D = "零一二三四五六七八九"


def _int_zh(n):
    if n < 10:
        return _D[n]
    if n < 20:
        return "十" + (_D[n % 10] if n % 10 else "")
    if n < 100:
        return _D[n // 10] + "十" + (_D[n % 10] if n % 10 else "")
    if n < 1000:
        r = n % 100
        if r == 0:
            tail = ""
        elif r < 10:
            tail = "零" + _D[r]
        else:
            tail = _D[r // 10] + "十" + (_D[r % 10] if r % 10 else "")
        return _D[n // 100] + "百" + tail
    if n < 10000:
        r = n % 1000
        return _D[n // 1000] + "千" + ("" if r == 0 else ("零" if r < 100 else "") + _int_zh(r))
    return "".join(_D[int(c)] for c in str(n))


def num_to_zh(s):
    s = re.sub(r"(\d+)\s*/\s*(\d+)", lambda m: _int_zh(int(m.group(2))) + "分之" + _int_zh(int(m.group(1))), s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*%", lambda m: "百分之" + _int_zh(int(float(m.group(1)))), s)
    s = re.sub(r"(\d{4})(?=\s*年)", lambda m: "".join(_D[int(c)] for c in m.group(1)), s)
    s = re.sub(r"\d+", lambda m: _int_zh(int(m.group(0))), s)
    return s


def norm_py(s):
    s = num_to_zh(s)
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    out = []
    for tok in lazy_pinyin(s):
        out.extend([tok] if re.fullmatch(r"[a-z]+", tok) else list(tok.lower()))
    return out
def edit(a, b):
    d = list(range(len(b)+1))
    for i in range(1, len(a)+1):
        prev, d[0] = d[0], i
        for j in range(1, len(b)+1):
            cur = d[j]
            d[j] = min(d[j]+1, d[j-1]+1, prev + (a[i-1] != b[j-1]))
            prev = cur
    return d[len(b)]
def pinyin_err(ref, hyp):
    r, h = norm_py(ref), norm_py(hyp)
    return edit(r, h) / max(1, len(r))
if __name__ == "__main__":
    ref = sys.argv[1]
    for p in sys.argv[2:]:
        hyp = transcribe(p)
        print(f"{os.path.basename(p)}  err={pinyin_err(ref, hyp):.3f}  hyp={hyp}")
