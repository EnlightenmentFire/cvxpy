"""ASR 回读：faster-whisper small 逐句转写，按无调拼音与稿子比对，列出相似度低的句子。"""
import sys, os, json, re, difflib
sys.path.insert(0, '/tmp/claude-0/work/vid')
from script import BEATS
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
m = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=4)
def py(s): return [p for p in lazy_pinyin(re.sub(r'[^一-鿿0-9]', '', s))]
res = {}; only = sys.argv[1:]
for b in BEATS:
    if only and b['id'] not in only: continue
    p = f"proc/{b['id']}.wav"
    if not os.path.exists(p): continue
    import soundfile as sf, numpy as np
    from scipy.signal import resample_poly
    w, sr = sf.read(p, dtype='float32'); w = resample_poly(w, 1, 3).astype(np.float32)
    segs, _ = m.transcribe(w, language='zh', beam_size=5, vad_filter=False)
    txt = ''.join(s.text for s in segs)
    a, c = py(b['say']), py(txt)
    r = difflib.SequenceMatcher(None, a, c).ratio()
    res[b['id']] = dict(ratio=round(r, 3), asr=txt, ref=b['say'])
    print(b['id'], round(r, 3), txt, flush=True)
json.dump(res, open('asr.json', 'w'), ensure_ascii=False, indent=1)
bad = {k: v for k, v in res.items() if v['ratio'] < 0.85}
print('LOW', len(bad), sorted(bad, key=lambda k: bad[k]['ratio']))
