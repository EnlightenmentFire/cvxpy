# -*- coding: utf-8 -*-
"""渲染一段（或全片）：音频混音 + 逐帧画面 → mp4。
用法：python3 make_segment.py OUT_BASENAME FIRST_BEAT_ID LAST_BEAT_ID [--audio-only] [--crf N]
"""
import os
import subprocess
import sys
import time

import numpy as np
import skia

from audio_mix import SR, build_mix, write_wav
from compose import build_timeline, load_manifests, render
from render_lib import W, H, FPS

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")


def main():
    out, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
    audio_only = "--audio-only" in sys.argv
    crf = 26
    if "--crf" in sys.argv:
        crf = int(sys.argv[sys.argv.index("--crf") + 1])
    m, g = load_manifests(WORK)
    tl, total = build_timeline(m, g)
    i0 = next(k for k, e in enumerate(tl) if e["id"] == first)
    i1 = next(k for k, e in enumerate(tl) if e["id"] == last)
    t0, t1 = tl[i0]["start"], tl[i1]["start"] + tl[i1]["dur"]
    print(f"segment {first}..{last}: {t0:.2f}–{t1:.2f}s ({t1 - t0:.1f}s); full timeline {total / 60:.2f} min", flush=True)
    mix = build_mix(tl, t0, t1, m, g)
    dry = build_mix(tl, t0, t1, m, g, voice_only=True)
    write_wav(out + ".wav", mix)
    write_wav(out + "_voice_dry.wav", dry)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + ".wav", "-c:a", "libmp3lame", "-b:a", "192k",
                    out + ".mp3"], check=True)
    if audio_only:
        return
    n = int(round((t1 - t0) * FPS))
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", out + ".wav",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-tune", "animation", "-c:a", "aac", "-b:a", "128k",
                            "-movflags", "+faststart", "-shortest", out + ".mp4"], stdin=subprocess.PIPE)
    surf, surf2 = skia.Surface(W, H), skia.Surface(W, H)
    t_start = time.time()
    for k in range(n):
        t = t0 + k / FPS
        render(tl, t, surf, surf2)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        enc.stdin.write(np.ascontiguousarray(arr[:, :, :3]).tobytes())
        if k % 300 == 0:
            el = time.time() - t_start
            print(f"frame {k}/{n}  {el:.0f}s elapsed", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", out + ".mp4", f"{time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
