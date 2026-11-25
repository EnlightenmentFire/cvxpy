"""旁白后处理 + 时间线。

1) 每句：去头尾静音、句内停顿压到 ≤0.38 s、rubberband R3 变速（保共振峰）、50 Hz 高通、统一到 -20 dBFS RMS（语音段）
2) 时间线：句间按脚本 gap 停顿；场景切换处多留 0.5 s；输出 timeline.json、narration.srt、sentences.json/txt、voice.wav
usage: python voice_post.py            （处理全部已合成的句子并建时间线）
"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines, SCENES

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW = f"{WORK}/tts/raw"
OUT = f"{WORK}/tts/proc"
SR = 48000
TEMPO = {"n": float(os.environ.get("TEMPO_N", 1.12)), "q": float(os.environ.get("TEMPO_Q", 1.03))}
MAX_PAUSE = 0.38
TARGET_RMS_DB = -20.0
LEAD = 0.25          # 首帧即开口前的留白（秒）
SCENE_EXTRA = 0.5    # 场景切换额外停顿
TAIL = 6.0           # 最后一句后的尾声（月出云翳）
PUNCT = r"[，。？！：；、“”《》·…\s]"


def frame_db(x, sr, win=0.02):
    n = int(sr * win)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 42, -60)
    voiced = db > thr
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2)
    i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]:
                j += 1
            L = j - k
            keep = min(L, maxf)
            a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n])
            k = j
        else:
            out.append(x[k * n:(k + 1) * n])
            k += 1
    y = np.concatenate(out)
    f = int(0.012 * sr)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, sr, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, TEMPO[d["k"]])
    sos = butter(4, 50, "highpass", fs=SR, output="sos")
    x = sosfiltfilt(sos, x).astype(np.float32)
    db, n = frame_db(x, SR)
    v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    rms = np.sqrt((fr ** 2).mean())
    x = x * (10 ** (TARGET_RMS_DB / 20) / (rms + 1e-9))
    peak = np.abs(x).max()
    if peak > 0.9:
        x = x * 0.9 / peak
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return x


def pauses(x, sr, min_len=0.10):
    """句内停顿（秒）的中心位置列表"""
    db, n = frame_db(x, sr, 0.01)
    thr = db.max() - 32
    sil = db < thr
    res, k = [], 0
    while k < len(sil):
        if sil[k]:
            j = k
            while j < len(sil) and sil[j]:
                j += 1
            if (j - k) * 0.01 >= min_len and k > 0 and j < len(sil):
                res.append((k + j) / 2 * 0.01)
            k = j
        else:
            k += 1
    return res


def chunks(text, maxlen=16):
    """把字幕切成 ≤maxlen 的块（在标点处断），去掉块尾逗号句号"""
    parts = re.findall(r"[^，。？！：；…]+[，。？！：；…]*", text)
    out, cur = [], ""
    for p in parts:
        core = re.sub(PUNCT, "", p)
        if cur and len(re.sub(PUNCT, "", cur)) + len(core) > maxlen:
            out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    res = []
    for c in out:  # 仍超长的硬切
        while len(re.sub(PUNCT, "", c)) > maxlen + 4:
            res.append(c[:maxlen])
            c = c[maxlen:]
        res.append(c)
    return [re.sub(r"[，。；：、]+$", "", c).strip() for c in res if c.strip()]


def fmt(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def build():
    lines = all_lines()
    t = LEAD
    tl, prev_scene = [], None
    voice = []
    for d in lines:
        p = f"{OUT}/{d['id']}.wav"
        if os.path.exists(p) and not os.environ.get("FAKE"):
            x, _ = sf.read(p)
        elif os.environ.get("FAKE"):
            x = np.zeros(int(len(re.sub(PUNCT, "", d["say"])) / (4.6 if d["k"] == "n" else 3.6) * SR), np.float32)
        else:
            raise SystemExit(f"missing {p}")
        if prev_scene and d["scene"] != prev_scene:
            t += SCENE_EXTRA
        prev_scene = d["scene"]
        dur = len(x) / SR
        # 字幕块按字数比例分配，再吸附到句内停顿
        sub = d["sub"]
        for a_, b_ in (("D零", "D0"), ("D一", "D1"), ("D二", "D2"), ("D三", "D3"), ("D四", "D4"), ("二点五米", "2.5 米"),
                       ("八纳秒", "8 纳秒"), ("一九八二年", "1982 年"), ("二零零零年", "2000 年"), ("第一百七十三偈", "第 173 偈")):
            sub = sub.replace(a_, b_)
        cs = chunks(sub)
        n_tot = sum(len(re.sub(PUNCT, "", c)) for c in cs) or 1
        ps = pauses(x, SR)
        bounds, acc = [0.0], 0
        for c in cs[:-1]:
            acc += len(re.sub(PUNCT, "", c))
            est = dur * acc / n_tot
            near = [q for q in ps if abs(q - est) < 0.7]
            bounds.append(min(near, key=lambda q: abs(q - est)) if near else est)
        bounds.append(dur)
        subs = [dict(text=c, start=round(t + bounds[i], 3), end=round(t + bounds[i + 1], 3)) for i, c in enumerate(cs)]
        tl.append(dict(id=d["id"], scene=d["scene"], cue=d["cue"], k=d["k"], say=d["say"], sub=d["sub"],
                       nosub=d.get("nosub", False), start=round(t, 3), end=round(t + dur, 3), subs=subs))
        voice.append((t, x))
        t += dur + d["gap"]
    total = t + TAIL
    # 场景起止
    scenes = []
    for s, name in SCENES:
        ls = [e for e in tl if e["scene"] == s]
        scenes.append(dict(id=s, name=name, start=ls[0]["start"], end=ls[-1]["end"]))
    out = np.zeros(int(total * SR) + SR, np.float32)
    for st, x in voice:
        i = int(round(st * SR))
        out[i:i + len(x)] += x
    out = out[:int(total * SR)]
    os.makedirs(f"{WORK}/stems", exist_ok=True)
    sf.write(f"{WORK}/stems/voice.wav", out, SR, subtype="PCM_24")
    json.dump(dict(total=round(total, 3), lines=tl, scenes=scenes), open(f"{WORK}/timeline.json", "w"), ensure_ascii=False, indent=1)
    # SRT（字幕块）
    k = 1
    with open(f"{WORK}/narration.srt", "w", encoding="utf8") as f:
        for e in tl:
            for s in e["subs"]:
                f.write(f"{k}\n{fmt(s['start'])} --> {fmt(s['end'])}\n{s['text']}\n\n")
                k += 1
    n_ch = sum(len(re.sub(PUNCT, "", e["say"])) for e in tl)
    print(f"total {total:.1f}s ({total / 60:.2f} min); {n_ch} 字; {n_ch / (total - TAIL - LEAD) * 60:.0f} 字/分（含停顿）")
    for s in scenes:
        print(f"  {s['id']:6s} {s['start']:7.1f} - {s['end']:7.1f}")


if __name__ == "__main__":
    if "--timeline-only" not in sys.argv:
        for d in all_lines():
            if os.path.exists(f"{RAW}/{d['id']}.wav"):
                process(d)
    build()
