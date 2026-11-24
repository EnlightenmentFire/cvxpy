# 逐句整体拉速（rubberband，保留共振峰），之后再压一次停顿、去首尾静音。用法：python tools/stretch_lines.py in_dir out_dir tempo_n tempo_q [行号,...]
import sys, os, subprocess, tempfile, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'src')); sys.path.insert(0, HERE)
from script import L
from qwen_clone_utils import squeeze_pauses, trim, f0
src, dst, tn, tq = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); os.makedirs(dst, exist_ok=True)
idx = [int(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else [i for i in range(len(L)) if os.path.exists(os.path.join(src, f'{i:03d}.wav'))]
for i in idx:
    tempo = tq if L[i][1] == 'q' else tn; pi = os.path.join(src, f'{i:03d}.wav')
    with tempfile.TemporaryDirectory() as d:
        po = os.path.join(d, 'o.wav')
        if abs(tempo - 1) > 1e-3: subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', pi, '-af', f'rubberband=tempo={tempo}:formant=preserved:pitchq=quality:transients=smooth:detector=soft', po], check=True)
        else: po = pi
        b, sr = sf.read(po); b = b.astype(np.float32)
    b = trim(squeeze_pauses(b, sr), sr); sf.write(os.path.join(dst, f'{i:03d}.wav'), b, sr, subtype='PCM_16')
print('stretched', len(idx), 'lines', tn, tq)
