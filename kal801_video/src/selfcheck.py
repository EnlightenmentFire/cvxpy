# -*- coding: utf-8 -*-
"""导出前自检（《配乐规范》第五条 + 本期规矩）：
  1. ASR：纯人声 / 配乐版 / 手机外放模拟（300 Hz–7 kHz 带通 + 压缩）三者误读率对比；
  2. 响度：两版整体 LUFS、真峰值；
  3. 音乐有没有"突然冒出来"：配乐轨（已侧链）短时响度的突跳位置，是否都落在旁白停顿处；
  4. 高潮段：撞山后静音是否 ≥2 秒、音乐单独出来的 2 秒电平。
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from asr_check import transcribe          # noqa: E402
from compose import build_timeline, load_manifests   # noqa: E402
from mix_spec import short_term_lufs, SR   # noqa: E402
from tts_build import to_tokens          # noqa: E402

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")


def lev(a, b):
    import numpy as _np
    # 拼音 token 编辑距离（行向量化）
    if not a:
        return len(b)
    prev = _np.arange(len(b) + 1)
    vocab = {t: i for i, t in enumerate(set(a) | set(b))}
    bb = _np.array([vocab[t] for t in b])
    for i, t in enumerate(a, 1):
        cur = _np.empty_like(prev)
        cur[0] = i
        sub = prev[:-1] + (bb != vocab[t])
        ins_del = _np.minimum(prev[1:] + 1, sub)
        # 需要顺序依赖的插入：逐元素累积
        cur[1:] = ins_del
        for j in range(1, len(cur)):
            if cur[j - 1] + 1 < cur[j]:
                cur[j] = cur[j - 1] + 1
        prev = cur
    return int(prev[-1])


def cer_text(ref, hyp):
    a, b = to_tokens(ref), to_tokens(hyp)
    return lev(a, b) / max(1, len(a))


def phone_sim(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-af",
                    "highpass=f=300,lowpass=f=7000,acompressor=threshold=-20dB:ratio=3:attack=5:release=80",
                    dst], check=True)


def ebur(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null",
                        "-"], capture_output=True, text=True).stderr
    s = r[r.rindex("Summary:"):]
    return " ".join(s.split())


def main():
    m, g = load_manifests(WORK)
    tl, total = build_timeline(m, g)
    ref = "".join(e["say"] for e in tl if e["say"])
    out = {}
    files = {"纯人声": os.path.join(WORK, "voice_only.wav"), "配乐版": os.path.join(WORK, "mix_musicgen.wav"),
             "无配乐版": os.path.join(WORK, "mix_nomusic.wav")}
    phone = os.path.join(WORK, "_phone_sim.wav")
    phone_sim(files["配乐版"], phone)
    files["配乐版·手机外放模拟"] = phone
    for k, p in files.items():
        hyp = transcribe(p)
        out[k] = dict(cer=round(cer_text(ref, hyp), 4))
        open(os.path.join(WORK, f"_asr_{k}.txt"), "w", encoding="utf-8").write(hyp)
        print(k, out[k], flush=True)
    for k in ("配乐版", "无配乐版"):
        out[k]["loudness"] = ebur(files[k])
    # 音乐轨突跳
    duck = os.path.join(WORK, "_mg_duck.wav")
    if os.path.exists(duck):
        d, _ = sf.read(duck, dtype="float32")
        v, _ = sf.read(os.path.join(WORK, "voice_only.wav"), dtype="float32")
        Lm = short_term_lufs(d, 0.4, 0.1)
        Lv = short_term_lufs(v, 0.4, 0.1)
        jumps = []
        for i in range(10, len(Lm)):
            dj = Lm[i] - Lm[i - 10]           # 1 秒内上升
            if dj > 8 and Lm[i] > -40:
                in_pause = Lv[i] < -40
                jumps.append((round(i * 0.1, 1), round(float(dj), 1), bool(in_pause)))
        merged = []
        for j in jumps:
            if not merged or j[0] - merged[-1][0] > 2:
                merged.append(j)
        out["音乐突跳(>8dB/1s)"] = dict(count=len(merged), not_in_pause=[j for j in merged if not j[2]][:10])
    # 高潮段
    mx, _ = sf.read(files["配乐版"], dtype="float32")
    imp = next(e for e in tl if e["id"] == "s3_37")
    mem = next(e for e in tl if e["id"] == "s3_38")
    a = int((imp["start"] + 1.0) * SR)
    b = int((imp["start"] + imp["dur"]) * SR)
    sil = 20 * np.log10(np.sqrt(np.mean(mx[a:b] ** 2)) + 1e-12)
    c0 = int(mem["start"] * SR)
    c1 = int((mem["start"] + mem["lead"]) * SR)
    alone = short_term_lufs(mx[c0:c1], 0.4, 0.1)
    out["高潮段"] = dict(silence_seconds=round((b - a) / SR + 0.05, 2), silence_rms_dbfs=round(float(sil), 1),
                       music_alone_seconds=round(mem["lead"], 2),
                       music_alone_lufs_median=round(float(np.median(alone)), 1) if len(alone) else None)
    json.dump(out, open(os.path.join(WORK, "selfcheck.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
