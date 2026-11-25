# ASR 回读：Whisper small 逐段转写，按拼音（不计声调）对比旁白稿
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import librosa
from difflib import SequenceMatcher
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
from script_data import S
A = sys.argv[1]
only = set(int(v) for v in sys.argv[2].split(',')) if len(sys.argv) > 2 else None
man = json.load(open(os.path.join(A, 'manifest.json')))
m = WhisperModel('small', device='cpu', compute_type='int8')
def py(s):
    s = re.sub(r'[^一-鿿0-9]', '', s)
    return lazy_pinyin(s)
rows = []
for e in man:
    if e.get('chap') or (only and e['i'] not in only):
        continue
    ref = S[e['i']].get('tts') or S[e['i']]['t']
    y, _ = librosa.load(e['file'], sr=16000)
    segs, _ = m.transcribe(y, language='zh', initial_prompt='以下是普通话的历史解说。', beam_size=5)
    hyp = ''.join(s.text for s in segs)
    r, h = py(ref), py(hyp)
    sim = SequenceMatcher(None, r, h).ratio()
    rows.append((sim, e['i'], S[e['i']]['t'], hyp))
    print(f"{e['i']:3d} {sim:.2f} | {S[e['i']]['t']} | {hyp}", flush=True)
rows.sort()
print('\n=== lowest ===')
for r in rows[:25]:
    print(f"{r[1]:3d} {r[0]:.2f} | {r[2]} | {r[3]}")
print('mean', sum(r[0] for r in rows) / len(rows))
