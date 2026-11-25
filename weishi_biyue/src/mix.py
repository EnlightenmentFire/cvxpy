# -*- coding: utf-8 -*-
"""旁白 + 配乐混音（按《配乐规范》的 ffmpeg 链）并自检。

  音乐: volume → 3kHz 削 4dB → 0.3s 淡入 → 以旁白为侧链压缩（有旁白时自动压低、停顿时回升）
  总线: amix → 两遍 loudnorm（-16 LUFS / -1.5 dBTP，线性）
用法: python mix.py voice.wav music.wav out.wav [music_volume]
"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

SR = 48000


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def chain(vol):
    return (f"[0:a]aformat=channel_layouts=stereo,apad=whole_dur={{dur}},asplit=2[v][sc];"
            f"[1:a]volume={vol},equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=0.3:curve=qsin[m];"
            f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=10:release=300[duck]")


def frames_rms(x, win=0.05):
    n = int(win * SR)
    m = len(x) // n
    f = x[: m * n].reshape(m, n, -1)
    return 10 * np.log10((f ** 2).mean((1, 2)) + 1e-12)


def main(voice, music, out, vol=0.6):
    dur = sf.info(music).duration
    c = chain(vol).replace("{dur}", f"{dur:.4f}")
    # 单独导出压低后的音乐和旁白，用来量「有旁白时音乐比人声低多少」
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music, "-filter_complex",
         c + ";[duck]anull[mo];[v]anull[vo]", "-map", "[mo]", "-ar", str(SR), out + ".duck.wav",
         "-map", "[vo]", "-ar", str(SR), out + ".voice.wav"])
    pre = c + ";[v][duck]amix=inputs=2:duration=longest:normalize=0"
    r = run(["ffmpeg", "-y", "-hide_banner", "-i", voice, "-i", music, "-filter_complex",
             pre + ",loudnorm=I=-16:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"])
    js = r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1]
    m = json.loads(js)
    ln = (f"loudnorm=I=-16:TP=-2.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music, "-filter_complex",
         pre + "," + ln + ",aresample=48000", "-ar", str(SR), "-c:a", "pcm_s24le", out])
    # ---- 自检
    v, _ = sf.read(out + ".voice.wav")
    d, _ = sf.read(out + ".duck.wav")
    rv, rd = frames_rms(v), frames_rms(d)
    L = min(len(rv), len(rd))
    rv, rd = rv[:L], rd[:L]
    act = rv > rv.max() - 30
    gap = rv[act] - rd[act]
    mm = json.loads(run(["ffmpeg", "-hide_banner", "-i", out, "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr.split("[Parsed_loudnorm")[-1].split("\n", 1)[1])
    rep = dict(music_volume=vol, voice_over_music_db_median=round(float(np.median(gap)), 1),
               voice_over_music_db_p10=round(float(np.percentile(gap, 10)), 1),
               integrated_lufs=float(mm["input_i"]), true_peak_dbtp=float(mm["input_tp"]), lra=float(mm["input_lra"]))
    print(json.dumps(rep))
    return rep


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 0.6)
