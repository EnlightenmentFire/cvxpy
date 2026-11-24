# -*- coding: utf-8 -*-
"""逐句配音：Qwen3-TTS Base 克隆（参考音由 VoiceDesign 设计）→ 音高检查 → ASR 回读 → 后处理。

用法：python3 tts_build.py [段落号...]      例如  python3 tts_build.py 0 1
产物：$WORK/beats/<id>.wav（24 kHz 单声道，已高通/压停顿/拉速/电平统一）与 manifest.json
"""
import hashlib, json, os, re, subprocess, sys, time

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import B  # noqa: E402

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
REF_WAV = os.environ.get("KAL_REF", os.path.join(WORK, "ref_voice.wav"))
REF_TEXT = "一九九七年八月六日凌晨，关岛下着雨。一架从首尔起飞的波音七四七，正在穿过云层，准备降落。"
OUT = os.path.join(WORK, "beats")
RAW = os.path.join(WORK, "beats_raw")
MAN = os.path.join(WORK, "manifest.json")
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

F0_LO, F0_HI = 85.0, 105.0          # 男声中位音高目标
CER_MAX = 0.10                       # 拼音级错误率上限
MAX_TRIES = 6
TEMPO = {"narr": 1.16, "quote": 1.06}  # 旁白偏快，引文稍慢
PAUSE_MAX = 0.40                     # 句内停顿上限（秒）
TARGET_RMS_DB = -20.0                # 单句活动语音 RMS；混音时整体推到 -18 dBFS


# ───────────── 文本归一（拼音比对） ─────────────
def to_tokens(s):
    import cn2an
    from pypinyin import lazy_pinyin
    s = s.replace("D C 八", "DC八")
    try:
        s = cn2an.transform(s, "an2cn")
    except Exception:
        pass
    toks = []
    for ch in s:
        if "一" <= ch <= "鿿":
            toks.append(lazy_pinyin(ch)[0])
        elif ch.isascii() and ch.isalpha():
            toks.append(ch.lower())
    return toks


def cer(ref, hyp):
    a, b = to_tokens(ref), to_tokens(hyp)
    if not a:
        return 0.0
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return d[len(b)] / len(a)


# ───────────── 声学工具 ─────────────
def median_f0(w, sr):
    import parselmouth
    snd = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


def hpf(w, sr, fc=50.0):
    sos = butter(2, fc, btype="highpass", fs=sr, output="sos")
    return sosfiltfilt(sos, w).astype(np.float32)


def frame_db(w, sr, hop=0.01, win=0.03):
    h, n = int(sr * hop), int(sr * win)
    pad = np.pad(w, (n // 2, n // 2))
    idx = np.arange(0, len(w), h)
    r = np.array([np.sqrt(np.mean(pad[i:i + n] ** 2) + 1e-12) for i in idx])
    return 20 * np.log10(r + 1e-9), h


def trim_and_squeeze(w, sr):
    """去首尾静音；句内超过 PAUSE_MAX 的停顿压到 PAUSE_MAX（中间切掉，8 ms 交叉淡化）。"""
    xf = int(0.008 * sr)
    db, h = frame_db(w, sr)
    thr = max(-48.0, db.max() - 38.0)
    v = db > thr
    if not v.any():
        return w
    i0 = max(0, int(np.argmax(v)) - 3)
    i1 = min(len(v), len(v) - int(np.argmax(v[::-1])) + 4)
    w = w[i0 * h:i1 * h]
    maxf = int(round(PAUSE_MAX / 0.01))
    keep = maxf // 2
    for _ in range(80):
        db, h = frame_db(w, sr)
        v = db > thr
        cut = None
        i = 0
        while i < len(v):
            if not v[i]:
                j = i
                while j < len(v) and not v[j]:
                    j += 1
                if j - i > maxf and i > 0 and j < len(v):
                    cut = ((i + keep) * h, (j - keep) * h)
                    break
                i = j
            else:
                i += 1
        if cut is None:
            break
        w = _xfade_concat([w[:cut[0]], w[cut[1]:]], xf)
    return w


def _xfade_concat(parts, xf):
    out = parts[0].astype(np.float32)
    for p in parts[1:]:
        p = p.astype(np.float32)
        if len(out) > xf and len(p) > xf:
            fade = np.linspace(0, 1, xf, dtype=np.float32)
            mid = out[-xf:] * (1 - fade) + p[:xf] * fade
            out = np.concatenate([out[:-xf], mid, p[xf:]])
        else:
            out = np.concatenate([out, p])
    return out


def active_rms_db(w, sr):
    db, h = frame_db(w, sr)
    thr = db.max() - 30
    act = db[db > thr]
    return float(10 * np.log10(np.mean(10 ** (act / 10)))) if len(act) else -99.0


def stretch(w, sr, tempo, tag):
    if abs(tempo - 1.0) < 1e-3:
        return w
    a = os.path.join(WORK, f"_rb_in_{tag}.wav")
    b = os.path.join(WORK, f"_rb_out_{tag}.wav")
    sf.write(a, w, sr, subtype="FLOAT")
    subprocess.run(["rubberband", "-q", "-3", "-T", f"{tempo}", a, b], check=True)
    y, _ = sf.read(b, dtype="float32")
    os.remove(a); os.remove(b)
    return y


def postprocess(w, sr, tempo, tag):
    w = hpf(w, sr)
    w = trim_and_squeeze(w, sr)
    w = stretch(w, sr, tempo, tag)
    g = TARGET_RMS_DB - active_rms_db(w, sr)
    w = w * (10 ** (g / 20))
    pk = np.max(np.abs(w)) + 1e-9
    if pk > 0.97:
        w = w * (0.97 / pk)
    fade = int(0.006 * sr)
    w[:fade] *= np.linspace(0, 1, fade)
    w[-fade:] *= np.linspace(1, 0, fade)
    return w.astype(np.float32)


# ───────────── 主流程 ─────────────
def load_manifest():
    if os.path.exists(MAN):
        return json.load(open(MAN, encoding="utf-8"))
    return {}


def save_manifest(m):
    json.dump(m, open(MAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main(secs):
    import torch
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    sys.path.insert(0, HERE)
    from asr_check import transcribe

    man = load_manifest()
    todo = [x for x in B if x["say"] and (not secs or x["sec"] in secs)]
    todo = [x for x in todo if not (x["id"] in man and man[x["id"]].get("ok") and man[x["id"]].get("say") == x["say"])]
    print(f"{len(todo)} beats to synthesize", flush=True)
    if not todo:
        return
    model = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.bfloat16,
                                          device_map="cpu", attn_implementation="sdpa")
    prompt = model.create_voice_clone_prompt(ref_audio=REF_WAV, ref_text=REF_TEXT, x_vector_only_mode=False)
    for x in todo:
        base_seed = int(hashlib.md5(x["id"].encode()).hexdigest()[:6], 16)
        best = None
        for k in range(MAX_TRIES):
            seed = base_seed + 7919 * k
            torch.manual_seed(seed)
            t0 = time.time()
            wavs, sr = model.generate_voice_clone(text=x["say"], language="Chinese", voice_clone_prompt=prompt)
            w = np.asarray(wavs[0], dtype=np.float32)
            gen_t = time.time() - t0
            rawp = os.path.join(RAW, f"{x['id']}_{k}.wav")
            sf.write(rawp, w, sr)
            f0 = median_f0(w, sr)
            hyp = transcribe(rawp)
            e = cer(x["say"], hyp)
            dur = len(w) / sr
            ok = (F0_LO <= f0 <= F0_HI) and e <= CER_MAX
            score = (0 if F0_LO <= f0 <= F0_HI else 1) * 10 + e + abs(f0 - 95) / 1000
            print(f"{x['id']} try{k} seed={seed} f0={f0:.1f} cer={e:.3f} dur={dur:.1f}s gen={gen_t:.0f}s ok={ok} | {hyp}",
                  flush=True)
            cand = dict(seed=seed, f0=f0, cer=e, asr=hyp, raw=rawp, sr=sr, score=score, ok=ok)
            if best is None or score < best["score"]:
                best = cand
            if ok:
                break
        w, sr = sf.read(best["raw"], dtype="float32")
        y = postprocess(w, sr, TEMPO[x["tempo"]], x["id"])
        outp = os.path.join(OUT, f"{x['id']}.wav")
        sf.write(outp, y, sr)
        man[x["id"]] = dict(say=x["say"], seed=best["seed"], f0=round(best["f0"], 1), cer=round(best["cer"], 3),
                            asr=best["asr"], ok=bool(best["ok"]), dur=round(len(y) / sr, 3), tempo=TEMPO[x["tempo"]],
                            file=outp)
        save_manifest(man)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]])
