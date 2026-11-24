import sys, parselmouth, numpy as np
def median_f0(path, fmin=60, fmax=300):
    snd = parselmouth.Sound(path)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=fmin, pitch_ceiling=fmax)
    f = p.selected_array['frequency']; f = f[f > 0]
    return float(np.median(f)) if len(f) else float('nan'), float(np.percentile(f, 10)) if len(f) else 0, float(np.percentile(f, 90)) if len(f) else 0
if __name__ == "__main__":
    for a in sys.argv[1:]:
        m, lo, hi = median_f0(a)
        print(f"{a}: median {m:.1f} Hz (p10 {lo:.0f}, p90 {hi:.0f})")
