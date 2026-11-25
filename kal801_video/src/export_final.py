# -*- coding: utf-8 -*-
"""全片导出（可断点续跑）：
  1. 混两条音轨：MusicGen 配乐版 / 无配乐版（已存在则跳过）；
  2. 画面按 90 秒一段渲染成独立 mp4（每段以关键帧开头，完成后写 .done 标记，重启后跳过已完成段）；
  3. 无损拼接画面段，再分别封装两版成片。
用法：python3 export_final.py OUTDIR [--crf N] [--redo-audio]
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
import skia
import soundfile as sf

from compose import build_timeline, load_manifests, render
from mix_spec import build_stems, mix
from render_lib import W, H, FPS

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
NAME = "组织里的权力_不敢说的那句话"
CHUNK = 90 * FPS


def render_chunk(tl, k0, k1, path, crf):
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-maxrate", "1500k",
                            "-bufsize", "3000k", "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "animation",
                            "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", path], stdin=subprocess.PIPE)
    surf, surf2 = skia.Surface(W, H), skia.Surface(W, H)
    for k in range(k0, k1):
        render(tl, k / FPS, surf, surf2)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        enc.stdin.write(np.ascontiguousarray(arr[:, :, :3]).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"encode failed: {path}")


def render_video(tl, total, crf, worker=None):
    """worker=(r, N)：只渲染编号 i % N == r 的段，然后返回（并行用）。"""
    n = int(round(total * FPS))
    cdir = os.path.join(WORK, "chunks")
    os.makedirs(cdir, exist_ok=True)
    parts = []
    t0 = time.time()
    for i, k0 in enumerate(range(0, n, CHUNK)):
        k1 = min(n, k0 + CHUNK)
        p = os.path.join(cdir, f"c{i:03d}.mp4")
        parts.append(p)
        if os.path.exists(p + ".done"):
            continue
        if worker and i % worker[1] != worker[0]:
            continue
        render_chunk(tl, k0, k1, p, crf)
        open(p + ".done", "w").write(f"{k0}-{k1}\n")
        print(f"chunk {i} frames {k0}-{k1} done, {time.time() - t0:.0f}s elapsed", flush=True)
    if worker:
        return None
    pending = [p for p in parts if not os.path.exists(p + ".done")]
    if pending:
        raise SystemExit(f"还有未完成的画面段：{pending}")
    lst = os.path.join(cdir, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(WORK, "video_only.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    return out


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
    a_music = os.path.join(WORK, "mix_musicgen.wav")
    a_plain = os.path.join(WORK, "mix_nomusic.wav")
    if "--redo-audio" in sys.argv or not (os.path.exists(a_music) and os.path.exists(a_plain)):
        rep = {}
        voice, sfx, music = build_stems(tl, 0.0, total, m, g, WORK, with_music=True)
        sf.write(os.path.join(WORK, "voice_only.wav"), voice, 48000)
        rep["musicgen"] = mix(voice, sfx, music, a_music, WORK, tag="mg")
        rep["nomusic"] = mix(voice, sfx, music * 0, a_plain, WORK, tag="nm", calibrate=False)
        json.dump(rep, open(os.path.join(WORK, "mix_report.json"), "w"), ensure_ascii=False, indent=1)
        print(json.dumps(rep, ensure_ascii=False, indent=1), flush=True)
    if "--worker" in sys.argv:
        r, N = sys.argv[sys.argv.index("--worker") + 1].split("/")
        render_video(tl, total, crf, (int(r), int(N)))
        return
    video = render_video(tl, total, crf)
    mux(video, a_music, os.path.join(outdir, f"{NAME}_配乐版.mp4"))
    mux(video, a_plain, os.path.join(outdir, f"{NAME}_无配乐版.mp4"))
    for f in sorted(os.listdir(outdir)):
        p = os.path.join(outdir, f)
        print(f, f"{os.path.getsize(p) / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
