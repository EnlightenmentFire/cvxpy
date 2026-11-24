"""Round-trip pronunciation check: Whisper transcribes each TTS line; compare pinyin
(with tones) against the input text and list mismatches. Run in the tts312 venv:
    python asr_check.py <tts_dir>
"""
import sys, os, json, re, difflib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import pinyin, Style

d = sys.argv[1]
meta = json.load(open(os.path.join(d, 'meta.json')))
m = WhisperModel('small', device='cpu', compute_type='int8')


def py(s):
    s = re.sub(r'[^一-鿿]', '', s)
    return [p[0] for p in pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)], s


bad = []
for x in meta:
    w, sr = sf.read(os.path.join(d, x['id'] + '.wav'))
    w = resample_poly(w, 16000, sr).astype(np.float32)
    segs, _ = m.transcribe(w, language='zh', initial_prompt='以下是普通话的句子。')
    hyp = ''.join(s.text for s in segs)
    # whisper writes digits; normalise them the same way as the TTS input
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tts import normalize
    hyp_n = normalize(hyp)
    R, rs = py(x['tts_norm'])
    Hh, hs = py(hyp_n)
    sm = difflib.SequenceMatcher(a=R, b=Hh, autojunk=False)
    err = 1 - sm.ratio()
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            diffs.append(f"{rs[i1:i2]}({' '.join(R[i1:i2])}) -> {hs[j1:j2]}({' '.join(Hh[j1:j2])})")
    flag = '!!' if err > 0.08 else '  '
    print(flag, x['id'], round(err, 3), ' | '.join(diffs)[:300], flush=True)
