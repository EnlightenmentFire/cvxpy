"""Voice QC helpers: pitch (parselmouth), ASR read-back (faster-whisper), pause/tempo/level processing.

Runs in the qwen312 venv (parselmouth, faster-whisper, pypinyin, soundfile).
"""
import functools
import os
import re
import subprocess
import tempfile

import numpy as np
import soundfile as sf

PITCH_LO, PITCH_HI = 85.0, 105.0
MAX_PAUSE = 0.38
TARGET_RMS_DBFS = -18.0


# ----------------------------------------------------------------------------
# pitch
# ----------------------------------------------------------------------------

def f0_median(x, sr):
    import parselmouth
    snd = parselmouth.Sound(np.asarray(x, np.float64), sampling_frequency=sr)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=60.0, pitch_ceiling=300.0)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


# ----------------------------------------------------------------------------
# ASR read-back
# ----------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _whisper():
    from faster_whisper import WhisperModel
    return WhisperModel("Systran/faster-whisper-medium", device="cpu", compute_type="int8", cpu_threads=4)


def asr(x, sr):
    import librosa
    y = librosa.resample(np.asarray(x, np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else x
    segs, _ = _whisper().transcribe(y, language="zh", beam_size=5, vad_filter=False,
                                    initial_prompt="以下是普通话的句子，使用简体中文。")
    return "".join(s.text for s in segs).strip()


_CN_DIGIT = "零一二三四五六七八九"


def _int_to_cn(n):
    """Read an integer the way a narrator would (0..99999999)."""
    n = int(n)
    if n == 0:
        return "零"
    units = [(10 ** 8, "亿"), (10 ** 4, "万"), (1000, "千"), (100, "百"), (10, "十")]

    def rd(v):
        out = ""
        zero = False
        for base, name in units:
            q, v = divmod(v, base)
            if q:
                if zero and out:
                    out += "零"
                out += (rd(q) if q >= 10 else ("两" if q == 2 and name in ("千", "万", "亿") else _CN_DIGIT[q])) + name
                zero = False
            elif out:
                zero = True
        if v:
            if zero and out:
                out += "零"
            out += _CN_DIGIT[v]
        return out
    r = rd(n)
    return r[1:] if r.startswith("一十") else r


def _digits_to_cn(text):
    text = re.sub(r"(\d{4})年", lambda m: "".join(_CN_DIGIT[int(c)] for c in m.group(1)) + "年", text)
    text = re.sub(r"\d+(\.\d+)?", lambda m: _int_to_cn(m.group(0).split(".")[0]), text)
    return text


def to_syllables(text):
    from pypinyin import lazy_pinyin
    text = _digits_to_cn(text)
    text = re.sub(r"[^一-鿿A-Za-z]", "", text)
    return [s for s in lazy_pinyin(text) if s.strip()]


def edit_distance(a, b):
    n, m = len(a), len(b)
    d = list(range(m + 1))
    for i in range(1, n + 1):
        prev, d[0] = d[0], i
        for j in range(1, m + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, d[j] = d[j], cur
    return d[m]


def syllable_error_rate(expected, recognized):
    a, b = to_syllables(expected), to_syllables(recognized)
    if not a:
        return 0.0
    return edit_distance(a, b) / len(a)


def tone_warnings(expected, recognized):
    """Tone mismatches between script and ASR read-back, allowing 3-3 sandhi and 一/不 sandhi.
    Warnings only: ASR picks characters by context, so these need a human ear to confirm."""
    from pypinyin import Style, lazy_pinyin
    import difflib
    ea = re.sub(r"[^\u4e00-\u9fff]", "", _digits_to_cn(expected))
    rb = re.sub(r"[^\u4e00-\u9fff]", "", _digits_to_cn(recognized))
    a = lazy_pinyin(ea, style=Style.TONE3, neutral_tone_with_five=True)
    b = lazy_pinyin(rb, style=Style.TONE3, neutral_tone_with_five=True)
    ok_tones = []
    for i, p in enumerate(a):
        t = p[-1]
        acc = {t}
        if t == "3" and i + 1 < len(a) and a[i + 1][-1] == "3":
            acc.add("2")
        if ea[i] == "一":
            acc |= {"1", "2", "4"}
        if ea[i] == "不":
            acc |= {"2", "4"}
        ok_tones.append(acc)
    sm = difflib.SequenceMatcher(a=[x[:-1] for x in a], b=[x[:-1] for x in b], autojunk=False)
    out = []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i, j = blk.a + k, blk.b + k
            tb = b[j][-1]
            if tb != "5" and a[i][-1] != "5" and tb not in ok_tones[i]:
                out.append(f"{ea[i]}({a[i]})~{rb[j]}({b[j]})")
    return out


def diff_report(expected, recognized):
    a, b = to_syllables(expected), to_syllables(recognized)
    import difflib
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            out.append(f"{op}: {' '.join(a[i1:i2])} -> {' '.join(b[j1:j2])}")
    return out


# ----------------------------------------------------------------------------
# signal processing
# ----------------------------------------------------------------------------

def frame_db(x, sr, win=0.02):
    n = max(1, int(win * sr))
    k = len(x) // n
    fr = x[: k * n].reshape(k, n)
    rms = np.sqrt(np.mean(fr ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms), n


def trim_silence(x, sr, thresh_db=-45.0, pad=0.06):
    db, n = frame_db(x, sr)
    ref = np.max(db)
    act = np.where(db > ref + thresh_db)[0]
    if len(act) == 0:
        return x
    a = max(0, act[0] * n - int(pad * sr))
    b = min(len(x), (act[-1] + 1) * n + int(pad * sr))
    return x[a:b]


def compress_pauses(x, sr, max_pause=MAX_PAUSE, thresh_db=-42.0):
    """Shorten every internal silence longer than max_pause down to max_pause."""
    db, n = frame_db(x, sr)
    ref = np.max(db)
    sil = db < ref + thresh_db
    out = []
    i = 0
    k = len(sil)
    keep = int(max_pause * sr)
    while i < k:
        j = i
        while j < k and sil[j] == sil[i]:
            j += 1
        seg = x[i * n: j * n]
        if sil[i] and len(seg) > keep and 0 < i and j < k:
            half = keep // 2
            fade = np.linspace(1, 0, min(half, 256))
            a = seg[:half].copy()
            b = seg[-(keep - half):].copy()
            a[-len(fade):] *= fade
            b[: len(fade)] *= fade[::-1]
            out.append(np.concatenate([a, b]))
        else:
            out.append(seg)
        i = j
    out.append(x[k * n:])
    return np.concatenate(out)


def longest_pause(x, sr, thresh_db=-42.0):
    db, n = frame_db(x, sr)
    ref = np.max(db)
    sil = db < ref + thresh_db
    best = cur = 0
    # ignore leading/trailing silence
    idx = np.where(~sil)[0]
    if len(idx) == 0:
        return 0.0
    for s in sil[idx[0]: idx[-1] + 1]:
        cur = cur + 1 if s else 0
        best = max(best, cur)
    return best * n / sr


def rubberband_tempo(x, sr, tempo):
    if abs(tempo - 1.0) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        sf.write(a, x, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-q", "-3", "--formant", "-T", f"{tempo:.4f}", a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, _ = sf.read(b, dtype="float32")
    return y


def highpass50(x, sr):
    from scipy import signal
    b, a = signal.butter(2, 50.0 / (sr / 2), "high")
    return signal.lfilter(b, a, x).astype(np.float32)


def active_rms_db(x, sr, thresh_db=-35.0):
    db, n = frame_db(x, sr)
    ref = np.max(db)
    act = db > ref + thresh_db
    if not np.any(act):
        return -120.0
    k = len(db)
    fr = x[: k * n].reshape(k, n)[act]
    return 20 * np.log10(np.sqrt(np.mean(fr ** 2)) + 1e-12)


def normalize_rms(x, sr, target=TARGET_RMS_DBFS):
    g = 10 ** ((target - active_rms_db(x, sr)) / 20)
    y = x * g
    peak = np.max(np.abs(y))
    if peak > 0.98:  # soft-limit rare peaks rather than lowering the whole line
        y = np.tanh(y / 0.98) * 0.98
    return y.astype(np.float32)


def speech_rate(text, x, sr):
    n = len(re.sub(r"[^一-鿿]", "", _digits_to_cn(text)))
    return n / (len(x) / sr)
