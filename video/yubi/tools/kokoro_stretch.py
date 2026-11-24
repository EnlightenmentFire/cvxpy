# -*- coding: utf-8 -*-
"""备选方案：Kokoro-82M-v1.1-zh 按 1.0 倍速合成，再用 rubberband（保留共振峰）整体拉速：旁白约 1.3 倍、引文约 1.16 倍。
不用 Kokoro 自带的变速（会吞句首句尾）。之后同样压停顿（≤0.4 s）、50 Hz 高通、去首尾静音，并逐句量音高。
用法：LINES_DIR=audio/lines_k034 python tools/kokoro_stretch.py zm_034 [行号,...] [tempo_n] [tempo_q]"""
import sys, os, json, re, subprocess, tempfile, warnings, numpy as np, soundfile as sf; warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src')); sys.path.insert(0, HERE)
from script import L, tts_text
import torch; torch.set_num_threads(4)
from kokoro import KPipeline, KModel
import parselmouth
voice = sys.argv[1]; ONLY = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else list(range(len(L)))
TN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.3; TQ = float(sys.argv[4]) if len(sys.argv) > 4 else 1.16
OUT = os.environ.get('LINES_DIR', os.path.join(ROOT, 'audio', f'lines_k{voice[-3:]}')); os.makedirs(OUT, exist_ok=True)
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)
from qwen_clone_utils import hp50, squeeze_pauses, trim, f0
log = {}
for i in ONLY:
    l = L[i]; a = np.concatenate([r.audio.numpy() for r in pipe(tts_text(l[2]), voice=voice, speed=1.0)]).astype(np.float32)
    tempo = TQ if l[1] == 'q' else TN
    with tempfile.TemporaryDirectory() as d:
        pi, po = os.path.join(d, 'i.wav'), os.path.join(d, 'o.wav'); sf.write(pi, a, 24000)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', pi, '-af', f'rubberband=tempo={tempo}:formant=preserved:pitchq=quality:transients=smooth:detector=soft', po], check=True)
        b, sr = sf.read(po); b = b.astype(np.float32)
    b = trim(squeeze_pauses(hp50(b, sr), sr), sr); med, p90 = f0(b, sr)
    sf.write(os.path.join(OUT, f'{i:03d}.wav'), b, sr, subtype='PCM_16')
    nch = len(re.findall(r'[一-鿿]', l[2])); log[str(i)] = dict(med=med, p90=p90, dur=round(len(b) / sr, 2), cps=round(nch / (len(b) / sr), 2))
    print('LINE', i, l[1], log[str(i)], flush=True)
json.dump(log, open(os.path.join(OUT, 'kokoro_log.json'), 'w'), indent=0)
