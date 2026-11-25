"""Whole-film ASR read-back on the final mix (music included).

Transcribes the finished soundtrack with faster-whisper, drops the stretches that
carry Reagan's original English audio, and compares the rest with the script at the
syllable level (toneless pinyin). Run in the qwen312 venv:
    python asr_film.py final_audio.wav timeline.json report.txt
"""
import sys, json, re, difflib, os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import normalize


def han(s):
    return re.sub(r'[^一-鿿]', '', normalize(s))


def main():
    wav, tlj, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    tl = json.load(open(tlj))
    w, sr = sf.read(wav)
    if w.ndim == 2:
        w = w.mean(1)
    # silence the English clips so they don't pollute the Chinese read-back
    for c in tl['clips']:
        a, b = int(c['start'] * sr), int((c['start'] + c['dur']) * sr)
        w[a:b] = 0
    w16 = resample_poly(w, 16000, sr).astype(np.float32)
    m = WhisperModel(os.environ.get('ASR_MODEL', 'medium'), device='cpu', compute_type='int8')
    segs, _ = m.transcribe(w16, language='zh', initial_prompt='以下是普通话的纪录片旁白。', beam_size=5,
                           vad_filter=True)
    hyp = ''.join(s.text for s in segs)
    ref = ''.join(ln['text'] for ln in tl['lines'])
    from script_data import tts_text
    R, Hh = lazy_pinyin(han(tts_text(ref))), lazy_pinyin(han(hyp))
    rs, hs = han(tts_text(ref)), han(hyp)
    sm = difflib.SequenceMatcher(a=R, b=Hh, autojunk=False)
    err = 1 - sm.ratio()
    lines = [f'whole-film syllable error rate (music included, English clips excluded): {err:.4f}',
             f'reference syllables: {len(R)}, transcript syllables: {len(Hh)}', '', 'differences:']
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            lines.append(f'  {tag:8s} {rs[i1:i2]} -> {hs[j1:j2]}')
    lines += ['', 'transcript:', hyp]
    open(outp, 'w').write('\n'.join(lines))
    print('\n'.join(lines[:60]))


if __name__ == '__main__':
    main()
