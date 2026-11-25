"""edge-tts zh-CN-YunyangNeural narration per VOICE_SPEC: rate -8%, pitch +0Hz,
per-line synthesis, trim leading/trailing silence, 0.5 s gaps, -15 LUFS.
Usage: python voice_yunyang.py lines.txt out_dir [--only 3,7]
Outputs line_NNNN.wav, timeline.json, narration.srt, narration.wav
"""
import sys, os, json, asyncio, subprocess, numpy as np, soundfile as sf
SR = 48000; GAP = 0.50
VOICE, RATE, PITCH = 'zh-CN-YunyangNeural', '-8%', '+0Hz'

async def synth(text, mp3):
    import edge_tts
    for k in range(5):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(mp3); return
        except Exception as e:
            print('retry', k, e); await asyncio.sleep(2 + 3*k)
    raise RuntimeError('edge-tts failed: ' + text)

def load(mp3):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def trim(y, thr_db=-45, pad=0.03):
    fr = int(0.01*SR); e = np.array([np.sqrt(np.mean(y[i:i+fr]**2)+1e-12) for i in range(0, len(y)-fr, fr)])
    on = np.where(20*np.log10(e) > thr_db)[0]
    if len(on) == 0: return y
    a = max(0, on[0]*fr - int(pad*SR)); b = min(len(y), (on[-1]+1)*fr + int(pad*SR))
    return y[a:b]

def srt_t(s):
    ms = int(round(s*1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); se, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{se:02d},{ms:03d}'

def assemble(lines, out, wav_for):
    seg, tl, t = [], [], 0.0
    for i, text in enumerate(lines, 1):
        y = wav_for(i)
        seg.append(y); seg.append(np.zeros(int(GAP*SR), np.float32))
        tl.append({'i': i, 'text': text, 'start': round(t, 3), 'end': round(t + len(y)/SR, 3)})
        t += len(y)/SR + GAP
    full = np.concatenate(seg)
    sf.write(os.path.join(out, 'narration_raw.wav'), full, SR)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out, 'narration_raw.wav'), '-af',
                    'loudnorm=I=-15:TP=-1.5:LRA=11:linear=true', '-ar', str(SR), os.path.join(out, 'narration.wav')], check=True)
    json.dump(tl, open(os.path.join(out, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'narration.srt'), 'w') as f:
        for e in tl: f.write(f"{e['i']}\n{srt_t(e['start'])} --> {srt_t(e['end'])}\n{e['text']}\n\n")
    n = sum(len(x) for x in lines); dur = t
    print(f'{len(lines)} lines, {dur:.1f}s, {n} chars, {n/dur*60:.0f} chars/min')

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    lines = [l.strip() for l in open(src) if l.strip() and not l.startswith('#')]
    only = set(int(x) for x in sys.argv[4].split(',')) if '--only' in sys.argv else None
    async def run():
        import hashlib, shutil
        cache = os.path.join(out, 'cache'); os.makedirs(cache, exist_ok=True)
        for i, text in enumerate(lines, 1):
            w = os.path.join(out, f'line_{i:04d}.wav')
            c = os.path.join(cache, hashlib.md5(text.encode()).hexdigest() + '.wav')
            if not os.path.exists(c) or (only and i in only):
                mp3 = c[:-4] + '.mp3'; await synth(text, mp3)
                sf.write(c, trim(load(mp3)), SR); os.remove(mp3)
            shutil.copyfile(c, w)
    asyncio.run(run())
    assemble(lines, out, lambda i: sf.read(os.path.join(out, f'line_{i:04d}.wav'), dtype='float32')[0])
