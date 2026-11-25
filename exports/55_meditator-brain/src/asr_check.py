"""ASR read-back: faster-whisper transcribes each line wav; report char error rate per line."""
import sys, json, os, re, difflib
from faster_whisper import WhisperModel
import opencc, soundfile as sf
from scipy.signal import resample_poly
cc = opencc.OpenCC('t2s')
tl = json.load(open(os.path.join(sys.argv[1], 'timeline.json')))
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else 'small', device='cpu', compute_type='int8')
norm = lambda s: re.sub(r'[^一-鿿A-Za-z0-9]', '', cc.convert(s))
rows = []
for e in tl:
    y, sr = sf.read(os.path.join(sys.argv[1], f"line_{e['i']:04d}.wav"), dtype='float32')
    y = resample_poly(y, 1, 3).astype('float32') if sr == 48000 else y
    segs, _ = m.transcribe(y, language='zh', beam_size=5,
                           initial_prompt='以下是普通话的句子。')
    hyp = ''.join(s.text for s in segs)
    a, b = norm(e['text']), norm(hyp)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    rows.append({'i': e['i'], 'ratio': round(r, 3), 'ref': e['text'], 'hyp': cc.convert(hyp)})
    print(e['i'], round(r, 3), flush=True)
json.dump(rows, open(os.path.join(sys.argv[1], 'asr_report.json'), 'w'), ensure_ascii=False, indent=1)
