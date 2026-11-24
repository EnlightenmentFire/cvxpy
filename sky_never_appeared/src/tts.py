"""Kokoro-82M v1.1-zh (Apache-2.0) narration: one wav per line + timing json.

Run inside the tts312 venv:
    python tts.py lines.json out_dir [voice]
lines.json: [{"id":..., "tts":..., "pause":seconds_after}, ...]
"""
import sys, os, json, re, glob
import numpy as np
import soundfile as sf

REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
SR = 24000

DIG = '零一二三四五六七八九'


def read_digits(s):
    return ''.join(DIG[int(ch)] for ch in s)


def read_int(n):
    """Chinese reading of an integer < 100000 (e.g. 5500 -> 五千五百)."""
    n = int(n)
    if n == 0:
        return '零'
    units = [(10000, '万'), (1000, '千'), (100, '百'), (10, '十')]
    out = ''
    zero = False
    for u, name in units:
        q = n // u
        n %= u
        if q:
            if zero:
                out += '零'
            if not (u == 10 and q == 1 and out == ''):
                out += DIG[q]
            out += name
            zero = False
        elif out:
            zero = True
    if n:
        if zero:
            out += '零'
        out += DIG[n]
    # trailing zeros: 5500 -> 五千五百 (not 五千五百零)
    return out


def normalize(s):
    s = s.replace('“', '').replace('”', '').replace('「', '').replace('」', '').replace('"', '')
    s = s.replace('《', '').replace('》', '')
    # years (19xx/20xx followed by 年 or used as year)
    s = re.sub(r'(1[89]\d\d|20\d\d)\s*年', lambda m: read_digits(m.group(1)) + '年', s)
    s = re.sub(r'(\d+)\s*月', lambda m: read_int(m.group(1)) + '月', s)
    s = re.sub(r'(\d+)\s*日', lambda m: read_int(m.group(1)) + '日', s)
    s = re.sub(r'(\d+)\s*号', lambda m: read_int(m.group(1)) + '号', s)
    s = re.sub(r'(\d+)\s*%', lambda m: '百分之' + read_int(m.group(1)), s)
    s = re.sub(r'(\d+)', lambda m: read_int(m.group(1)), s)
    s = re.sub(r'\s+', '', s)
    return s


def main():
    lines = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else 'zm_098'
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    os.makedirs(out, exist_ok=True)
    from kokoro import KModel, KPipeline
    model = KModel(repo_id=REPO).eval()
    en = KPipeline(lang_code='a', repo_id=REPO, model=False)

    def en_callable(t):
        return next(en(t)).phonemes
    zh = KPipeline(lang_code='z', repo_id=REPO, model=model, en_callable=en_callable)
    vdir = glob.glob(os.path.expanduser('~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M-v1.1-zh/snapshots/*/voices'))[0]
    vpath = os.path.join(vdir, voice + '.pt')

    import torch
    torch.set_num_threads(int(os.environ.get('TTS_THREADS', '4')))

    def spd(len_ps):
        # this voice does not rush on long lines; keep a constant pace
        return speed
    meta = []
    for ln in lines:
        txt = normalize(ln['tts'])
        wavs = []
        for r in zh(txt, voice=vpath, speed=spd):
            wavs.append(r.audio.numpy())
        w = np.concatenate(wavs) if wavs else np.zeros(1)
        # trim leading/trailing near-silence
        a = np.abs(w)
        idx = np.nonzero(a > 0.01)[0]
        if len(idx):
            w = w[max(0, idx[0] - 240): idx[-1] + 2400]
        f = os.path.join(out, f"{ln['id']}.wav")
        sf.write(f, w.astype(np.float32), SR)
        meta.append({'id': ln['id'], 'dur': len(w) / SR, 'tts_norm': txt})
        print(ln['id'], round(len(w) / SR, 2), txt, flush=True)
    json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
