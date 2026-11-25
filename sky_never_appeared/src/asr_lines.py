"""Line-by-line ASR read-back: pure voice vs. the finished mix.

The whole-film check (asr_film.py) runs Whisper in long-form mode, where a tiny
change in the input can move segment boundaries and change the transcript. This
check removes that noise. It cuts every narration line out of both soundtracks at
the same timeline position and transcribes each cut on its own. It then compares
both transcripts with the script at the syllable level (toneless pinyin).
Run in the qwen312 venv:
    python asr_lines.py voice.wav final_mix.wav timeline.json report.txt
"""
import sys, json, re, difflib, os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import normalize
from script_data import tts_text

PAD = 0.12


def han(s):
    return re.sub(r'[^一-鿿]', '', normalize(s))


def load16(p):
    w, sr = sf.read(p, dtype='float32')
    if w.ndim == 2:
        w = w.mean(1)
    return resample_poly(w, 16000, sr).astype(np.float32)


def errors(ref, hyp):
    R, H = lazy_pinyin(ref), lazy_pinyin(hyp)
    sm = difflib.SequenceMatcher(a=R, b=H, autojunk=False)
    n = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal')
    return n, len(R)


def main():
    vp, mp, tlj, outp = sys.argv[1:5]
    tl = json.load(open(tlj))
    m = WhisperModel(os.environ.get('ASR_MODEL', 'medium'), device='cpu', compute_type='int8',
                     cpu_threads=int(os.environ.get('ASR_THREADS', '2')))
    tracks = {'voice': load16(vp), 'mix': load16(mp)}
    rows, tot = [], {'voice': 0, 'mix': 0}
    nref = 0
    for ln in tl['lines']:
        ref = han(tts_text(ln['text']))
        a = int(max(0, ln['start'] - PAD) * 16000)
        b = int((ln['start'] + ln['dur'] + PAD) * 16000)
        row = {'id': ln['id'], 'ref': ref}
        for k, w in tracks.items():
            segs, _ = m.transcribe(w[a:b], language='zh', beam_size=5, vad_filter=False,
                                   condition_on_previous_text=False,
                                   initial_prompt='以下是普通话的纪录片旁白。')
            hyp = han(''.join(s.text for s in segs))
            n, nr = errors(ref, hyp)
            row[k], row[k + '_n'] = hyp, n
            tot[k] += n
        nref += nr
        rows.append(row)
        print(f"{row['id']:5s} voice {row['voice_n']:2d}  mix {row['mix_n']:2d}", flush=True)
    worse = [r for r in rows if r['mix_n'] > r['voice_n']]
    better = [r for r in rows if r['mix_n'] < r['voice_n']]
    out = [f'line-by-line ASR, {len(rows)} narration lines, {nref} reference syllables',
           f"syllable errors  pure voice: {tot['voice']} ({tot['voice'] / nref:.2%})   "
           f"final mix: {tot['mix']} ({tot['mix'] / nref:.2%})",
           f'lines where the mix reads worse than the pure voice: {len(worse)}; better: {len(better)}', '']
    for r in rows:
        if r['voice_n'] or r['mix_n']:
            out.append(f"{r['id']}  voice {r['voice_n']}  mix {r['mix_n']}")
            out.append(f"   script: {r['ref']}")
            if r['voice_n']:
                out.append(f"   voice : {r['voice']}")
            if r['mix_n']:
                out.append(f"   mix   : {r['mix']}")
    open(outp, 'w').write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
