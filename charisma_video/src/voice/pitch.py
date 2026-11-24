import parselmouth, numpy as np, sys
def med_f0(path, lo=60, hi=300):
    s=parselmouth.Sound(path)
    p=s.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi)
    f=p.selected_array['frequency']; f=f[f>0]
    return float(np.median(f)) if len(f) else 0.0
if __name__=="__main__":
    for a in sys.argv[1:]: print(a, round(med_f0(a),1))
