import parselmouth, sys, numpy as np
for f in sys.argv[1:]:
    s = parselmouth.Sound(f)
    p = s.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v>0]
    print(f"{f}: dur {s.duration:.2f}s median F0 {np.median(v):.1f}Hz  p10 {np.percentile(v,10):.0f} p90 {np.percentile(v,90):.0f}")
