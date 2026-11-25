# edge-tts 云扬逐句合成 -> 裁静音 -> 拼接（句间 0.5s）-> timeline.json / narration.srt / narration.wav
import asyncio, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from script import SCENES

OUT = sys.argv[1] if len(sys.argv) > 1 else 'voice'
os.makedirs(OUT, exist_ok=True)
SR = 48000
GAP = 0.50
VOICE, RATE = 'zh-CN-YunyangNeural', '-8%'

lines = []
for si, sc in enumerate(SCENES):
    for li, (sub, say) in enumerate(sc['lines']):
        lines.append(dict(scene=sc['id'], si=si, li=li, sub=sub, say=say or sub))

async def synth(i, L, sem):
    mp3 = f'{OUT}/line_{i+1:04d}.mp3'
    if os.path.exists(f'{OUT}/line_{i+1:04d}.wav') or (os.path.exists(mp3) and os.path.getsize(mp3) > 1000):
        return
    async with sem:
        import edge_tts
        for k in range(4):
            try:
                c = edge_tts.Communicate(L['say'], VOICE, rate=RATE, pitch='+0Hz')
                await c.save(mp3)
                return
            except Exception as e:
                print('retry', i, e); await asyncio.sleep(2 + 2 * k)

async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[synth(i, L, sem) for i, L in enumerate(lines)])
asyncio.run(main())

def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def trim(x, thr=0.008):
    env = np.convolve(np.abs(x), np.ones(240) / 240, 'same')
    idx = np.where(env > thr)[0]
    if len(idx) == 0: return x
    a = max(0, idx[0] - int(0.03 * SR)); b = min(len(x), idx[-1] + int(0.06 * SR))
    y = x[a:b].copy()
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

PAD_TITLE_BEFORE, PAD_TITLE_AFTER, PAD_SCENE = 0.9, 0.7, 0.25
segs = []; t = 0.0; tl = []
prev_si = None
for i, L in enumerate(lines):
    wv = f'{OUT}/line_{i+1:04d}.wav'   # 外部（如托克维尔音色）逐句 wav 优先
    y = trim(load(wv if os.path.exists(wv) else f'{OUT}/line_{i+1:04d}.mp3'))
    kind = SCENES[L['si']]['kind']
    if prev_si is not None and L['si'] != prev_si:
        t += PAD_SCENE
        if SCENES[prev_si]['kind'] == 'title': t += PAD_TITLE_AFTER
    if L['li'] == 0 and kind == 'title': t += PAD_TITLE_BEFORE
    if i == 0: t += 0.35   # 声音钩子先响 0.35s
    d = len(y) / SR
    tl.append(dict(i=i + 1, scene=L['scene'], si=L['si'], li=L['li'], start=round(t, 3), end=round(t + d, 3),
                   text=L['sub'], say=L['say']))
    segs.append((t, y)); t += d + GAP; prev_si = L['si']
total = t + 2.5   # 结尾留白
buf = np.zeros(int(total * SR) + SR, np.float32)
for st, y in segs:
    a = int(st * SR); buf[a:a + len(y)] += y
buf = buf[:int(total * SR)]
# 场景区间
scenes = []
for si, sc in enumerate(SCENES):
    ls = [x for x in tl if x['si'] == si]
    scenes.append(dict(id=sc['id'], kind=sc['kind'], start=ls[0]['start'], end=ls[-1]['end']))
for k in range(len(scenes)):
    scenes[k]['vstart'] = 0.0 if k == 0 else scenes[k - 1]['vend']
    scenes[k]['vend'] = total if k == len(scenes) - 1 else round((scenes[k]['end'] + scenes[k + 1]['start']) / 2, 3)
json.dump(dict(total=round(total, 3), lines=tl, scenes=scenes), open(f'{OUT}/timeline.json', 'w'), ensure_ascii=False, indent=1)
raw = f'{OUT}/narration_raw.wav'
import wave
with wave.open(raw, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11', '-ar', str(SR), f'{OUT}/narration.wav'])
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'
with open(f'{OUT}/narration.srt', 'w') as f:
    for x in tl:
        f.write(f"{x['i']}\n{ts(x['start'])} --> {ts(x['end'])}\n{x['text']}\n\n")
hz = sum(len([c for c in x['text'] if '一' <= c <= '鿿']) for x in tl)
print('total', round(total, 1), 's  lines', len(tl), ' hanzi', hz, ' rate', round(hz / total * 60), '/min')
