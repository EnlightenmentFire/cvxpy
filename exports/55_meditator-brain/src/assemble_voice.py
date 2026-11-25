"""Assemble externally generated per-line wavs (e.g. Tocqueville voice from the box) into
timeline.json / narration.srt / narration.wav (-15 LUFS) so render.py + mix.py can rebuild the video.
python assemble_voice.py lines.txt IN_DIR(line_0001.wav...) OUT_DIR"""
import sys, os, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from voice_yunyang import assemble, trim, SR

def load_any(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return trim(np.frombuffer(raw, np.float32).copy())

if __name__ == '__main__':
    src, ind, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    lines = [l.strip() for l in open(src) if l.strip() and not l.startswith('#')]
    missing = [i for i in range(1, len(lines) + 1) if not os.path.exists(os.path.join(ind, f'line_{i:04d}.wav'))]
    if missing: sys.exit(f'missing line wavs: {missing[:10]}...')
    import soundfile as sf
    def get(i):
        y = load_any(os.path.join(ind, f'line_{i:04d}.wav')); sf.write(os.path.join(out, f'line_{i:04d}.wav'), y, SR); return y
    assemble(lines, out, get)
