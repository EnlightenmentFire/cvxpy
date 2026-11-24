"""Assemble the ~1 minute voice sample (processed narration, no music)."""
import os, subprocess, sys
import numpy as np, soundfile as sf

GROUPS = [
    ["c_year", "c_ad", "c_apps", "c_bet"],
    ["b_dennis", "b_fut", "b_fut2", "b_long", "b_long2", "b_pit"],
    ["b_quote"],                     # a quotation, read a little slower
    ["r5_line", "r5_pct"],           # "2N", "百分之二"
    ["t_april", "t_turtles"],        # "百分之五十五"
]
SR = 48000

def main(lines_dir, out_base):
    parts = []
    for gi, g in enumerate(GROUPS):
        for k, lid in enumerate(g):
            y, sr = sf.read(os.path.join(lines_dir, lid + ".wav"), dtype="float32")
            assert sr == SR
            parts.append(y)
            parts.append(np.zeros(int((0.32 if k < len(g) - 1 else 0.9) * SR), np.float32))
    x = np.concatenate(parts)
    sf.write(out_base + ".wav", x, SR, subtype="PCM_24")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_base + ".wav", "-c:a", "aac", "-b:a", "192k", out_base + ".m4a"], check=True)
    print(f"{len(x) / SR:.1f}s -> {out_base}.m4a")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
