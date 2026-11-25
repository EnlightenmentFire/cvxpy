"""Re-record one narration line with the cloned voice, keeping its length.

Used when the per-line ASR read-back flags a word (the voice spec says to re-record
misread lines). It generates several takes with the same voice-clone prompt and keeps
takes whose median pitch is in range and whose read-back contains the required
words. It then picks the take closest to the old length, time-aligns it to the
old length exactly (rubberband, formant-preserving), and checks it again. The new
take has the same length as the old one, so the timeline, subtitles and picture
stay unchanged. Run in the qwen312 venv from the folder that holds design/:
    python qwen_retake.py lines.json design.json meta.json <line_id> <must_words> <out_dir>
"""
import os, sys, json
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qwen_narrate as Q
from tts import normalize

TAKES_PER_BATCH = int(os.environ.get('BATCH', '6'))
BATCHES = int(os.environ.get('BATCHES', '2'))
SEED = int(os.environ.get('SEED_BASE', '9100'))
MAX_RATIO = 0.07   # natural length within 7% of the old take, so the alignment stretch stays small


def main():
    lines_p, design_p, meta_p, lid, must, out = sys.argv[1:7]
    must = [m for m in must.split(',') if m]
    os.makedirs(out, exist_ok=True)
    ln = [x for x in json.load(open(lines_p)) if x['id'] == lid][0]
    old_dur = [m for m in json.load(open(meta_p)) if m['id'] == lid][0]['dur']
    assert len(ln['segs']) == 1, 'single-segment lines only'
    kind, text = ln['segs'][0]
    tempo = 1.0 if kind == 'n' else Q.QUOTE_SLOW
    v = Q.Voice(json.load(open(design_p)))
    takes = []
    for b in range(BATCHES):
        seed = SEED + b * 1009
        wavs, sr = v.say_batch([normalize(text)] * TAKES_PER_BATCH, seed)
        for k, w in enumerate(wavs):
            w = Q.trim_and_cap(w, sr)
            f0 = Q.median_f0(w, sr)
            lw = Q.finish(Q.stretch(w, sr, tempo), sr)
            hyp = Q.asr(lw, sr)
            err = Q.read_back_error(ln['tts'], hyp)
            dur = len(lw) / sr
            ok = Q.F0_LO <= f0 <= Q.F0_HI and all(m in hyp for m in must)
            name = f'take_{b}_{k}.wav'
            sf.write(os.path.join(out, name), lw, sr)
            takes.append({'name': name, 'seed': seed, 'f0': round(f0, 1), 'dur': round(dur, 3), 'err': round(err, 3),
                          'asr': hyp, 'ok': ok, 'w': lw, 'sr': sr})
            print(f"{name} f0 {f0:.1f} dur {dur:.2f} (old {old_dur:.2f}) err {err:.3f} ok {ok} | {hyp}", flush=True)
    good = [t for t in takes if t['ok'] and abs(t['dur'] / old_dur - 1) <= MAX_RATIO]
    if not good:
        print('no usable take'); sys.exit(1)
    good.sort(key=lambda t: (t['err'], abs(t['dur'] - old_dur)))
    best = good[0]
    sr = best['sr']
    n_old = int(round(old_dur * sr))
    aligned = Q.stretch(best['w'], sr, len(best['w']) / n_old)
    aligned = np.pad(aligned, (0, max(0, n_old - len(aligned))))[:n_old]
    aligned = Q.finish(aligned, sr)
    hyp = Q.asr(aligned, sr)
    err = Q.read_back_error(ln['tts'], hyp)
    f0 = Q.median_f0(aligned, sr)
    final = os.path.join(out, f'{lid}_final.wav')
    sf.write(final, aligned, sr)
    rep = {'line': lid, 'old_dur': old_dur, 'chosen': {k: v for k, v in best.items() if k not in ('w', 'sr')},
           'aligned': {'dur': len(aligned) / sr, 'f0': round(f0, 1), 'err': round(err, 3), 'asr': hyp,
                       'must_ok': all(m in hyp for m in must)},
           'takes': [{k: v for k, v in t.items() if k not in ('w', 'sr')} for t in takes]}
    json.dump(rep, open(os.path.join(out, 'retake_report.json'), 'w'), ensure_ascii=False, indent=1)
    print('chosen', best['name'], '-> aligned', round(len(aligned) / sr, 3), 's, f0', round(f0, 1), 'err', round(err, 3), '|', hyp)


if __name__ == '__main__':
    main()
