"""Opening sound hook: a qing (磬) strike blended with a soft rising electronic hum (EEG lab)."""
import sys, numpy as np, soundfile as sf
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from music import qing, reverb, SR
def hook(dur=6.0):
    n = int(dur*SR); t = np.arange(n)/SR
    q = np.zeros(n); s = qing(523.25, dur=dur, amp=0.9); q[:len(s)] = s[:n]
    # electrodes lighting: soft ascending blips (0.1-1.2s), then a smooth gamma 'hum' swelling
    bl = np.zeros(n)
    for k in range(8):
        i = int((0.05 + 0.1*k)*SR); m = int(0.06*SR)
        tt = np.arange(m)/SR
        bl[i:i+m] += 0.05*np.sin(2*np.pi*(880+90*k)*tt)*np.exp(-tt/0.015)
    hum = 0.05*np.sin(2*np.pi*40*t)*np.sin(2*np.pi*80*t+0.3) * np.clip((t-1.2)/1.2, 0, 1)*np.clip((dur-t)/1.5, 0, 1)
    y = reverb(q + bl + hum, rt=3.0, mix=0.3)
    return y / np.max(np.abs(y)) * 0.9
if __name__ == '__main__':
    y = hook(); sf.write(sys.argv[1], np.stack([y, y], 1).astype(np.float32), SR)
