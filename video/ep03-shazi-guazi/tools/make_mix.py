"""Self-synthesised music + SFX, ducked under narration. Usage: python tools/make_mix.py <dir with timeline.json + narration.wav>
Everything here is generated with numpy (Karplus-Strong plucks, sine bass, noise percussion): no third-party audio."""
import sys, json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly, fftconvolve
D = sys.argv[1] if len(sys.argv) > 1 else 'build'
TL = json.load(open(f'{D}/timeline.json'))
SR = 48000
total = TL['total']; N = int(total*SR)
rng = np.random.default_rng(3)
L = TL['lines']; SEC = TL['secs']
def cw(lid, word, nth=0):
    seen = 0
    for ch in L[lid]['chunks']:
        i = ch['t'].find(word)
        while i >= 0:
            if seen == nth: return ch['s'] + (ch['e']-ch['s'])*i/max(1, len(ch['t']))
            seen += 1; i = ch['t'].find(word, i+1)
    return L[lid]['s']
c = lambda lid: L[lid]['s']; ce = lambda lid: L[lid]['e']

def midi(n): return 440*2**((n-69)/12)
def pluck(f, dur, bright=0.5, damp=0.996):
    n = int(SR/f); m = int(dur*SR)
    buf = rng.uniform(-1, 1, n)
    # lowpass the excitation for a softer, ruan-like tone
    k = int(1 + (1-bright)*6); buf = np.convolve(buf, np.ones(k)/k, 'same')
    out = np.empty(m)
    reps = m//n + 1; cur = buf
    chunks = []
    for _ in range(reps):
        chunks.append(cur); cur = damp*0.5*(cur + np.roll(cur, 1))
    out = np.concatenate(chunks)[:m]
    env = np.minimum(1, np.arange(m)/(0.004*SR)) * np.exp(-np.arange(m)/(dur*0.45*SR))
    return out*env
def sine_bass(f, dur):
    t = np.arange(int(dur*SR))/SR
    return (np.sin(2*np.pi*f*t) + 0.25*np.sin(4*np.pi*f*t))*np.minimum(1, t/0.012)*np.exp(-t/(dur*0.5))
def block(f=950, dur=0.09):
    t = np.arange(int(dur*SR))/SR
    return (np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*f*1.52*t))*np.exp(-t/0.018)
def shaker(dur=0.05):
    x = rng.normal(0, 1, int(dur*SR)); sos = butter(2, [5000, 11000], 'bp', fs=SR, output='sos')
    return sosfilt(sos, x)*np.exp(-np.arange(len(x))/(0.012*SR))
def thump(f=62, dur=0.5):
    t = np.arange(int(dur*SR))/SR
    return np.sin(2*np.pi*(f + 40*np.exp(-t/0.03))*t)*np.exp(-t/0.12) + 0.25*rng.normal(0, 1, len(t))*np.exp(-t/0.004)

mel = np.zeros(N+SR*4); bas = np.zeros(N+SR*4); perc = np.zeros(N+SR*4); pad = np.zeros(N+SR*4); sfx = np.zeros(N+SR*4)
def add(buf, t, x, g=1.0):
    i = int(t*SR)
    if i < 0 or i >= N: return
    buf[i:i+len(x)] += g*x[:len(buf)-i]

# ---- arrangement ----
BPM = 92; beat = 60/BPM; e8 = beat/2; bar = 4*beat
D4, E4, Fs4, A4, B4, D5, E5, A3, B3 = 62, 64, 66, 69, 71, 74, 76, 57, 59
MOTIFS = [
    [A4, None, B4, A4, Fs4, None, E4, None, D4, None, E4, Fs4, A4, None, None, None],
    [B4, None, D5, B4, A4, None, Fs4, None, E4, None, Fs4, E4, D4, None, None, None],
    [Fs4, None, A4, None, B4, A4, Fs4, None, E4, None, D4, None, E4, None, None, None],
    [D5, None, B4, A4, B4, None, A4, Fs4, E4, None, Fs4, None, D4, None, None, None],
]
SPARSE = [
    [A4, None, None, None, Fs4, None, None, None, E4, None, None, None, D4, None, None, None],
    [B3, None, None, None, D4, None, None, None, E4, None, None, None, None, None, None, None],
]
BASS = [38, 38, 35, 43]  # D2 D2 B1 G2 (per 2 bars)
def mode_at(t):
    s = SEC
    if t < L['c3']['e'] + 0.6: return 'open'
    if t < s['s2']['n'] - 0.2: return 'title'
    if t < s['s3']['s']: return 'groove'
    if t < s['s4']['s']: return 'sparse'
    if t < s['s5']['s']: return 'groove'
    if t < s['s6']['s']: return 'groove2'
    if t < s['s7']['s']: return 'wait'
    return 'still'
nb = int(total/(2*bar)) + 1
for k in range(nb):  # each k = 2 bars (16 eighths)
    t0 = k*2*bar; m = mode_at(t0 + 0.01)
    if m == 'still': continue
    if m == 'open':
        if k % 2 == 0: add(bas, t0, sine_bass(midi(38), 2.6), 0.5)
        for j, n in enumerate([D4, None, None, None, None, None, None, None, A3, None, None, None, None, None, None, None]):
            if n: add(mel, t0 + j*e8, pluck(midi(n), 2.2, 0.35), 0.5)
        continue
    mot = (SPARSE[k % 2] if m in ('sparse', 'wait') else MOTIFS[k % 4])
    for j, n in enumerate(mot):
        if n is None: continue
        tt = t0 + j*e8 + rng.normal(0, 0.004)
        add(mel, tt, pluck(midi(n), 1.5 if m in ('sparse', 'wait') else 0.9, 0.55), 0.62 + 0.1*(j % 4 == 0))
        if m in ('title', 'groove2') and j % 8 == 0: add(mel, tt, pluck(midi(n-12), 1.2, 0.4), 0.3)
    b = BASS[k % 4]
    for j in ([0, 8] if m in ('sparse', 'wait') else [0, 6, 8, 14]):
        add(bas, t0 + j*e8, sine_bass(midi(b if j < 8 else (b+7 if b != 43 else 45)), 0.9), 0.55 if j % 8 == 0 else 0.32)
    if m in ('groove', 'groove2', 'title'):
        for j in [4, 12]: add(perc, t0 + j*e8, block(), 0.22)
        for j in range(16): add(perc, t0 + j*e8, shaker(), 0.05 + 0.04*(j % 2) + (0.03 if m == 'groove2' else 0))
    if m == 'wait':
        for j in [0, 4, 8, 12]: add(perc, t0 + j*e8, block(1250, 0.05), 0.12)   # clock-like tick
# drone for S7/S8 and cold open
t = np.arange(N)/SR
def win(a, b, fi=1.5, fo=1.5): return np.clip((t-a)/fi, 0, 1)*np.clip((b-t)/fo, 0, 1)
dr = (np.sin(2*np.pi*midi(38)*t) + 0.6*np.sin(2*np.pi*midi(45)*t + 0.3) + 0.25*np.sin(2*np.pi*midi(50)*t))*(0.8 + 0.2*np.sin(2*np.pi*0.13*t))
pad[:N] += dr*0.16*win(SEC['s7']['s'], total - 0.9, 2.0, 1.2) + dr*0.10*win(0, L['c3']['e'] + 1.0, 0.8, 1.2)
# S8 single plucks, S7 chapter pluck
for lid, n in [('h1', D4), ('h2', A3), ('h3', D4)]:
    add(mel, c(lid) - 0.25, pluck(midi(n), 3.0, 0.35), 0.6); add(mel, c(lid) - 0.25, pluck(midi(n-12), 3.0, 0.3), 0.4)
add(mel, SEC['s7']['s'] + 0.15, pluck(midi(D4), 3.0, 0.35), 0.6); add(mel, SEC['s7']['s'] + 0.15, pluck(midi(50-12), 3.5, 0.3), 0.5)
add(mel, ce('g8') + 1.1, pluck(midi(A3), 3.0, 0.3), 0.35)
# chapter thumps
for sid in ['s2', 's3', 's4', 's5', 's6', 's7']: add(sfx, SEC[sid]['s'] + 0.08, thump(), 0.5)
# stamp / slam hits
hits = [(cw('c1', '7') - 0.2, 0.25), (cw('c2', '8') - 0.05, 0.5), (cw('a4', '7') - 0.2, 0.35), (cw('a14', '七上八下') - 0.1, 0.45), (cw('b3', '资本主义尾巴') - 0.05, 0.4),
        (cw('b4', '投机倒把') - 0.1, 0.45), (cw('f6', '先不动') - 0.1, 0.45), (cw('e1', '贴了') - 0.2, 0.3)]
for tt, g in hits: add(sfx, tt, thump(75, 0.35), g)
# wok: sizzle + spatula scrapes during b6 scene
w0, w1 = c('b6') - 0.2, c('b7') - 0.1
n = int((w1-w0)*SR); nz = rng.normal(0, 1, n)
siz = sosfilt(butter(2, [3500, 9000], 'bp', fs=SR, output='sos'), nz)
lfo = 0.6 + 0.4*np.abs(sosfilt(butter(1, 6, 'lp', fs=SR, output='sos'), rng.normal(0, 1, n)))/0.02
siz *= np.clip(lfo, 0, 1.5)*np.clip(np.arange(n)/(0.5*SR), 0, 1)*np.clip((n-np.arange(n))/(0.6*SR), 0, 1)
add(sfx, w0, siz, 0.035)
per = np.pi/2.6
for k in range(int((w1-w0)/per)):
    m = int(0.32*SR); x = rng.normal(0, 1, m)
    x = sosfilt(butter(2, [1400, 4200], 'bp', fs=SR, output='sos'), x) + 0.5*sosfilt(butter(2, [2900, 3300], 'bp', fs=SR, output='sos'), x)
    env = np.sin(np.pi*np.arange(m)/m)**1.5
    add(sfx, w0 + 0.4 + k*per, x*env, 0.10)
    for j in range(5): add(sfx, w0 + 0.55 + k*per + j*0.035 + rng.uniform(0, .02), shaker(0.03), 0.10)   # seeds rattle

# ---- bus processing ----
def rev(x, wet=0.22, T=1.4):
    m = int(T*SR); ir = rng.normal(0, 1, m)*np.exp(-np.arange(m)/(T*0.22*SR)); ir = sosfilt(butter(2, [300, 5000], 'bp', fs=SR, output='sos'), ir); ir /= np.sqrt((ir**2).sum())
    return x + wet*fftconvolve(x, ir)[:len(x)]
mel = sosfilt(butter(2, 5200, 'lp', fs=SR, output='sos'), mel); mel = rev(mel, 0.3)
perc = rev(perc, 0.15, 0.6)
music = (0.50*mel + 0.50*bas + 0.6*perc + pad)[:N]
music /= max(1e-9, np.abs(music).max()); music *= 0.5
# intro/outro fades
music *= np.clip(t/0.4, 0, 1)*np.clip((total - 0.85 - t)/0.6, 0, 1)
# S7: no rhythm section already; keep extra low during the quote
# ---- narration + ducking ----
nar, sr = sf.read(f'{D}/narration.wav', dtype='float32'); assert sr == 24000
nar = resample_poly(nar, 2, 1)[:N]; nar = np.pad(nar, (0, N-len(nar)))
nar = sosfilt(butter(2, 70, 'hp', fs=SR, output='sos'), nar)
# gentle compression
envn = np.sqrt(sosfilt(butter(1, 12, 'lp', fs=SR, output='sos'), nar**2).clip(0)); thr = 0.12
gain = np.where(envn > thr, (thr + (envn-thr)/2.5)/np.maximum(envn, 1e-9), 1.0); nar = nar*gain
nar /= np.abs(nar).max(); nar *= 0.82
act = (np.abs(nar) > 0.02).astype(float)
# hold 0.45 s then smooth
hold = int(0.45*SR); k = np.ones(hold); act = np.clip(fftconvolve(act, k)[:N], 0, 1)
act = sosfilt(butter(1, 3.0, 'lp', fs=SR, output='sos'), act).clip(0, 1)
duck = 1.0 - 0.74*act           # music at ~26% (-11.7 dB) under voice
q0, q1 = c('g2') - 0.5, ce('g8') + 2.2
duck *= 1 - 0.45*np.clip((t-q0)/1.0, 0, 1)*np.clip((q1-t)/1.0, 0, 1)
mix = nar + music*duck*0.62 + sfx[:N]*(1 - 0.35*act)*0.5
mix = np.tanh(mix*1.05)/1.05
st = np.stack([mix, mix], 1)
sf.write(f'{D}/mix.wav', st.astype(np.float32), SR)
sf.write(f'{D}/music_only.wav', (music*0.62).astype(np.float32), SR)
print('mix ok', total, 'peak', float(np.abs(mix).max()), 'nar rms', float(np.sqrt((nar**2).mean())), 'music rms under vo', float(np.sqrt(((music*duck*0.62)**2).mean())))
