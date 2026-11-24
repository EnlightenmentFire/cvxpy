"""逐行合成旁白 -> audio/lines/<voice>/<id>.wav；再拼成 narration.wav 并生成时间轴 render/timeline.js
用法: python tts/synth.py [voice=zm_033] [speed=1.0] [only=id1,id2]"""
import sys, os, json, re, hashlib, numpy as np, soundfile as sf
sys.path.insert(0, 'script'); import script as S
args = dict(a.split('=') for a in sys.argv[1:])
VOICE = args.get('voice', 'zm_033'); SPEED = float(args.get('speed', 1.0)); SR = 24000
ONLY = set(args['only'].split(',')) if 'only' in args else None
OUT = f'audio/lines/{VOICE}_{SPEED}'; os.makedirs(OUT, exist_ok=True)
L = S.lines()
if ONLY: L = [l for l in L if l['id'] in ONLY]
pipe = None; model = None; pack = None
# 读音校正（在音素层面改，逐条人工核对过 G2P 输出）：
PH_FIX = [
 ("ㄧ4ㄐ又3", "ㄧ1ㄐ又3"),            # 年份里的「一九」读 yī，不变调
 ("ㄅㄚ1ㄧ4ㄋ言2", "ㄅㄚ1ㄧ1ㄋ言2"),    # 一九八一年
 ("ㄑㄧ1ㄧ4ㄋ言2", "ㄑㄧ1ㄧ1ㄋ言2"),    # 一九七一年
 ("ㄕ十2ㄧ2ㄐㄝ4", "ㄕ十2ㄧ1ㄐㄝ4"),    # 十一届
 ("ㄧ4ㄑㄧ1", "ㄧ1ㄑㄧ1"),            # 一期（序数）
 ("ㄧ2ㄏㄠ4", "ㄧ1ㄏㄠ4"),            # 一号高炉
 ("ㄨ2/ㄧ4ㄉ又1", "ㄨ2/ㄧ1ㄉ又1"),      # 无一丢失
 ("ㄎㄚ3/我3ㄇㄣ5", "ㄑ压3/我3ㄇㄣ5"),  # 卡（qiǎ）我们
 ("ㄖㄣ2/ㄉㄜ5/ㄅㄚ3", "ㄖㄣ2/ㄉㄟ2/ㄅㄚ3"),  # 花钱的人得（děi）把账
 ("ㄉㄜ2ㄉㄠ4", "ㄉㄜ5ㄉㄠ4"),          # 做得到
 ("ㄕㄤ4ㄒ压5", "ㄕㄤ4ㄒ压4"),          # 四分之一上下（「下」不读轻声，免得含糊）
]
def g2p_fixed(text):
    ps, _ = pipe.g2p(text)
    for a_, b_ in PH_FIX: ps = ps.replace(a_, b_)
    return ps
def synth(text):
    global pipe, model, pack
    from kokoro import KPipeline, KModel
    if pipe is None:
        REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
        model = KModel(repo_id=REPO).eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model); pack = pipe.load_voice(VOICE)
    out = []
    for part in re.split(r'(?<=[。？！；：])', text):
        if not part.strip(): continue
        ps = g2p_fixed(part)
        o = KPipeline.infer(model, ps, pack, SPEED)
        out += [o.audio.numpy(), np.zeros(int(SR * 0.12), np.float32)]
    return np.concatenate(out[:-1])
def silences(w, thr_db=-38, min_len=0.12):
    hop = 240; n = len(w) // hop
    e = np.sqrt((w[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    q = 20 * np.log10(e / (np.abs(w).max() + 1e-9)) < thr_db
    segs = []; i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            if (j - i) * hop / SR >= min_len or i == 0 or j == n: segs.append((i * hop, j * hop))
            i = j
        else: i += 1
    return segs
def tighten(w):
    """裁掉首尾静音；句内过长的停顿压短（保留节奏，不拖沓）"""
    segs = silences(w); out = []; pos = 0; N = len(w)
    for a, b in segs:
        out.append(w[pos:a]); d = (b - a) / SR
        if a == 0 or b >= N - 240: keep = 0.03
        else: keep = d if d <= 0.26 else min(0.26 + 0.25 * (d - 0.26), 0.42)
        k = int(keep * SR); h = k // 2
        out.append(np.concatenate([w[a:a + h], w[b - (k - h):b]]) if k > 0 else np.zeros(0, np.float32)); pos = b
    out.append(w[pos:]); return np.concatenate(out)
for l in L:
    key = hashlib.md5(l['tts'].encode()).hexdigest()[:8]; f = f"{OUT}/{l['id']}_{key}.wav"
    if not os.path.exists(f):
        w = tighten(synth(l['tts'])); sf.write(f, w, SR); print(l['id'], f'{len(w)/SR:.2f}s', flush=True)
    l['wav'] = f
if ONLY: sys.exit()
# ---- timeline ----
PUNC = '，。：；？！、'
def chunks(sub):
    """按标点切字幕，每条不超过 ~19 字"""
    parts = re.findall(r'[^，。：；？！]+[，。：；？！」]*', sub); out = []; cur = ''
    for p in parts:
        if cur and len(re.sub(r'[「」]', '', cur + p)) > 16: out.append(cur); cur = p
        else: cur += p
    if cur: out.append(cur)
    return out
def nchar(t): return len(re.sub(r'[，。：；？！、「」《》\s%]', '', S.clean_tts(t)))
LEAD = 0.7; TITLE = 4.6; CHAP = 1.5
t = LEAD; tl = []; secs = []; buf = []; cur = None
def pad_to(tt):
    n = int(tt * SR) - sum(len(b) for b in buf)
    if n > 0: buf.append(np.zeros(n, np.float32))
for sid, sname, ls in S.SECTIONS:
    if sid == 'title': secs.append(dict(id=sid, name=sname, start=t, end=t + TITLE)); t += TITLE; continue
    st = t
    if sid not in ('cold', 'end'): t += CHAP
    if sid == 'end': t += 0.8
    for (lid, sub, pause, src) in ls:
        l = next(x for x in L if x['id'] == lid); w, _ = sf.read(l['wav'], dtype='float32'); d = len(w) / SR
        pad_to(t); buf.append(w)
        # subtitle chunk timing: proportional to char count, snapped to nearest silence
        cs = chunks(sub); tot = sum(nchar(c) for c in cs) or 1; sil = [((a + b) / 2 / SR) for a, b in silences(w) if a > 0 and b < len(w) - 240]
        acc = 0; bounds = [0.0]
        for c in cs[:-1]:
            acc += nchar(c); g = d * acc / tot
            near = [s for s in sil if abs(s - g) < 0.45]
            bounds.append(min(near, key=lambda s: abs(s - g)) if near else g)
        bounds.append(d)
        subs = [dict(text=re.sub(r'[，。；：]+$', '', c).strip(), start=round(t + bounds[i], 3), end=round(t + bounds[i + 1], 3)) for i, c in enumerate(cs)]
        tl.append(dict(id=lid, sec=sid, start=round(t, 3), end=round(t + d, 3), sub=sub, src=src, subs=subs))
        t += d + pause
    secs.append(dict(id=sid, name=sname, start=round(st, 3), end=round(t, 3)))
END = t + 1.6
pad_to(END); nar = np.concatenate(buf)
os.makedirs('audio/out', exist_ok=True); sf.write('audio/out/narration.wav', nar, SR)
TL = dict(dur=round(END, 3), fps=30, voice=VOICE, sections=secs, lines=tl)
json.dump(TL, open('render/timeline.json', 'w'), ensure_ascii=False, indent=1)
open('render/timeline.js', 'w').write('window.TL=' + json.dumps(TL, ensure_ascii=False) + ';')
print('TOTAL', f'{END:.1f}s = {int(END//60)}:{END%60:04.1f}')
for s in secs: print(f"  {s['id']:8s} {s['start']:6.1f} → {s['end']:6.1f}  ({s['end']-s['start']:.1f}s)")
