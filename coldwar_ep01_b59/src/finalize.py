"""Final encode (2-pass H.264, size-targeted) + mux + whole-film checks.

  python finalize.py encode OUT.mp4 [TARGET_MB]
  python finalize.py check OUT.mp4          # (qwen312 venv) ASR read-back of the whole mix + loudness
"""
import json
import os
import re
import subprocess
import sys

SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
EDIT = os.path.join(SCR, "edit")


def probe_duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def encode(out, target_mb=93.0, audio_kbps=128):
    pic = os.path.join(EDIT, "picture.mp4")
    mix = os.path.join(EDIT, "mix.wav")
    dur = probe_duration(pic)
    total_kbps = target_mb * 8 * 1024 / dur  # MiB -> kbit
    v_kbps = int(total_kbps - audio_kbps - 12)  # container overhead margin
    print(f"duration {dur:.1f}s -> video {v_kbps} kbps")
    x264 = "aq-mode=3:aq-strength=0.9:deblock=-1,-1:keyint=120:min-keyint=30:rc-lookahead=60"
    common = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
              "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 2.2)}k", "-bufsize", f"{int(v_kbps * 4)}k",
              "-x264-params", x264, "-r", "30"]
    log = os.path.join(EDIT, "x264pass")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pic] + common +
                   ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pic, "-i", mix] + common +
                   ["-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ar", "48000",
                    "-ac", "2", "-shortest", "-movflags", "+faststart", out], check=True)
    size = os.path.getsize(out) / 1024 / 1024
    print(f"{out}: {size:.1f} MiB, {probe_duration(out):.1f}s")


def check(out):
    sys.path.insert(0, os.path.dirname(__file__))
    import numpy as np
    import soundfile as sf
    import voiceqc as Q
    wav = os.path.join(EDIT, "final_audio_16k.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-ac", "1", "-ar", "16000", wav], check=True)
    x, sr = sf.read(wav, dtype="float32")
    heard = Q.asr(x, sr)
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lines = json.load(open(os.path.join(ROOT, "audio/full/lines.json")))
    expected = "".join(ln["tts"] for ln in lines)
    ser = Q.syllable_error_rate(expected, heard)
    diff = Q.diff_report(expected, heard)
    lufs = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", lufs)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lufs)
    rep = {"asr_syllable_error_rate": round(float(ser), 4), "diff": diff, "asr_text": heard,
           "integrated_lufs": m[-1] if m else None, "true_peak_dbfs": p[-1] if p else None}
    json.dump(rep, open(os.path.join(EDIT, "final_check.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "asr_text"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "encode":
        encode(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 93.0)
    else:
        check(sys.argv[2])
