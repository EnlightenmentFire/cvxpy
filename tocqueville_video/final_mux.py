"""Mix per 配乐规范.md and mux with the picture track (H.264 + AAC, < 100 MB).

Chain (spec §4): voice sidechains the music; music volume 0.5, -4 dB at 3 kHz, 2 s fade-in;
sidechaincompress threshold 0.02 ratio 10 attack 15 release 500; amix (normalize=0) with the SFX stem;
then two-pass linear loudnorm to I=-16 LUFS, TP=-1.5 dBTP, LRA=11.
usage: python final_mux.py mix            -> stems/mix_final.wav + measurements
       python final_mux.py mux <out.mp4>  -> encode with the picture track
"""
import sys, os, json, re, subprocess
import numpy as np, soundfile as sf

WORK = "/tmp/claude-0/work"
ST = f"{WORK}/stems"
SR = 48000


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def loudnorm_measure(path, extra=""):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"{extra}loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    return json.loads(js)


def mix():
    graph = ("[0:a]aformat=channel_layouts=stereo,asplit=2[v][sc];"
             "[1:a]volume=0.5,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2[m];"
             "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];"
             "[2:a]aformat=channel_layouts=stereo[fx];"
             "[v][duck][fx]amix=inputs=3:duration=first:normalize=0[out]")
    pre = f"{ST}/mix_pre.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{ST}/voice.wav", "-i", f"{ST}/music.wav", "-i", f"{ST}/sfx.wav",
         "-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_f32le", pre])
    # also keep the ducked music alone (for measurement)
    graph_m = ("[0:a]aformat=channel_layouts=stereo[sc];"
               "[1:a]volume=0.5,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2[m];"
               "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{ST}/voice.wav", "-i", f"{ST}/music.wav",
         "-filter_complex", graph_m, "-map", "[duck]", "-c:a", "pcm_f32le", f"{ST}/music_ducked.wav"])
    m = loudnorm_measure(pre)
    ln = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    out = f"{ST}/mix_final.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pre, "-af", ln, "-ar", "48000", "-c:a", "pcm_s24le", out])
    gain = float(m["target_offset"]) + (-16.0 - float(m["input_i"]))
    report(out, gain)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, (float(tp[-1]) if tp else None)


def report(out, gain):
    I, tp = lufs(out)
    print(f"final mix: {I:.1f} LUFS, true peak {tp} dBTP, applied gain {gain:+.1f} dB")
    # narration loudness inside the final mix (voice stem with the same gain)
    v, _ = sf.read(f"{ST}/voice.wav")
    sf.write(f"{ST}/_v_gain.wav", (v * 10 ** (gain / 20)).astype(np.float32), SR, subtype="FLOAT")
    vI, _ = lufs(f"{ST}/_v_gain.wav")
    print(f"narration alone at the same gain: {vI:.1f} LUFS")
    # music vs voice, while speaking and in pauses (>= 1 s)
    md, _ = sf.read(f"{ST}/music_ducked.wav", always_2d=True)
    md = md.mean(1)
    n = int(0.05 * SR)
    L = min(len(v), len(md)) // n * n
    vv = np.sqrt((v[:L].reshape(-1, n) ** 2).mean(1))
    mm = np.sqrt((md[:L].reshape(-1, n) ** 2).mean(1))
    speak = 20 * np.log10(vv + 1e-9) > -35
    sil = np.convolve(~speak, np.ones(20), "same") >= 20
    tl = json.load(open(f"{WORK}/timeline.json"))
    print("per chapter: music level under narration relative to narration (dB)")
    for s in tl["scenes"]:
        a, b = int(s["start"] / 0.05), int(s["end"] / 0.05)
        sp = speak[a:b]
        if sp.sum() < 10 or (mm[a:b][sp] ** 2).mean() < 1e-12:
            print(f"  {s['id']}: (no music)")
            continue
        rel = 10 * np.log10((mm[a:b][sp] ** 2).mean() / (vv[a:b][sp] ** 2).mean())
        ps = sil[a:b]
        pause = 10 * np.log10((mm[a:b][ps] ** 2).mean() / (vv[a:b][sp] ** 2).mean()) if ps.sum() > 5 and (mm[a:b][ps] ** 2).mean() > 0 else float("nan")
        print(f"  {s['id']}: under speech {rel:+.1f} dB, in pauses >=1s {pause:+.1f} dB")


def mux(out):
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    pic = f"{WORK}/video/picture.mp4"
    a_kbps = 128
    v_kbps = int(94 * 1024 * 1024 * 8 / total / 1000 - a_kbps - 8)
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 2.2)}k",
              "-bufsize", f"{v_kbps * 4}k", "-pix_fmt", "yuv420p", "-r", "30", "-g", "300"]
    os.chdir(f"{WORK}/video")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic] + common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", f"{ST}/mix_final.wav"] + common +
        ["-pass", "2", "-c:a", "aac", "-b:a", f"{a_kbps}k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out])
    print(f"{out}: {os.path.getsize(out) / 1024 / 1024:.1f} MB, video {v_kbps} kbps")


if __name__ == "__main__":
    if sys.argv[1] == "mix":
        mix()
    else:
        mux(sys.argv[2])
