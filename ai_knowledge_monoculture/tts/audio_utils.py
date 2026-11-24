"""Audio checks and clean-up used by the narration pipeline."""
import os
import re
import subprocess
import tempfile

import numpy as np
import parselmouth
import soundfile as sf

_ASR = None


def median_f0(wav, sr, floor=50, ceil=300):
    snd = parselmouth.Sound(np.asarray(wav, np.float64), sampling_frequency=sr)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=floor, pitch_ceiling=ceil)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    if len(f) == 0:
        return 0.0, 0.0, 0.0
    return float(np.median(f)), float(np.percentile(f, 10)), float(np.percentile(f, 90))


def asr_model():
    global _ASR
    if _ASR is None:
        from faster_whisper import WhisperModel
        _ASR = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
    return _ASR


def transcribe(path_or_wav, sr=None, lang="zh", words=False, prompt=None):
    m = asr_model()
    if isinstance(path_or_wav, str):
        wav, sr = sf.read(path_or_wav, dtype="float32")
    else:
        wav = np.asarray(path_or_wav, np.float32)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if sr != 16000:  # pass a 16 kHz array directly (avoids PyAV decoding)
        from scipy.signal import resample_poly
        g = np.gcd(int(sr), 16000)
        wav = resample_poly(wav, 16000 // g, int(sr) // g).astype(np.float32)
    src = wav
    segs, _ = m.transcribe(src, language=lang, beam_size=5, word_timestamps=words, vad_filter=False,
                           initial_prompt=prompt, condition_on_previous_text=False)
    segs = list(segs)
    text = "".join(s.text for s in segs)
    if words:
        ws = [(w.word, w.start, w.end) for s in segs for w in (s.words or [])]
        return text, ws
    return text


CN_DIGITS = "零一二三四五六七八九"


def normalize_zh(s):
    """Strip punctuation/spaces, map Arabic digits to Chinese digits, unify a few variants."""
    try:
        import cn2an
        s = cn2an.transform(s, "an2cn")
    except Exception:
        pass
    s = s.lower()
    s = re.sub(r"[\s，。、；：！？“”‘’《》（）()\-—…·,.;:!?'\"%]", "", s)
    s = s.replace("%", "")
    s = "".join(CN_DIGITS[int(c)] if c.isdigit() else c for c in s)
    for a, b in [("〇", "零"), ("两", "二"), ("他", "它"), ("她", "它"), ("地", "的"), ("得", "的")]:
        s = s.replace(a, b)
    return s


def cer(ref, hyp):
    r, h = normalize_zh(ref), normalize_zh(hyp)
    if not r:
        return 0.0
    d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        prev = d.copy()
        d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(h)] / len(r)


def to_syllables(s):
    """Text -> list of tone-numbered pinyin syllables (Latin words kept as lowercase tokens).
    Comparing syllables instead of characters ignores ASR homophone spellings
    (e.g. 艾利斯 / 爱丽丝) but still catches wrong sounds or tones."""
    from pypinyin import Style, lazy_pinyin
    s = normalize_zh(s)
    out = []
    for tok in lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True, errors=lambda x: list(x)):
        tok = tok.strip()
        if not tok:
            continue
        out.append(tok)
    # merge consecutive single Latin letters (e.g. o p t -> opt) for a fair comparison
    merged = []
    for tok in out:
        if len(tok) == 1 and tok.isascii() and tok.isalpha() and merged and merged[-1].isascii() and merged[-1].isalpha() \
                and not any(c.isdigit() for c in merged[-1]):
            merged[-1] += tok
        else:
            merged.append(tok)
    return merged


def per(ref, hyp):
    """Syllable (pinyin+tone) error rate."""
    r, h = to_syllables(ref), to_syllables(hyp)
    if not r:
        return 0.0
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev = d[:]
        d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(h)] / len(r)


def frame_rms_db(wav, sr, win=0.02):
    n = int(sr * win)
    k = len(wav) // n
    if k == 0:
        return np.array([-120.0])
    fr = wav[: k * n].reshape(k, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)


def trim_and_squeeze(wav, sr, thresh_db=-42, max_pause=0.4, edge=0.06):
    """Trim leading/trailing silence and shorten internal pauses longer than max_pause."""
    win = 0.02
    db = frame_rms_db(wav, sr, win)
    voiced = db > thresh_db
    if not voiced.any():
        return wav
    n = int(sr * win)
    first = max(0, np.argmax(voiced) * n - int(edge * sr))
    last = min(len(wav), (len(voiced) - np.argmax(voiced[::-1])) * n + int(edge * sr))
    wav = wav[first:last]
    db = frame_rms_db(wav, sr, win)
    voiced = db > thresh_db
    out, i = [], 0
    maxf = int(max_pause / win)
    while i < len(voiced):
        j = i
        while j < len(voiced) and voiced[j] == voiced[i]:
            j += 1
        seg = wav[i * n: j * n]
        if not voiced[i] and (j - i) > maxf:
            keep = maxf * n
            half = keep // 2
            fade = np.linspace(1, 0, min(half, 240))
            a = seg[:half].copy()
            b = seg[-half:].copy()
            a[-len(fade):] *= fade
            b[: len(fade)] *= fade[::-1]
            seg = np.concatenate([a, b])
        out.append(seg)
        i = j
    out.append(wav[len(voiced) * n:])
    return np.concatenate(out)


def ffmpeg_filter(wav, sr, af, out_sr=None):
    """Run an ffmpeg audio filter chain on a mono float array."""
    fd1, src = tempfile.mkstemp(suffix=".wav")
    fd2, dst = tempfile.mkstemp(suffix=".wav")
    os.close(fd1)
    os.close(fd2)
    sf.write(src, wav, sr, subtype="FLOAT")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af]
    if out_sr:
        cmd += ["-ar", str(out_sr)]
    cmd += ["-c:a", "pcm_f32le", dst]
    subprocess.run(cmd, check=True)
    y, sr2 = sf.read(dst, dtype="float32")
    os.remove(src)
    os.remove(dst)
    return y, sr2


def tempo(wav, sr, factor):
    """Speed up without changing pitch; rubberband with formants preserved."""
    if abs(factor - 1) < 1e-3:
        return wav
    y, _ = ffmpeg_filter(wav, sr, f"rubberband=tempo={factor:.4f}:formant=preserved:pitchq=quality")
    return y


def highpass(wav, sr, f=50):
    y, _ = ffmpeg_filter(wav, sr, f"highpass=f={f}:poles=2")
    return y


def rms_dbfs(wav):
    return 20 * np.log10(np.sqrt(np.mean(np.square(wav))) + 1e-12)


def active_rms_dbfs(wav, sr, thresh_db=-45):
    db = frame_rms_db(wav, sr)
    n = int(sr * 0.02)
    k = len(wav) // n
    fr = wav[: k * n].reshape(k, n)
    act = fr[db[:k] > thresh_db]
    if len(act) == 0:
        return rms_dbfs(wav)
    return rms_dbfs(act.ravel())


def normalize_rms(wav, sr, target=-18.0, peak_ceiling=-1.0):
    g = 10 ** ((target - active_rms_dbfs(wav, sr)) / 20)
    y = wav * g
    pk = np.max(np.abs(y)) + 1e-9
    lim = 10 ** (peak_ceiling / 20)
    if pk > lim:  # gentle soft clip instead of hard clipping
        y = np.tanh(y / lim) * lim
    return y.astype(np.float32)
