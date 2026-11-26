"""Step 4 (ep47): assemble the delivered files from the post-processed takes.

proc/<id>.wav (24 kHz, already trimmed / pause-capped / tempo / 50 Hz HP / -18 dBFS active RMS)
  -> 48 kHz mono line_XXXX.wav (padded with zeros to a whole millisecond so timeline times are exact)
  -> narration.wav: lines 1..113 joined with 0.40 s of silence, no lead-in,
     one overall gain to -15 LUFS integrated, true peak kept <= -1.5 dBTP
  -> timeline.json
usage: python assemble.py <voice_dir> <deliver_dir>
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines  # noqa: E402

SR = 48000
GAP = 0.40
TARGET_LUFS = -15.0
TP_CEIL = -1.5


def ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail).group(1))
    return i, tp, lra


def measure(x):
    fd, p = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(p, x, SR, subtype="FLOAT")
    try:
        return ebur128(p)
    finally:
        os.remove(p)


def tp_limit(x, ceil_db, os_factor=4, release=0.05):
    """Gain-reduce only where the 4x-oversampled (true) peak would exceed ceil_db.
    Smooth look-ahead gain envelope; leaves everything below the ceiling untouched."""
    lim = 10 ** (ceil_db / 20)
    up = resample_poly(x, os_factor, 1)
    pk = np.abs(up).reshape(-1, os_factor).max(axis=1)[: len(x)]
    need = np.minimum(1.0, lim / np.maximum(pk, 1e-9))
    if need.min() >= 1.0:
        return x, 0.0
    # look-ahead: spread each reduction over +-2 ms (min filter), then smooth release
    w = int(0.002 * SR)
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    g = minimum_filter1d(need, size=2 * w + 1)
    g = uniform_filter1d(g, size=w)
    g = np.minimum(g, minimum_filter1d(need, size=2 * w + 1))
    a = np.exp(-1.0 / (release * SR))
    out = g.copy()
    tail = int(8 * release * SR)
    idx = np.flatnonzero(g < 1.0)
    # only walk the neighbourhoods that are actually reduced (plus release tail)
    starts = idx[np.r_[True, np.diff(idx) > tail]]
    ends = idx[np.r_[np.diff(idx) > tail, True]]
    for s0, e0 in zip(starts, ends):
        for i in range(max(1, s0), min(len(out), e0 + tail)):  # release: recover slowly
            if out[i] > out[i - 1]:
                out[i] = out[i - 1] * a + out[i] * (1 - a)
    return (x * out).astype(np.float32), float(20 * np.log10(out.min()))


def main():
    voice, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    lines = all_lines()
    assert len(lines) == 113
    gap = np.zeros(int(round(GAP * SR)), np.float32)
    parts, timeline, t = [], [], 0
    for k, ln in enumerate(lines, 1):
        x, sr = sf.read(os.path.join(voice, "proc", f"{ln['id']}.wav"), dtype="float32")
        if x.ndim > 1:
            x = x.mean(axis=1)
        if sr != SR:
            g = np.gcd(int(sr), SR)
            x = resample_poly(x, SR // g, int(sr) // g).astype(np.float32)
        pad = (-len(x)) % (SR // 1000)
        x = np.concatenate([x, np.zeros(pad, np.float32)])
        fname = f"{ln['id']}.wav"
        sf.write(os.path.join(dst, fname), x, SR, subtype="PCM_24")
        if k > 1:
            parts.append(gap)
            t += len(gap)
        start = t
        parts.append(x)
        t += len(x)
        timeline.append(dict(i=k, text=ln["say"], start=round(start / SR, 3), end=round(t / SR, 3), file=fname))
    y = np.concatenate(parts)

    i0, tp0, _ = measure(y)
    gain_db = TARGET_LUFS - i0
    lim_db = 0.0
    for _ in range(12):
        z = (y * 10 ** (gain_db / 20)).astype(np.float32)
        z, lim_db = tp_limit(z, TP_CEIL - 0.3)
        i1, tp1, lra = measure(z)
        if abs(i1 - TARGET_LUFS) <= 0.05 and tp1 <= TP_CEIL:
            break
        gain_db += TARGET_LUFS - i1
    sf.write(os.path.join(dst, "narration.wav"), z, SR, subtype="PCM_24")
    i2, tp2, lra2 = ebur128(os.path.join(dst, "narration.wav"))
    json.dump(timeline, open(os.path.join(dst, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    info = dict(duration_s=round(len(z) / SR, 3), sample_rate=SR, gap_s=GAP, lines=len(timeline),
                lufs_before=i0, true_peak_before=tp0, gain_db=round(gain_db, 2), max_limiter_gr_db=round(lim_db, 2),
                lufs_integrated=i2, true_peak_dbtp=tp2, lra=lra2)
    json.dump(info, open(os.path.join(dst, "narration_loudness.json"), "w"), indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
