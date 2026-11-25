"""混音与封装。

底乐比旁白低约 22 dB（旁白进行时），1 秒以上的停顿处抬 5 dB；包络平滑（起 80 ms / 落 600 ms）。
成片两遍 loudnorm 到 -15 LUFS、真峰值目标 -2.0 dBTP（AAC 编码后约 -1.5）；另出无配乐版（只有旁白，同样 -15 LUFS）。
usage: python mix.py mix                     -> stems/mix_music.wav, stems/mix_voice_only.wav + 电平报告
       python mix.py mux <picture.mp4> <out_dir> <basename>
"""
import sys, os, json, re, subprocess
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
ST = f"{WORK}/stems"
SR = 48000
UNDER = float(os.environ.get("MUSIC_UNDER_DB", 22.0))
PAUSE_LIFT = 5.0


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, (float(tp[-1]) if tp else None)


def loudnorm(src, dst, I=-15.0, TP=-2.0):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", ln, "-ar", "48000", "-c:a", "pcm_s24le", dst])


def mix():
    v, _ = sf.read(f"{ST}/voice.wav")
    m, _ = sf.read(f"{ST}/music.wav", always_2d=True)
    n = min(len(v), len(m))
    v, m = v[:n], m[:n]
    vI, _ = lufs(f"{ST}/voice.wav")
    mI, _ = lufs(f"{ST}/music.wav")
    base = 10 ** ((vI - UNDER - mI) / 20)
    # 旁白活动检测（50 ms 帧）
    hop = int(0.05 * SR)
    fr = v[: n // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    speak = db > db.max() - 38
    # 1 秒以上停顿
    sil = ~speak
    run_len = np.zeros(len(sil), int)
    k = 0
    while k < len(sil):
        if sil[k]:
            j = k
            while j < len(sil) and sil[j]:
                j += 1
            if (j - k) * 0.05 >= 1.0:
                run_len[k + 4:j - 4] = 1  # 两头各留 0.2 s
            k = j
        else:
            k += 1
    g_db = np.where(run_len > 0, PAUSE_LIFT, 0.0)
    # 平滑：起 80 ms，落 600 ms（单极点）
    out = np.zeros_like(g_db)
    cur = g_db[0]
    for i, x in enumerate(g_db):
        c = 0.05 / (0.6 if x < cur else 0.25)
        cur = cur + (x - cur) * min(1, c)
        out[i] = cur
    g = np.repeat(10 ** (out / 20), hop)
    g = np.concatenate([g, np.full(n - len(g), g[-1])])
    g = uniform_filter1d(g, int(0.05 * SR))
    mm = m * (base * g)[:, None]
    # 按场景校准：旁白进行时，底乐 RMS 比旁白低 TARGET dB（场景交界 3 秒交叉过渡）
    TARGET = -float(os.environ.get("MUSIC_REL_DB", 21.0))
    tl0 = json.load(open(f"{WORK}/timeline.json"))
    vv0 = np.sqrt((fr ** 2).mean(1))
    mf0 = mm.mean(1)[: n // hop * hop].reshape(-1, hop)
    ml0 = np.sqrt((mf0 ** 2).mean(1))
    corr = np.ones(n)
    pts_t, pts_g = [], []
    for sc_ in tl0["scenes"]:
        a_, b_ = int(sc_["start"] / 0.05), int(sc_["end"] / 0.05)
        sp_ = speak[a_:b_]
        rel = 10 * np.log10((ml0[a_:b_][sp_] ** 2).mean() / (vv0[a_:b_][sp_] ** 2).mean())
        gdb = TARGET - rel
        pts_t += [sc_["start"] + 1.5, sc_["end"] - 1.5]
        pts_g += [gdb, gdb]
    tt = np.arange(n) / SR
    corr = 10 ** (np.interp(tt, pts_t, pts_g) / 20)
    mm = mm * corr[:, None]
    # 开场声音钩子：第 0 秒的磬抬 8 dB，1.5 秒内回落到正常底乐电平
    hook_db = 8.0 * np.clip(1 - (tt - 0.2) / 1.3, 0, 1)
    mm = mm * (10 ** (hook_db / 20))[:, None]
    mix = np.stack([v, v], 1) + mm
    sf.write(f"{ST}/_pre_music.wav", mix.astype(np.float32), SR, subtype="FLOAT")
    sf.write(f"{ST}/_pre_voice.wav", np.stack([v, v], 1).astype(np.float32), SR, subtype="FLOAT")
    loudnorm(f"{ST}/_pre_music.wav", f"{ST}/mix_music.wav")
    loudnorm(f"{ST}/_pre_voice.wav", f"{ST}/mix_voice_only.wav")
    for p in ("mix_music.wav", "mix_voice_only.wav"):
        I, tp = lufs(f"{ST}/{p}")
        print(f"{p}: {I:.1f} LUFS, true peak {tp} dBTP")
    # 电平报告：底乐相对旁白（旁白进行时 / 1 秒以上停顿）
    vv = np.sqrt((fr ** 2).mean(1))
    mf = mm.mean(1)[: n // hop * hop].reshape(-1, hop)
    ml = np.sqrt((mf ** 2).mean(1))
    tl = json.load(open(f"{WORK}/timeline.json"))
    rep = []
    for s in tl["scenes"]:
        a, b = int(s["start"] / 0.05), int(s["end"] / 0.05)
        sp = speak[a:b]
        under = 10 * np.log10((ml[a:b][sp] ** 2).mean() / (vv[a:b][sp] ** 2).mean())
        ps = run_len[a:b] > 0
        pause = 10 * np.log10((ml[a:b][ps] ** 2).mean() / (vv[a:b][sp] ** 2).mean()) if ps.sum() > 3 else float("nan")
        rep.append(f"  {s['id']:6s} 旁白时底乐 {under:+.1f} dB，停顿处 {pause:+.1f} dB")
    print("底乐相对旁白（RMS）：\n" + "\n".join(rep))
    open(f"{ST}/mix_report.txt", "w").write("\n".join(rep) + "\n")


def mux(pic, out_dir, base):
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    a_kbps = 128
    v_kbps = int(95 * 1024 * 1024 * 8 / total / 1000 - a_kbps - 10)
    os.makedirs(out_dir, exist_ok=True)
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 2)}k", "-bufsize", f"{v_kbps * 4}k",
              "-pix_fmt", "yuv420p", "-r", "25", "-fps_mode", "cfr", "-g", "250", "-profile:v", "high"]
    cwd = os.getcwd()
    os.chdir(f"{WORK}/video")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic] + common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    outs = []
    for tag, wav in (("", "mix_music.wav"), ("_无配乐版", "mix_voice_only.wav")):
        out = os.path.join(out_dir, f"{base}{tag}.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", f"{ST}/{wav}"] + common +
            ["-pass", "2", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", f"{a_kbps}k", "-ar", "48000", "-ac", "2",
             "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-movflags", "+faststart", out])
        outs.append(out)
        print(f"{out}: {os.path.getsize(out) / 1024 / 1024:.1f} MB, video {v_kbps} kbps")
    os.chdir(cwd)
    for o in outs:
        r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,r_frame_rate,width,height", "-of", "json", o])
        st = json.loads(r.stdout)["streams"]
        dv = [float(s["duration"]) for s in st if s["codec_type"] == "video"][0]
        da = [float(s["duration"]) for s in st if s["codec_type"] == "audio"][0]
        print(f"  {os.path.basename(o)}: video {dv:.3f}s audio {da:.3f}s diff {abs(dv - da):.3f}s; {[(s.get('width'), s.get('height'), s.get('r_frame_rate')) for s in st if s['codec_type'] == 'video']}")


if __name__ == "__main__":
    if sys.argv[1] == "mix":
        mix()
    else:
        mux(sys.argv[2], sys.argv[3], sys.argv[4])
