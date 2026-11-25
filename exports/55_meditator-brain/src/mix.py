"""Mix narration + self-generated music (ducked ~22 dB under voice) + opening qing hook.
python mix.py VOICE_DIR PLAN.json OUT_DIR  -> mix_music.wav, mix_nomusic.wav (both -15 LUFS, TP<=-1.5)"""
import sys, os, json, subprocess, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import uniform_filter1d
sys.path.insert(0, os.path.dirname(__file__))
from music import compose, qing, SR
from sfx import hook

voice_dir, plan_f, out = sys.argv[1:4]
plan = json.load(open(plan_f)); total = plan['total']; off = plan['vo_offset']
n = int(round(total * SR))
v, sr = sf.read(os.path.join(voice_dir, 'narration.wav'), dtype='float32'); assert sr == SR
if v.ndim > 1: v = v.mean(1)
voice = np.zeros(n, np.float32); i0 = int(off * SR); voice[i0:i0 + len(v)] = v[:n - i0]
meter = pyln.Meter(SR)
bell_ids = ['lutz_intro', 'lazar_intro', 'causal_q', 'altered', 'tanjing', 'ending']
bells = [s['start'] + 0.05 for s in plan['scenes'] if s['id'] in bell_ids]
mus = compose(total, bells)[:n]
if len(mus) < n: mus = np.pad(mus, (0, n - len(mus)))
mus = mus * 10 ** ((-15 - meter.integrated_loudness(mus)) / 20)        # music to -15 LUFS reference
env = np.sqrt(uniform_filter1d(voice.astype(np.float64) ** 2, int(0.05 * SR)))
active = (env > 10 ** (-40 / 20)).astype(np.float64)
active = np.clip(uniform_filter1d(active, int(0.6 * SR)) * 3, 0, 1)   # bridge short gaps between words
g_db = -19.0 - 5.0 * active        # -24 dB under speech, -19 dB in pauses (re: voice reference)
g_db = uniform_filter1d(g_db, int(0.4 * SR))
mus *= 10 ** (g_db / 20)
h = hook(); sfx = np.zeros(n); sfx[:len(h)] = h[:n] * 10 ** (-9 / 20)
# soft qing at the end
q = qing(392.0, dur=6.0, amp=0.5); e0 = int((total - 4.6) * SR); sfx[e0:e0 + len(q)] += q[:n - e0] * 10 ** (-14 / 20)
def finish(x, fn):
    tmp = fn + '.raw.wav'; sf.write(tmp, np.stack([x, x], 1).astype(np.float32), SR)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-y', '-i', tmp, '-af', 'loudnorm=I=-15:TP=-2.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(r[r.rfind('{'):])
    af = (f"loudnorm=I=-15:TP=-2.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', af, '-ar', '48000', fn], check=True); os.remove(tmp)
os.makedirs(out, exist_ok=True)
finish(voice + mus + sfx, os.path.join(out, 'mix_music.wav'))
finish(voice + sfx, os.path.join(out, 'mix_nomusic.wav'))
sf.write(os.path.join(out, 'music_only.wav'), mus.astype(np.float32), SR)
print('voice LUFS', round(meter.integrated_loudness(voice[i0:i0+len(v)]), 1), 'music(ducked) LUFS', round(meter.integrated_loudness(mus), 1))
