import sys, numpy as np, soundfile as sf, time
sys.path.insert(0, 'tools')
from kokoro_tts import synth, SR
text = "一九八一年，一个中国人做生意，最多只能雇七个人。雇到第八个，就是另一回事了。这条线，是从一百多年前的一道算术题来的。"
voices = sys.argv[1:]
def f0_med(x):
    # crude autocorrelation f0 over frames
    fl = int(0.04*SR); hop = int(0.02*SR); f = []
    for i in range(0, len(x)-fl, hop):
        w = x[i:i+fl]
        if np.sqrt((w**2).mean()) < 0.03: continue
        w = w - w.mean(); ac = np.correlate(w, w, 'full')[fl-1:]
        lo, hi = SR//300, SR//60
        k = lo + np.argmax(ac[lo:hi])
        if ac[k] > 0.4*ac[0]: f.append(SR/k)
    return np.median(f) if f else 0
for v in voices:
    t = time.time(); x = synth(text, v, 0.92)
    sf.write(f'build/aud_{v}.wav', x, SR)
    print(v, f'dur={len(x)/SR:.1f}s f0={f0_med(x):.0f}Hz gen={time.time()-t:.1f}s', flush=True)
