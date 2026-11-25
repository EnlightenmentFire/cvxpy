# -*- coding: utf-8 -*-
"""给 MusicGen 候选片段打分，帮助挑版本（最好听、最不抢人声的那一版）：
- 响度（BS.1770 积分）与 3 秒短时响度的起伏，最响的 2 秒窗口位置（高潮对齐用）
- 1–4 kHz（人声清晰度频段）能量占比：越低越不抢旁白
- 估调（与 D 小调模板的相关）、估速（BPM）
- 有没有人声：faster-whisper 回读，排除“唱出字”的片段
- 中途断空、削波
另出一张梅尔谱总览图 cache/music/sheet_<前缀>.png。用法：python tools/music_pick.py 前缀 [前缀…]"""
import sys, os, glob, json, numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from loud import lufs, short_term
MD = os.path.join(ROOT, 'cache', 'music')
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])   # Krumhansl 小调
KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def key_of(y, sr):
    c = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1); best = []
    for mode, tpl in (('m', KS_MIN), ('', KS_MAJ)):
        for k in range(12): best.append((np.corrcoef(c, np.roll(tpl, k))[0, 1], NAMES[k] + mode))
    best.sort(reverse=True); dm = [r for r, n in best if n == 'Dm'][0]
    return best[0][1], round(best[0][0], 2), round(dm, 2)


def analyse(p, asr=None):
    w, sr = sf.read(p); w48 = librosa.resample(w.T.astype(np.float32), orig_sr=sr, target_sr=48000).T
    m = w.mean(1); r = {}
    r['dur'] = round(len(w) / sr, 1); r['lufs'] = round(lufs(w48), 1)
    t, st = short_term(w48, 48000, 3.0, 0.25); r['st_range'] = round(float(np.percentile(st, 95) - np.percentile(st, 10)), 1)
    t2, st2 = short_term(w48, 48000, 2.0, 0.1); r['peak2s_at'] = round(float(t2[np.argmax(st2)]), 1)
    S = np.abs(librosa.stft(m, n_fft=4096, hop_length=1024)) ** 2; f = librosa.fft_frequencies(sr=sr, n_fft=4096)
    tot = S[(f > 40)].sum(); r['band1_4k'] = round(float(S[(f > 1000) & (f < 4000)].sum() / tot * 100), 1)
    r['band2_4k'] = round(float(S[(f > 2000) & (f < 4000)].sum() / tot * 100), 2)
    r['centroid'] = int(np.median(librosa.feature.spectral_centroid(y=m, sr=sr)))
    r['key'], r['key_r'], r['dm_r'] = key_of(m, sr)
    tempo, _ = librosa.beat.beat_track(y=m, sr=sr); r['bpm'] = int(np.atleast_1d(tempo)[0])
    e = librosa.feature.rms(y=m, frame_length=2048, hop_length=512)[0]; q = e < e.max() * 0.02
    run = 0; mx = 0
    for v in q[20:-20]:
        run = run + 1 if v else 0; mx = max(mx, run)
    r['gap_s'] = round(mx * 512 / sr, 2); r['clip'] = int((np.abs(w) > 0.99).sum())
    if asr is not None:
        y16 = librosa.resample(m.astype(np.float32), orig_sr=sr, target_sr=16000); txt = []
        for lang in ('zh', 'en'):
            segs, _ = asr.transcribe(y16, language=lang, beam_size=1, vad_filter=False, condition_on_previous_text=False)
            for s in segs:
                if s.no_speech_prob < 0.6 and s.avg_logprob > -0.9 and len(s.text.strip()) > 1: txt.append(f'{lang}:{s.text.strip()}({s.avg_logprob:.1f}/{s.no_speech_prob:.2f})')
        r['asr'] = ' | '.join(txt)[:120]
    return r, m, sr, (t, st)


def sheet(rows, out):
    from PIL import Image, ImageDraw, ImageFont
    H = 150; Wd = 1400; img = Image.new('RGB', (Wd, H * len(rows)), (12, 12, 14)); dr = ImageDraw.Draw(img)
    try: font = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'NotoSansSC.ttf'), 18)
    except Exception: font = ImageFont.load_default()
    for i, (name, m, sr, (t, st), r) in enumerate(rows):
        M = librosa.power_to_db(librosa.feature.melspectrogram(y=m, sr=sr, n_fft=2048, hop_length=512, n_mels=96, fmax=8000), ref=np.max)
        a = np.clip((M + 70) / 70, 0, 1)[::-1]; rgb = (np.stack([a ** 0.6, a ** 1.2, a ** 2.5], -1) * 255).astype(np.uint8)
        im = Image.fromarray(rgb).resize((Wd - 300, H - 8)); img.paste(im, (300, i * H + 4))
        x = 300 + (np.asarray(t) / r['dur']) * (Wd - 300); y = i * H + 4 + (H - 8) * (1 - np.clip((np.asarray(st) + 45) / 40, 0, 1))
        dr.line(list(zip(x.tolist(), y.tolist())), fill=(120, 220, 255), width=2)
        dr.text((8, i * H + 8), name, fill=(240, 220, 160), font=font)
        dr.text((8, i * H + 34), f"{r['lufs']} LUFS  rng {r['st_range']}  pk@{r['peak2s_at']}s", fill=(220, 220, 220), font=font)
        dr.text((8, i * H + 58), f"1-4k {r['band1_4k']}%  2-4k {r['band2_4k']}%  {r['key']}({r['dm_r']})", fill=(220, 220, 220), font=font)
        dr.text((8, i * H + 82), f"{r['bpm']}bpm  gap {r['gap_s']}s  clip {r['clip']}", fill=(220, 220, 220), font=font)
        if r.get('asr'): dr.text((8, i * H + 106), 'ASR! ' + r['asr'][:24], fill=(255, 120, 100), font=font)
    img.save(out)


if __name__ == '__main__':
    asr = None
    if os.environ.get('NOASR') != '1':
        from faster_whisper import WhisperModel
        asr = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=2)
    res = json.load(open(os.path.join(MD, 'pick.json'))) if os.path.exists(os.path.join(MD, 'pick.json')) else {}
    for pre in sys.argv[1:]:
        rows = []
        for p in sorted(glob.glob(os.path.join(MD, pre + '*.wav'))):
            n = os.path.basename(p); r, m, sr, st = analyse(p, asr); res[n] = r; rows.append((n, m, sr, st, r))
            print(n, json.dumps(r, ensure_ascii=False), flush=True)
        if rows: sheet(rows, os.path.join(MD, f'sheet_{pre.strip("_*")}.png'))
    json.dump(res, open(os.path.join(MD, 'pick.json'), 'w'), ensure_ascii=False, indent=1)
