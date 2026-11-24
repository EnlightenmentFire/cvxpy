"""script.py -> per-line TTS (cached) -> narration.wav + timeline.js"""
import sys, re, json, hashlib, os, importlib, numpy as np, soundfile as sf
sys.path.insert(0, '.'); sys.path.insert(0, 'tools')
ENGINE = os.environ.get('TTS', 'kokoro'); VOICE = os.environ.get('VOICE', 'zm_010'); SPEED = float(os.environ.get('SPEED', '0.95'))
SR = 24000
script = importlib.import_module('script')
SEEDS = getattr(script, 'SEEDS', {})
OUT = os.environ.get('OUT', 'build')
PUNC = '，。；：？！'
def parse(text):
    """-> list of chunks [(display, spoken)] split at punctuation outside braces."""
    toks = re.findall(r'\{([^|}]*)\|([^}]*)\}|(.)', text, flags=re.S)
    chunks = []; d = s = ''
    for dd, ss, ch in toks:
        if ch:
            d += ch; s += ch
            if ch == '/':
                d = d[:-1]; s = s[:-1]
                if d: chunks.append((d + '\u200b', s)); d = s = ''
            elif ch in PUNC: chunks.append((d, s)); d = s = ''
        else: d += dd; s += ss
    if d.strip('”’ '): chunks.append((d, s))
    elif chunks and d: chunks[-1] = (chunks[-1][0]+d, chunks[-1][1]+s)
    # move closing quotes that start a chunk back to previous chunk
    out = []
    for d, s in chunks:
        while out and d and d[0] in '”’》':
            out[-1] = (out[-1][0]+d[0], out[-1][1]+s[0]); d, s = d[1:], s[1:]
        if d: out.append((d, s))
    # merge very short chunks with neighbours (<=4 hanzi) when result <= 17
    merged = []
    for d, s in out:
        if merged and (len(merged[-1][0]) + len(d) <= 15) and merged[-1][0][-1] in '，：；' and not merged[-1][0].endswith('\u200b') :
            merged[-1] = (merged[-1][0]+d, merged[-1][1]+s)
        else: merged.append((d, s))
    return merged
MAN = {}
def tts(text, rate=1.0):
    sp = round(SPEED*rate, 3); seed = SEEDS.get(text, 7)
    key = hashlib.md5(f'{ENGINE}|{VOICE}|{sp}|{seed}|{text}'.encode()).hexdigest()[:16]
    p = f'build/tts/{key}.wav'
    if not os.path.exists(p):
        os.makedirs('build/tts', exist_ok=True)
        if ENGINE == 'kokoro':
            from kokoro_tts import synth
            x = synth(text, VOICE, sp)
        else:
            from cosy_tts import synth
            x = synth(text, VOICE, sp, seed)
            print('gen', len(x)/SR, text[:16], flush=True)
        sf.write(p, x, SR)
    x, sr = sf.read(p, dtype='float32'); assert sr == SR
    MAN[text] = p
    return x
def trim(x, thr=0.012):
    e = np.abs(x); idx = np.where(e > thr)[0]
    if len(idx) == 0: return x
    a = max(0, idx[0]-int(0.03*SR)); b = min(len(x), idx[-1]+int(0.10*SR))
    return x[a:b]
def gaps(x, min_len=0.09, thr=0.02):
    hop = int(0.01*SR); n = len(x)//hop
    rms = np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1)); sil = rms < thr*max(0.2, rms.max()/0.2) if False else rms < 0.018
    out = []; i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            if (j-i)*0.01 >= min_len and i > 0 and j < n: out.append(((i+j)/2*0.01, (j-i)*0.01))
            i = j
        else: i += 1
    return out
def weight(s): return len(re.findall(r'[一-鿿]', s)) + 0.0
t = 0.6  # lead-in
audio = []; lines = {}; subs = []; secs = {}
for sid, title, L in script.SECTIONS:
    secs[sid] = {'title': title, 's': t}
    t += getattr(script, 'PRE', {}).get(sid, 0); secs[sid]['n'] = t
    for lid, text, pause, *opt in L:
        rate = opt[0] if opt else 1.0
        chunks = parse(text)
        spoken = ''.join(s for _, s in chunks)
        x = trim(tts(spoken, rate)); dur = len(x)/SR
        # chunk boundaries
        w = np.array([weight(s) for _, s in chunks]); cum = np.cumsum(w)/w.sum()*dur
        g = gaps(x); bounds = []
        for k in range(len(chunks)-1):
            est = cum[k]; best = None
            for gt, gl in g:
                if abs(gt-est) < 0.9 and (best is None or abs(gt-est) < abs(best-est)): best = gt
            bounds.append(best if best is not None else est)
        bounds = sorted(bounds)
        edges = [0.0] + bounds + [dur]
        cl = []
        for (d, s), a, b in zip(chunks, edges[:-1], edges[1:]):
            disp = d.replace('\u200b','').rstrip('，。；：').strip(); d = d.replace('\u200b','')
            subs.append({'s': round(t+a, 3), 'e': round(t+b, 3), 't': disp, 'line': lid}); cl.append({'s': round(t+a, 3), 'e': round(t+b, 3), 't': d})
        lines[lid] = {'s': round(t, 3), 'e': round(t+dur, 3), 'sec': sid, 'chunks': cl, 'text': ''.join(d for d, _ in chunks)}
        audio.append((t, x)); t += dur + pause
    secs[sid]['e'] = t
total = t + 1.2
out = np.zeros(int(total*SR)+SR, np.float32)
for st, x in audio:
    i = int(st*SR); out[i:i+len(x)] += x
out = out[:int(total*SR)]
sf.write(f'{OUT}/narration.wav', out, SR)
json.dump({'lines': lines, 'subs': subs, 'secs': secs, 'total': round(total, 3)}, open(f'{OUT}/timeline.json', 'w'), ensure_ascii=False, indent=1)
open(f'{OUT}/timeline.js', 'w').write('window.TL=' + json.dumps({'lines': lines, 'subs': subs, 'secs': secs, 'total': round(total, 3)}, ensure_ascii=False) + ';')
json.dump(MAN, open(f'{OUT}/manifest.json', 'w'), ensure_ascii=False, indent=1)
nchar = sum(len(re.findall(r'[一-鿿]', l['text'])) for l in lines.values())
print(f'total {total:.1f}s ({total/60:.2f} min), {len(lines)} lines, {len(subs)} subs, {nchar} hanzi')
for sid, v in secs.items(): print(sid, v['title'], f"{v['s']:.1f}-{v['e']:.1f} ({v['e']-v['s']:.1f}s)")
print('max sub len', max(len(s['t']) for s in subs), [s['t'] for s in subs if len(s['t']) > 17])
