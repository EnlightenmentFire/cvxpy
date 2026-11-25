"""混音 + 封装。
  底乐比人声低 MUSIC_REL dB（静态），旁白期间再侧链压低约 3 dB（停顿处自然回升）；
  两遍 loudnorm 到 -15 LUFS / -1.5 dBTP；aresample=async=1；音频裁到与视频同长。
usage: python mix.py VIDEO_SILENT.mp4 OUT.mp4 [--nomusic]
"""
import sys, os, re, json, subprocess
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
MUSIC_REL = float(os.environ.get("MUSIC_REL", -20.0))
I, TP = -15.0, -1.5


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def lufs(path, extra=""):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", (extra + "," if extra else "") + "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1])


def dur(path, stream="v:0"):
    r = run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration", "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def main():
    vid, out = sys.argv[1], sys.argv[2]
    nomusic = "--nomusic" in sys.argv
    V, M, S = f"{WORK}/voice.wav", f"{WORK}/music.wav", f"{WORK}/sfx.wav"
    lv, lm = lufs(V), lufs(M)
    gm = (lv + MUSIC_REL) - lm
    print(f"voice {lv:.1f} LUFS, music {lm:.1f} LUFS -> music gain {gm:+.1f} dB")
    T = dur(vid)
    pre = f"{WORK}/premix{'_nm' if nomusic else ''}.wav"
    if nomusic:
        fc = ("[0:a]aresample=async=1[v];[2:a]volume=0.55[s];"
              "[v][s]amix=inputs=2:normalize=0:duration=longest[mx]")
    else:
        fc = (f"[0:a]aresample=async=1,asplit=2[v][key];[1:a]volume={gm:.2f}dB[m0];"
              "[m0][key]sidechaincompress=threshold=0.02:ratio=3:attack=40:release=700:makeup=1[m];"
              "[2:a]volume=0.55[s];[v][m][s]amix=inputs=3:normalize=0:duration=longest[mx]")
    run(["ffmpeg", "-v", "error", "-y", "-i", V, "-i", M, "-i", S, "-filter_complex", fc + f";[mx]atrim=0:{T:.3f},apad=whole_dur={T:.3f}[o]",
         "-map", "[o]", "-ar", "48000", pre])
    # loudnorm 两遍
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", pre, "-filter_complex", f"[1:a]{ln},aresample=48000:async=1[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", f"{T:.3f}", out])
    dv, da = dur(out, "v:0"), dur(out, "a:0")
    print(f"{out}: video {dv:.3f}s audio {da:.3f}s diff {abs(dv-da):.3f}s; LUFS {lufs(out):.1f}; size {os.path.getsize(out)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
