"""Build voice stem from timeline, mix with music + sfx, loudness-normalize, mux.
usage: python mix.py voice | mix | mux <out.mp4> <with_music:1|0>"""
import sys, os, json, re, subprocess
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d
W = "/tmp/claude-0/work"; ST = f"{W}/stems"; SR = 48000
MUSIC_UNDER = float(os.environ.get("MUSIC_UNDER", -21.0))  # music RMS under speech relative to voice RMS (dB)
PAUSE_LIFT = 4.0
def run(c): return subprocess.run(c, check=True, capture_output=True, text=True)
def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1]); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, (float(tp[-1]) if tp else None)

def voice():
    tl = json.load(open(f"{W}/timeline.json")); T = tl["total"]
    v = np.zeros(int(T * SR) + SR)
    for l in tl["lines"]:
        x, sr = sf.read(f"{W}/tts/proc/{l['id']}.wav"); assert sr == SR
        i = int(l["t0"] * SR); v[i:i + len(x)] += x
    v = v[:int(T * SR)]
    sf.write(f"{ST}/voice.wav", v.astype(np.float32), SR, subtype="FLOAT"); print("voice stem", len(v) / SR)

def rms_db(x): return 10 * np.log10((x ** 2).mean() + 1e-12)

def mix():
    v, _ = sf.read(f"{ST}/voice.wav"); m, _ = sf.read(f"{ST}/music.wav", always_2d=True); fx, _ = sf.read(f"{ST}/sfx.wav", always_2d=True)
    n = len(v); m = m[:n]; fx = fx[:n]
    hop = int(0.05 * SR); L = n // hop * hop
    fr = np.sqrt((v[:L].reshape(-1, hop) ** 2).mean(1))
    act = (20 * np.log10(fr + 1e-9) > -40).astype(float)
    act = np.maximum(act, uniform_filter1d(act, 16) > 0.05)  # bridge short gaps (<~0.8 s)
    act_s = uniform_filter1d(act.astype(float), 10)  # 0.5 s smoothing
    g_env = 10 ** (PAUSE_LIFT * (1 - act_s) / 20)
    g_env = np.repeat(g_env, hop); g_env = np.concatenate([g_env, np.full(n - len(g_env), g_env[-1])])
    spk = np.repeat(act > 0.5, hop); spk = np.concatenate([spk, np.zeros(n - len(spk), bool)])
    vdb = rms_db(v[spk]); mdb = rms_db(m.mean(1)[spk])
    g = 10 ** ((vdb + MUSIC_UNDER - mdb) / 20)
    mm = m * g * g_env[:, None]
    fxx = fx * (10 ** ((vdb - 12 - rms_db(fx.mean(1)[np.abs(fx.mean(1)) > 1e-4])) / 20)) * (0.55 + 0.45 * g_env[:, None] / g_env.max())
    for name, mus in [("mix_music", mm), ("mix_nomusic", 0 * mm)]:
        y = np.stack([v, v], 1) + mus + fxx
        pre = f"{ST}/{name}_pre.wav"; sf.write(pre, y.astype(np.float32), SR, subtype="FLOAT")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
        js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
        ln = ("loudnorm=I=-15:TP=-1.5:LRA=11:linear=true:" f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
        out = f"{ST}/{name}.wav"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pre, "-af", ln, "-ar", "48000", "-c:a", "pcm_s24le", out])
        I, tp = lufs(out); print(f"{name}: {I:.1f} LUFS, TP {tp} dBTP")
    print(f"music under speech: {rms_db(mm.mean(1)[spk]) - vdb:.1f} dB; in pauses: {rms_db(mm.mean(1)[~spk]) - vdb:.1f} dB (rel. speech RMS)")

def mux(out, with_music):
    tl = json.load(open(f"{W}/timeline.json")); total = tl["total"]
    pic = f"{W}/video/picture.mp4"; a = f"{ST}/mix_music.wav" if with_music else f"{ST}/mix_nomusic.wav"
    a_k = 128; v_k = int(92 * 1024 * 1024 * 8 / total / 1000 - a_k - 10)
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_k}k", "-maxrate", f"{int(v_k * 2)}k", "-bufsize", f"{v_k * 4}k",
              "-pix_fmt", "yuv420p", "-r", "25", "-g", "250", "-fps_mode", "cfr"]
    os.makedirs(f"{W}/video/pass", exist_ok=True); os.chdir(f"{W}/video/pass")
    if not os.path.exists("ffmpeg2pass-0.log.mbtree") or os.environ.get("REPASS"):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic] + common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", a] + common + ["-pass", "2", "-c:a", "aac", "-b:a", f"{a_k}k", "-ar", "48000",
         "-af", "aresample=async=1", "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-movflags", "+faststart", out])
    print(out, f"{os.path.getsize(out) / 1e6:.1f} MB", f"video {v_k} kbps")

if __name__ == "__main__":
    {"voice": voice, "mix": mix}.get(sys.argv[1], lambda: mux(sys.argv[2], sys.argv[3] == "1"))()
