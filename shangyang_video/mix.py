"""混音：旁白 + 配乐（按人声包络压低，压在人声下约 20–24 dB，停顿处略抬）+ 音效；
两遍 loudnorm 到 -15 LUFS / -1.5 dBTP。同时导出无配乐版。
python mix.py -> $WORK/mix_full.wav, $WORK/mix_nomusic.wav, $WORK/mix_report.json
"""
import os, json, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import uniform_filter1d, maximum_filter1d
from render import timeline
from music import INTENS

WK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000


def loudnorm(src, dst, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", dst], check=True)


def main():
    lines, segs, total = timeline()
    n = int(total * SR)
    v, _ = sf.read(f"{WK}/narration_raw.wav"); v = np.pad(v, (0, max(0, n - len(v))))[:n]
    m, _ = sf.read(f"{WK}/music.wav"); m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
    s, _ = sf.read(f"{WK}/sfx.wav"); s = np.pad(s, ((0, max(0, n - len(s))), (0, 0)))[:n]
    meter = pyln.Meter(SR)
    Lv = meter.integrated_loudness(v)
    # 人声活动包络（20 ms 帧）
    hop = int(0.02 * SR)
    fr = v[: n // hop * hop].reshape(-1, hop)
    act = (np.sqrt((fr ** 2).mean(1)) > 10 ** (-45 / 20)).astype(float)
    act = maximum_filter1d(act, size=int(0.6 / 0.02))         # 句内短停顿视为说话
    # 音乐短时响度（400 ms 块，K 加权）
    blk = int(0.4 * SR)
    mm = m.mean(1)
    Lm = []
    for i in range(0, n, blk):
        seg = m[i:i + blk]
        if len(seg) < blk:
            seg = np.pad(seg, ((0, blk - len(seg)), (0, 0)))
        Lm.append(meter.integrated_loudness(seg) if np.abs(seg).max() > 1e-5 else -70)
    Lm = np.array(Lm)
    Lm = uniform_filter1d(np.maximum(Lm, -50), size=8)    # 3.2 s 平滑
    # 目标：随场景强度在 -24…-20 dB 之间，停顿处 +3 dB
    tb = np.arange(len(Lm)) * 0.4
    I = np.ones(len(Lm))
    for sg in segs:
        I[(tb >= sg["start"]) & (tb < sg["end"])] = INTENS.get(sg["sc"], 1)
    rel = np.interp(I, [0, 1, 2, 3], [-24, -23, -21.5, -20])
    actb = np.interp(tb, np.arange(len(act)) * 0.02, act)
    tgt = Lv + rel + 3.0 * (1 - actb)
    gdb = np.clip(tgt - Lm, -30, 12)
    gdb = uniform_filter1d(gdb, size=4)
    g = 10 ** (np.interp(np.arange(n) / SR, tb + 0.2, gdb) / 20)
    mus = m * g[:, None]
    # 音乐与人声实际差（只在说话时测）
    sp = np.repeat(act, hop)[:n] > 0.5 if len(act) * hop >= n else np.pad(np.repeat(act, hop), (0, n))[:n] > 0.5
    rep = {"voice_LUFS": round(Lv, 2)}
    full = v[:, None] * np.ones((1, 2)) + mus + s * 1.0
    nomus = v[:, None] * np.ones((1, 2)) + s * 1.0
    sf.write(f"{WK}/mix_full_pre.wav", full, SR, subtype="FLOAT")
    sf.write(f"{WK}/mix_nomusic_pre.wav", nomus, SR, subtype="FLOAT")
    loudnorm(f"{WK}/mix_full_pre.wav", f"{WK}/mix_full.wav")
    loudnorm(f"{WK}/mix_nomusic_pre.wav", f"{WK}/mix_nomusic.wav")
    # 报告：每章音乐比人声低多少（说话时段）
    chap = {}
    for sg in segs:
        a, b = int(sg["start"] * SR), int(sg["end"] * SR)
        msk = sp[a:b]
        if msk.sum() < SR * 3:
            continue
        lv = meter.integrated_loudness(v[a:b][msk]); lm = meter.integrated_loudness(mus[a:b][msk])
        chap.setdefault(sg["lines"][0]["id"][0], []).append(lm - lv)
    rep["music_minus_voice_dB_by_chapter"] = {k: round(float(np.median(x)), 1) for k, x in chap.items()}
    for nm in ("mix_full", "mix_nomusic"):
        x, _ = sf.read(f"{WK}/{nm}.wav")
        rep[nm + "_LUFS"] = round(meter.integrated_loudness(x), 2)
    json.dump(rep, open(f"{WK}/mix_report.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
