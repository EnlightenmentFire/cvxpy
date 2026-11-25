# -*- coding: utf-8 -*-
"""全片导出：画面渲一次 → 两条音轨（MusicGen 配乐版 / 无配乐版）→ 两个 mp4。
用法：python3 export_final.py OUTDIR [--video-only | --audio-only] [--crf N]
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
import skia

from compose import build_timeline, load_manifests, render
from mix_spec import build_stems, mix
from render_lib import W, H, FPS

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
NAME = "组织里的权力_不敢说的那句话"


def render_video(tl, total, path, crf):
    n = int(round(total * FPS))
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-maxrate", "1500k",
                            "-bufsize", "3000k", "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "animation",
                            "-g", "60", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    surf, surf2 = skia.Surface(W, H), skia.Surface(W, H)
    t0 = time.time()
    for k in range(n):
        render(tl, k / FPS, surf, surf2)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        enc.stdin.write(np.ascontiguousarray(arr[:, :, :3]).tobytes())
        if k % 1800 == 0:
            print(f"video frame {k}/{n}  {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print(f"video done in {time.time() - t0:.0f}s", flush=True)


def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest",
                    "-movflags", "+faststart", out], check=True)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    crf = int(sys.argv[sys.argv.index("--crf") + 1]) if "--crf" in sys.argv else 22
    m, g = load_manifests(WORK)
    tl, total = build_timeline(m, g)
    missing = [e["id"] for e in tl if e["say"] and e["id"] not in m]
    if missing:
        raise SystemExit(f"缺少配音：{missing}")
    print(f"total {total / 60:.2f} min, {len(tl)} entries", flush=True)
    video = os.path.join(WORK, "video_only.mp4")
    if "--audio-only" not in sys.argv:
        render_video(tl, total, video, crf)
    if "--video-only" in sys.argv:
        return
    rep = {}
    voice, sfx, music = build_stems(tl, 0.0, total, m, g, WORK, with_music=True)
    a_music = os.path.join(WORK, "mix_musicgen.wav")
    a_plain = os.path.join(WORK, "mix_nomusic.wav")
    rep["musicgen"] = mix(voice, sfx, music, a_music, WORK, tag="mg")
    rep["nomusic"] = mix(voice, sfx, music * 0, a_plain, WORK, tag="nm", calibrate=False)
    import soundfile as sf
    sf.write(os.path.join(WORK, "voice_only.wav"), voice, 48000)
    json.dump(rep, open(os.path.join(WORK, "mix_report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1), flush=True)
    mux(video, a_music, os.path.join(outdir, f"{NAME}_配乐版.mp4"))
    mux(video, a_plain, os.path.join(outdir, f"{NAME}_无配乐版.mp4"))
    for f in sorted(os.listdir(outdir)):
        p = os.path.join(outdir, f)
        print(f, f"{os.path.getsize(p) / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
