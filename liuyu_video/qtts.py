# -*- coding: utf-8 -*-
"""Qwen3-TTS 旁白：设计声音 → 克隆 → 逐句合成，带音高与 ASR 校验。

流程（每个片段）：
  1. 文本做同音替换（只替换容易读错的文言/多音字），送 Qwen3-TTS-12Hz-1.7B-Base（克隆提示）；
  2. parselmouth 测中位音高，男声 85–105 Hz，不在范围就换 seed 重来；
  3. faster-whisper 回读，按无调拼音和期望读音比对；不过关换 seed，仍不过关记入报告；
  4. 去首尾静音，>0.4 s 的停顿压到 0.4 s，rubberband（保留共振峰）调到目标语速。
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SR = 24000
BASE = "/home/user/work/models/Qwen3-TTS-12Hz-1.7B-Base"
WHISPER = "/home/user/work/models/whisper-large-v3-turbo-ct2"
REF = "/home/user/work/qwen/ref.json"      # {"wav":..., "text":...}

F0_LO, F0_HI = 85.0, 105.0
MAX_TRIES = 5
ASR_OK = 0.9

# 送进 TTS 的同音替换：只替换容易读错的字，字幕仍用原文
TTS_SUB = [
    ("公元404年", "公元四零四年"), ("公元399年", "公元三九九年"), ("公元402年", "公元四零二年"), ("公元403年", "公元四零三年"),
    ("还不上", "环不上"), ("替他还钱", "替他环钱"), ("悄悄还的", "悄悄环的"),
    ("为时贱薄", "维时贱博"), ("卿当为", "卿当维"), ("称力", "趁力"), ("辟易", "必易"), ("瞋目", "嗔目"),
    ("长刀", "常刀"), ("矫情", "狡情"), ("刁逵", "刁葵"), ("王谧", "王密"), ("孟昶", "孟敞"), ("琅邪", "琅琊"),
    ("一喝", "一赫"), ("喝问", "赫问"), ("射中", "射众"), ("刀把子", "刀霸子"), ("江乘", "江城"), ("骰子", "投子"), ("句章", "勾章"),
    ("《", ""), ("》", ""), ("「", "“"), ("」", "”"),
]


def tts_text(s):
    for a, b in TTS_SUB:
        s = s.replace(a, b)
    return s


# ── 期望读音（无调拼音） ──────────────────────────────────
_PY = {}


def _init_py():
    if _PY:
        return
    import jieba
    from pypinyin import load_phrases_dict
    from pypinyin.contrib.tone_convert import to_tone
    import tts as ktts
    phrases = {}
    for w, py in ktts.PRON.items():
        syl = py.split()
        phrases[w] = [[to_tone(s)] for s in syl]
        jieba.add_word(w, freq=2_000_000)
    load_phrases_dict(phrases)
    _PY["ok"] = True


HAN = re.compile(r"[一-鿿]")


def syllables(text):
    """无调拼音序列（只取汉字；数字先转汉字）"""
    _init_py()
    import cn2an
    import jieba
    from pypinyin import lazy_pinyin, Style
    # 三位数（年份）逐位读：404 → 四零四；其余数字交给 cn2an
    t = re.sub(r"(?<!\d)\d{3}(?!\d)", lambda m: "".join("零一二三四五六七八九"[int(c)] for c in m.group()), text)
    t = cn2an.transform(t, "an2cn")
    out = []
    for w in jieba.lcut(t):
        hz = "".join(HAN.findall(w))
        if hz:
            out += lazy_pinyin(hz, style=Style.NORMAL)
    return out


def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


# ── 音高 ──────────────────────────────────────────────────
def median_f0(wav, sr=SR):
    import parselmouth
    snd = parselmouth.Sound(wav.astype(np.float64), sampling_frequency=sr)
    p = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


# ── 静音处理 ──────────────────────────────────────────────
def _frames_db(wav, win=0.02):
    n = int(win * SR)
    k = len(wav) // n
    if k == 0:
        return np.array([-120.0]), n
    fr = wav[: k * n].reshape(k, n)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms + 1e-9), n


def trim_and_cap(wav, cap=0.4, thr=-42.0, pad=0.04):
    db, n = _frames_db(wav)
    voiced = np.where(db > thr)[0]
    if len(voiced) == 0:
        return wav
    s = max(0, voiced[0] * n - int(pad * SR))
    e = min(len(wav), (voiced[-1] + 1) * n + int(pad * SR))
    wav = wav[s:e]
    # 压长停顿
    db, n = _frames_db(wav)
    silent = db <= thr
    out, i = [], 0
    k = len(silent)
    capf = int(cap / 0.02)
    while i < k:
        j = i
        while j < k and silent[j] == silent[i]:
            j += 1
        seg = wav[i * n: j * n]
        if silent[i] and (j - i) > capf:
            keep = capf * n
            half = keep // 2
            a, b = seg[:half], seg[-(keep - half):]
            fade = min(240, len(a), len(b))
            if fade > 0:
                a = a.copy(); b = b.copy()
                a[-fade:] *= np.linspace(1, 0, fade); b[:fade] *= np.linspace(0, 1, fade)
            seg = np.concatenate([a, b])
        out.append(seg)
        i = j
    out.append(wav[k * n:])
    return np.concatenate(out)


def stretch(wav, tempo):
    """rubberband 变速不变调，保留共振峰"""
    if abs(tempo - 1.0) < 0.01:
        return wav
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, wav, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality:transients=smooth:window=standard",
                        "-ar", str(SR), b], check=True)
        out, _ = sf.read(b, dtype="float32")
    return out


# ── 模型 ──────────────────────────────────────────────────
_M = {}


def model():
    if "tts" not in _M:
        import torch
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(int(os.environ.get("TTS_THREADS", "4")))
        m = Qwen3TTSModel.from_pretrained(BASE, device_map="cpu", dtype=torch.bfloat16)
        ref = json.load(open(REF))
        w, sr = sf.read(ref["wav"], dtype="float32")
        _M["prompt"] = m.create_voice_clone_prompt(ref_audio=(w, sr), ref_text=ref["text"])
        _M["tts"] = m
    return _M["tts"], _M["prompt"]


def asr_model():
    if "asr" not in _M:
        from faster_whisper import WhisperModel
        _M["asr"] = WhisperModel(WHISPER, device="cpu", compute_type="int8", cpu_threads=4)
    return _M["asr"]


def asr(wav):
    import opencc
    cc = _M.setdefault("cc", opencc.OpenCC("t2s"))
    m = asr_model()
    segs, _ = m.transcribe(wav.astype(np.float32) if SR == 16000 else _resample16(wav), language="zh",
                           initial_prompt="以下是普通话的句子。", word_timestamps=True, beam_size=5,
                           vad_filter=False, condition_on_previous_text=False)
    text, words = "", []
    for s in segs:
        text += s.text
        for w in (s.words or []):
            words.append((cc.convert(w.word.strip()), w.start, w.end))
    return cc.convert(text), words


def _resample16(wav):
    import librosa
    return librosa.resample(wav.astype(np.float32), orig_sr=SR, target_sr=16000)


def gen(text, seed):
    import torch
    m, prompt = model()
    torch.manual_seed(seed)
    np.random.seed(seed)
    wavs, sr = m.generate_voice_clone(text=text, language="Chinese", voice_clone_prompt=prompt)
    w = np.asarray(wavs[0], dtype=np.float32)
    if sr != SR:
        import librosa
        w = librosa.resample(w, orig_sr=sr, target_sr=SR)
    return w


def synth_segment(display, seeds=(1234, 2345, 3456, 4567, 5678), log=None):
    """返回 (wav, info)。display 为字幕用原文片段"""
    want = syllables(display)
    ttxt = tts_text(display)
    best = None
    tries = []
    for k, seed in enumerate(seeds[:MAX_TRIES]):
        t0 = time.time()
        w = gen(ttxt, seed)
        w = trim_and_cap(w)
        f0 = median_f0(w)
        text, words = asr(w)
        got = syllables(text)
        sim = similarity(want, got)
        ok_f0 = F0_LO <= f0 <= F0_HI
        ok_asr = sim >= ASR_OK
        info = dict(seed=seed, f0=round(f0, 1), sim=round(sim, 3), asr=text, dur=round(len(w) / SR, 2),
                    secs=round(time.time() - t0, 1))
        tries.append(info)
        if log:
            log(f"    seed {seed}: f0={f0:.1f}Hz sim={sim:.3f} dur={len(w)/SR:.2f}s  ASR:{text}")
        score = (ok_f0 and ok_asr, ok_asr, -abs(f0 - 95), sim)
        if best is None or score > best[0]:
            best = (score, w, info, words)
        if ok_f0 and ok_asr:
            break
    _, w, info, words = best
    info["tries"] = tries
    info["pass"] = bool(best[0][0])
    info["words"] = words
    return w, info


if __name__ == "__main__":
    print(syllables("他欠了钱，还不上。北朝敌国修的《魏书》更难听：「樗蒲倾产，为时贱薄」"))
