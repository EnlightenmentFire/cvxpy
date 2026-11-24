"""Step 2: clone the designed reference voice with Qwen3-TTS Base and narrate the script.

Pipeline (all checks per the voice spec):
  * every line is split into narration / quotation segments (quotes read slightly slower)
  * segments are synthesised in batches with the cloned voice (bf16 on CPU)
  * median pitch per segment (parselmouth) must be 85-105 Hz; otherwise the segment is
    regenerated with another seed (no global pitch shifting)
  * internal silences longer than 0.4 s are cut to 0.4 s
  * pace: rubberband time-stretch, formant preserving; narration faster, quotes slower
  * 50 Hz high-pass; speech RMS normalised to -18 dBFS
  * ASR read-back per line (faster-whisper); misread lines are regenerated
Run in the qwen312 venv:
    python qwen_narrate.py lines.json design.json out_dir
"""
import os, sys, json, re, time, glob, subprocess, tempfile, difflib
import numpy as np
import soundfile as sf
import torch
import parselmouth
from scipy import signal

F0_LO, F0_HI = 85.0, 105.0
ROUNDS = int(os.environ.get('ROUNDS', '4'))
ASR_ROUNDS = int(os.environ.get('ASR_ROUNDS', '2'))
BATCH = int(os.environ.get('BATCH', '6'))
QUOTE_SLOW = 0.89                                        # quotes at 1.16/1.3 of narration tempo
TARGET_CPS = float(os.environ.get('TARGET_CPS', '4.6'))  # narration chars/s after stretching
SEG_GAP = 0.14
MAX_PAUSE = 0.4
RMS_DB = -18.0
ASR_THR = float(os.environ.get('ASR_THR', '0.06'))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import normalize


def han(s):
    return re.sub(r'[^一-鿿]', '', s)


def median_f0(w, sr):
    snd = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr)
    p = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array['frequency']
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


def trim_and_cap(w, sr, cap=MAX_PAUSE):
    hop = int(0.01 * sr)
    n = len(w) // hop
    if n == 0:
        return w
    e = np.array([np.sqrt(np.mean(w[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(e + 1e-12)
    ref = np.percentile(db, 95)
    voiced = db > max(-42.0, ref - 38)
    idx = np.nonzero(voiced)[0]
    if len(idx) == 0:
        return w
    a, b = max(0, idx[0] - 3), min(n, idx[-1] + 6)
    keep, run, capn = [], 0, int(cap / 0.01)
    for i in range(a, b):
        if voiced[i]:
            run = 0
            keep.append(i)
        else:
            run += 1
            if run <= capn:
                keep.append(i)
    out = np.concatenate([w[i * hop:(i + 1) * hop] for i in keep]).astype(np.float32)
    f = min(len(out) // 4, int(0.005 * sr))
    if f > 0:
        out[:f] *= np.linspace(0, 1, f)
        out[-f:] *= np.linspace(1, 0, f)
    return out


def stretch(w, sr, tempo):
    if abs(tempo - 1.0) < 0.01:
        return w
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'a.wav'), os.path.join(d, 'b.wav')
        sf.write(a, w, sr)
        subprocess.run(['rubberband', '-q', '-T', f'{tempo:.4f}', '-F', '--fine', a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out, _ = sf.read(b)
    return out.astype(np.float32)


def finish(w, sr):
    w = signal.sosfilt(signal.butter(2, 50, 'hp', fs=sr, output='sos'), w)
    hop = int(0.02 * sr)
    rms = np.array([np.sqrt(np.mean(w[i:i + hop] ** 2)) for i in range(0, len(w) - hop, hop)] or [0.0])
    act = rms[rms > np.percentile(rms, 40)] if len(rms) > 4 else rms
    w = w * (10 ** (RMS_DB / 20) / (np.sqrt(np.mean(act ** 2)) + 1e-9))
    pk = np.abs(w).max()
    if pk > 0.97:
        w = w * 0.97 / pk
    return w.astype(np.float32)


class Voice:
    def __init__(self, design):
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(int(os.environ.get('TTS_THREADS', '4')))
        path = os.environ.get('QWEN_BASE_PATH') or glob.glob(
            '/tmp/claude-0/-home-user-cvxpy/f0c8e50d-dc80-5fad-820f-299cfe1179c7/scratchpad/ms_models/models/Qwen--Qwen3-TTS-12Hz-1.7B-Base/snapshots/*')[0]
        self.model = Qwen3TTSModel.from_pretrained(path, device_map='cpu',
                                                   dtype=getattr(torch, os.environ.get('QWEN_DTYPE', 'bfloat16')))
        ch = design['chosen']
        ref, sr = sf.read(ch['path'])
        self.prompt = self.model.create_voice_clone_prompt(ref_audio=(ref.astype(np.float32), sr),
                                                           ref_text=design['ref_text'], x_vector_only_mode=False)

    def say_batch(self, texts, seed):
        torch.manual_seed(seed); np.random.seed(seed)
        wavs, sr = self.model.generate_voice_clone(text=list(texts), language=['Chinese'] * len(texts),
                                                   voice_clone_prompt=self.prompt * len(texts))
        return [np.asarray(w, np.float32) for w in wavs], sr


_ASR = None
def asr(w, sr):
    global _ASR
    from faster_whisper import WhisperModel
    if _ASR is None:
        _ASR = WhisperModel(os.environ.get('ASR_MODEL', 'medium'), device='cpu', compute_type='int8')
    w16 = signal.resample_poly(w, 16000, sr).astype(np.float32)
    segs, _ = _ASR.transcribe(w16, language='zh', initial_prompt='以下是普通话的句子。', beam_size=5)
    return ''.join(s.text for s in segs)


def read_back_error(ref_text, hyp):
    from pypinyin import lazy_pinyin
    R = lazy_pinyin(han(normalize(ref_text)))
    Hh = lazy_pinyin(han(normalize(hyp)))
    return 1 - difflib.SequenceMatcher(a=R, b=Hh, autojunk=False).ratio()


def main():
    lines = json.load(open(sys.argv[1]))
    design = json.load(open(sys.argv[2]))
    out = sys.argv[3]
    os.makedirs(out, exist_ok=True)
    t_start = time.time()
    v = Voice(design)
    print(f'model loaded {time.time() - t_start:.0f}s', flush=True)
    segs = []
    for ln in lines:
        for i, (kind, txt) in enumerate(ln['segs']):
            segs.append({'key': f"{ln['id']}#{i}", 'line': ln['id'], 'i': i, 'kind': kind, 'text': txt,
                         'norm': normalize(txt), 'best': None, 'done': False, 'tries': 0})
    by_key = {s['key']: s for s in segs}
    seed_base = int(os.environ.get('SEED_BASE', '7000'))

    def synth_round(pending, rnd):
        pending = sorted(pending, key=lambda s: len(s['norm']))
        for b in range(0, len(pending), BATCH):
            chunk = pending[b:b + BATCH]
            seed = seed_base + rnd * 1009 + b
            t0 = time.time()
            wavs, sr = v.say_batch([s['norm'] for s in chunk], seed)
            for s, w in zip(chunk, wavs):
                w = trim_and_cap(w, sr)
                f0 = median_f0(w, sr)
                ok = F0_LO <= f0 <= F0_HI
                score = 0.0 if ok else min(abs(f0 - F0_LO), abs(f0 - F0_HI))
                s['tries'] += 1
                if s['best'] is None or score < s['best']['score']:
                    s['best'] = {'w': w, 'sr': sr, 'f0': f0, 'seed': seed, 'score': score}
                s['done'] = ok
            dur = sum(len(w) for w in wavs) / sr
            print(f'  round {rnd} batch {b // BATCH}: {len(chunk)} segs, {dur:.1f}s audio in {time.time() - t0:.0f}s; '
                  f"f0 {[round(s['best']['f0']) for s in chunk]}", flush=True)

    for rnd in range(ROUNDS):
        pending = [s for s in segs if not s['done']]
        if not pending:
            break
        synth_round(pending, rnd)
    rates = [len(han(s['text'])) / (len(s['best']['w']) / s['best']['sr']) for s in segs
             if s['kind'] == 'n' and len(han(s['text'])) >= 8]
    narr_tempo = float(np.clip(TARGET_CPS / np.median(rates), 1.0, 1.45)) if rates else 1.2
    if os.environ.get('NARR_TEMPO'):
        narr_tempo = float(os.environ['NARR_TEMPO'])
    quote_tempo = narr_tempo * QUOTE_SLOW
    print(f'raw narration pace {np.median(rates) if rates else 0:.2f} c/s -> tempo {narr_tempo:.3f}, quotes {quote_tempo:.3f}',
          flush=True)

    def build_line(ln):
        parts, info, sr = [], [], 24000
        for i in range(len(ln['segs'])):
            s = by_key[f"{ln['id']}#{i}"]
            b = s['best']
            sr = b['sr']
            tempo = quote_tempo if s['kind'] == 'q' else narr_tempo
            parts.append(stretch(b['w'], sr, tempo))
            if i < len(ln['segs']) - 1:
                parts.append(np.zeros(int(SEG_GAP * sr), np.float32))
            info.append({'kind': s['kind'], 'text': s['text'], 'f0': round(b['f0'], 1), 'seed': b['seed'],
                         'tempo': round(tempo, 3), 'tries': s['tries']})
        return finish(np.concatenate(parts), sr), sr, info

    results = {}
    for arnd in range(ASR_ROUNDS + 1):
        redo = []
        for ln in lines:
            if ln['id'] in results and results[ln['id']]['asr_err'] <= ASR_THR:
                continue
            w, sr, info = build_line(ln)
            hyp = asr(w, sr)
            err = read_back_error(ln['tts'], hyp)
            prev = results.get(ln['id'])
            if prev is None or err < prev['asr_err']:
                results[ln['id']] = {'id': ln['id'], 'w': w, 'sr': sr, 'segments': info, 'asr': hyp,
                                     'asr_err': round(err, 3), 'f0': round(median_f0(w, sr), 1), 'dur': len(w) / sr}
            print(f"  {ln['id']} f0={results[ln['id']]['f0']} err={err:.3f} asr={hyp}", flush=True)
            if err > ASR_THR:
                redo.append(ln)
        if not redo or arnd == ASR_ROUNDS:
            break
        pending = []
        for ln in redo:
            for i in range(len(ln['segs'])):
                s = by_key[f"{ln['id']}#{i}"]
                s['best'], s['done'] = None, False
                pending.append(s)
        for rnd in range(ROUNDS):
            p2 = [s for s in pending if not s['done']]
            if not p2:
                break
            synth_round(p2, 100 * (arnd + 1) + rnd)
    meta = []
    for ln in lines:
        r = results[ln['id']]
        sf.write(os.path.join(out, ln['id'] + '.wav'), r['w'], r['sr'])
        meta.append({k: v for k, v in r.items() if k not in ('w', 'sr')})
    json.dump({'narr_tempo': narr_tempo, 'quote_tempo': quote_tempo, 'lines': meta},
              open(os.path.join(out, 'report.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump([{'id': m['id'], 'dur': m['dur'], 'tts_norm': normalize(ln['tts'])} for m, ln in zip(meta, lines)],
              open(os.path.join(out, 'meta.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'done in {time.time() - t_start:.0f}s', flush=True)


if __name__ == '__main__':
    main()
