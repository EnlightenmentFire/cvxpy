"""成片：两遍 loudnorm 到 -15 LUFS / -1.5 dBTP；两遍 x264 压到 100 MB 以内；aresample=async=1 封装；核对音画时长。
usage: python final_mux.py <输出目录> <文件名前缀>
"""
import sys, os, json, subprocess, re

WK = os.environ.get("WORK", "/tmp/claude-0/work")
B = f"{WK}/build"
OUT, NAME = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def run(cmd, **kw):
    print("+", " ".join(cmd[:8]), "...", flush=True)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def loudnorm(src, dst, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", dst])


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    return I, tp


def dur(path, sel):
    r = run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "stream=duration", "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def main():
    loudnorm(f"{B}/mix_full_pre.wav", f"{B}/mix_full.wav")
    loudnorm(f"{B}/mix_nomusic_pre.wav", f"{B}/mix_nomusic.wav")
    vsrc = f"{B}/video_noaudio.mp4"
    T = dur(vsrc, "v:0")
    vk = int(min(900, (95 * 8 * 1024 * 1024 / T - 128000 - 20000) / 1000))
    print("video kbps", vk)
    common = ["-c:v", "libx264", "-preset", os.environ.get("PRESET", "medium"), "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 1.8)}k",
              "-bufsize", f"{vk * 4}k", "-x264-params", "aq-mode=3", "-pix_fmt", "yuv420p", "-r", "25", "-g", "50"]
    os.chdir(B)
    run(["ffmpeg", "-y", "-v", "error", "-i", vsrc, *common, "-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-y", "-v", "error", "-i", vsrc, *common, "-pass", "2", "-an", f"{B}/video_final.mp4"])
    outs = {}
    for tag, wav in (("", "mix_full.wav"), ("_无配乐", "mix_nomusic.wav")):
        o = f"{OUT}/{NAME}{tag}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", f"{B}/video_final.mp4", "-i", f"{B}/{wav}", "-map", "0:v:0", "-map", "1:a:0",
             "-c:v", "copy", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest",
             "-movflags", "+faststart", o])
        dv, da = dur(o, "v:0"), dur(o, "a:0")
        I, tp = measure(o)
        outs[o] = dict(video_s=dv, audio_s=da, diff_s=round(abs(dv - da), 3), lufs=I, true_peak_dbfs=tp,
                       size_mb=round(os.path.getsize(o) / 1e6, 1))
        print(o, outs[o], flush=True)
    json.dump(outs, open(f"{OUT}/mux_report.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
