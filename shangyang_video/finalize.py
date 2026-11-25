"""成片：无声画面 + 混音，aresample=async=1，两遍 x264 控制在 100 MB 以内；
ffprobe 核对音视频流时长差 ≤0.1 s；导出有配乐版与无配乐版。
python finalize.py
"""
import os, json, subprocess

WK = os.environ.get("WORK", "/tmp/claude-0/work")
TARGET_MB = float(os.environ.get("TARGET_MB", 93))


def dur(path, stream):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True).stdout.strip()
    return float(r)


def encode(audio, out, vbr):
    src = f"{WK}/video_silent.mp4"
    common = ["-i", src, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{vbr}k",
              "-maxrate", f"{int(vbr * 2.2)}k", "-bufsize", f"{int(vbr * 4)}k", "-pix_fmt", "yuv420p", "-r", "25", "-g", "100",
              "-profile:v", "high", "-movflags", "+faststart"]
    plog = f"{WK}/x264pass"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + common + ["-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + common + ["-pass", "2", "-passlogfile", plog, "-af", "aresample=async=1",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", out], check=True)


if __name__ == "__main__":
    vd = dur(f"{WK}/video_silent.mp4", "v:0")
    vbr = int(TARGET_MB * 8 * 1024 * 1024 / vd / 1000 - 135)
    print("video", vd, "s -> video bitrate", vbr, "kbps")
    rep = {}
    for nm, aud in [("full", "mix_full.wav"), ("nomusic", "mix_nomusic.wav")]:
        out = f"{WK}/final_{nm}.mp4"
        encode(f"{WK}/{aud}", out, vbr)
        a, v = dur(out, "a:0"), dur(out, "v:0")
        rep[nm] = dict(size_MB=round(os.path.getsize(out) / 1e6, 2), video_s=v, audio_s=a, diff_s=round(abs(a - v), 3))
        print(nm, rep[nm])
    json.dump(rep, open(f"{WK}/final_report.json", "w"), indent=1)
