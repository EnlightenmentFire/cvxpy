# -*- coding: utf-8 -*-
"""成片自检：
  1) 混音后 ASR 回读，与纯人声逐字/逐拼音比对；
  2) 连播三遍的首尾接缝：电平跳变、样点突变（咔哒）；
  3) 响度 / 真峰值；
  4) 画面：逐帧变化量，找「超过 3 秒完全不动」的段（答案帧除外）。
用法: python qa.py <work> final.mp4 voice.wav timeline.json
"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, sys.argv[1])
from asr import transcribe  # noqa: E402

sys.path.insert(0, __import__("os").path.dirname(__file__))
from voice_build import pinyin_seq  # noqa: E402

SR = 48000
REF = "包围敌人为什么要故意留一个口子一千八百多年前曹操围攻壶关下了一道命令城破之后全部活埋结果城里的人个个拼命打了几个月就是打不下来他的堂弟曹仁劝了一句曹操改了命令没过多久城就降了曹仁劝的是什么围死了人人只能拼命给条活路就没人想死"


def pinyin_err(hyp):
    import difflib
    hyp = hyp.replace("1800", "一千八百")  # ASR 把数字写成阿拉伯数字，不是读错
    a = ["xiang2" if x == "jiang4" else x for x in pinyin_seq(hyp)]
    b = ["xiang2" if x == "jiang4" else x for x in pinyin_seq(REF)]
    sm = difflib.SequenceMatcher(a=b, b=a)
    errs = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    return errs / len(b), [(op, b[i1:i2], a[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]


def main(work, mp4, voice, tl):
    rep = {}
    wav = mp4 + ".qa.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vn", "-ar", str(SR), wav], check=True)
    for name, f in (("voice_only", voice), ("final_mix", wav)):
        hyp = "".join(s.text for s in transcribe(f))
        e, diff = pinyin_err(hyp)
        rep[f"asr_{name}"] = dict(text=hyp, pinyin_error_rate=round(e, 4), diffs=diff)
    # 接缝
    a, _ = sf.read(wav)
    loop = np.concatenate([a, a, a])
    n = len(a)
    w = int(0.1 * SR)
    def rdb(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    jump = float(np.abs(loop[n] - loop[n - 1]).max())
    typical = float(np.percentile(np.abs(np.diff(a, axis=0)).max(1), 99.9))
    rep["loop_seam"] = dict(last_100ms_db=round(rdb(a[-w:]), 1), first_100ms_db=round(rdb(a[:w]), 1),
                            first_300ms_db=round(rdb(a[: 3 * w]), 1),
                            sample_jump_at_seam=round(jump, 4), p999_sample_step=round(typical, 4))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"): r.rindex("}") + 1])
    rep["loudness"] = dict(I=js["input_i"], TP=js["input_tp"], LRA=js["input_lra"])
    # 画面变化
    T = json.load(open(tl))
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp4, "-vf", "scale=270:480,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, 480, 270).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2))
    still = d < 0.02
    runs, i = [], 0
    while i < len(still):
        if still[i]:
            j = i
            while j < len(still) and still[j]:
                j += 1
            if (j - i) / 30 > 3 and i / 30 < T["answer"]:
                runs.append((round(i / 30, 2), round(j / 30, 2)))
            i = j
        else:
            i += 1
    rep["static_runs_over_3s_before_answer"] = runs
    rep["frames"] = int(fr.shape[0])
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


if __name__ == "__main__":
    main(*sys.argv[1:5])
