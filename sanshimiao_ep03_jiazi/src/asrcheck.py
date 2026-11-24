"""ASR read-back with faster-whisper large-v3 (CPU int8); compares in pinyin (tone-less) so
homophone characters don't count as errors but misreadings of sounds do."""
import re
import numpy as np

_M = None


def model():
    global _M
    if _M is None:
        from faster_whisper import WhisperModel
        _M = WhisperModel("/opt/models/faster-whisper-large-v3", device="cpu", compute_type="int8", cpu_threads=4)
    return _M


def to_cn_digits(s):
    import cn2an
    s = re.sub(r"(\d{4})\s*年", lambda m: "".join("零一二三四五六七八九"[int(c)] for c in m.group(1)) + "年", s)
    s = re.sub(r"\d+", lambda m: cn2an.an2cn(m.group(0)), s)
    return s


def norm_py(s, tone=False):
    import opencc
    from pypinyin import lazy_pinyin, Style
    s = opencc.OpenCC("t2s").convert(s)
    s = to_cn_digits(s)
    s = re.sub(r"[^一-鿿]", "", s)
    return lazy_pinyin(s, style=Style.TONE3 if tone else Style.NORMAL), s


def transcribe(a, sr, words=False, prompt=None):
    import librosa
    a16 = librosa.resample(np.asarray(a, np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else a
    segs, _ = model().transcribe(a16, language="zh", beam_size=5, word_timestamps=words, initial_prompt=prompt,
                                 condition_on_previous_text=False)
    segs = list(segs)
    text = "".join(s.text for s in segs).strip()
    if words:
        return text, [(w.word, w.start, w.end) for s in segs for w in s.words]
    return text


def per(ref, hyp):
    import jiwer
    r, _ = norm_py(ref)
    h, _ = norm_py(hyp)
    if not r:
        return 0.0
    return jiwer.wer(" ".join(r), " ".join(h) if h else "x")
