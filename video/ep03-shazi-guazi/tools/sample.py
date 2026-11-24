import sys, re, hashlib, json, numpy as np, soundfile as sf
sys.path.insert(0, '.'); import script
engine, voice, speed, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
ids = sys.argv[5:]
SR = 24000; parts = []; man = {}
for _, _, L in script.SECTIONS:
    for lid, text, pause, *opt in L:
        if lid not in ids: continue
        spoken = re.sub(r'\{[^|}]*\|([^}]*)\}', r'\1', text).replace('/', '')
        sp = round(speed*(opt[0] if opt else 1.0), 3)
        p = 'build/tts/' + hashlib.md5(f'{engine}|{voice}|{sp}|7|{spoken}'.encode()).hexdigest()[:16] + '.wav'
        x, sr = sf.read(p, dtype='float32'); idx = np.where(np.abs(x) > 0.012)[0]; lo = np.where(np.abs(x) > 0.003)[0]; x = x[max(0, idx[0]-720):lo[-1]+1440]
        parts += [x, np.zeros(int(min(pause, 0.7)*SR), np.float32)]; man[spoken] = p
y = np.concatenate([np.zeros(int(0.3*SR), np.float32)] + parts); y = y/np.abs(y).max()*0.85
sf.write(out, y, SR); json.dump(man, open(out + '.json', 'w'), ensure_ascii=False)
print(out, f'{len(y)/SR:.1f}s')
