# 微软云扬（zh-CN-YunyangNeural，edge-tts）逐句配音，替换 Kokoro 版。
# 规格（VOICE_SPEC / tools/voice_yunyang.py）：rate -8%，不降调，句间 0.5s，成片 -15 LUFS（响度在 make.sh 里做）。
# 运行环境：/opt/ttsenv（需 edge-tts）。经 agent 代理时须信任 /root/.ccr/ca-bundle.crt。
import asyncio, json, os, subprocess, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import S

if os.path.exists('/root/.ccr/ca-bundle.crt'):
    import certifi
    certifi.where = lambda: '/root/.ccr/ca-bundle.crt'
import edge_tts

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
VOICE, RATE, GAP, SR = 'zh-CN-YunyangNeural', '-8%', 0.5, 24000
END_HOLD = 2.2  # 末句之后的收尾停留（不属于句间）

# 只做同音替换，规避多音字误读（不改字幕）
REPL = [("乐进", "岳进"), ("乐将军", "岳将军"), ("张辽传", "张辽撰"), ("李典传", "李典撰"), ("吴主传", "吴主撰"),
        ("甘宁传", "甘宁撰"), ("凌统传", "凌统撰"), ("江表传", "江表撰"), ("蒋济传", "蒋济撰"), ("都亭侯", "嘟亭侯"),
        ("虎贲", "虎奔"), ("会稽", "快鸡"), ("椎牛", "垂牛"), ("张憙", "张喜"), ("薛悌", "薛替")]


def prep(s):
    t = s.get('tts') or s['t']
    for a, b in REPL:
        t = t.replace(a, b)
    return t


async def one(i, txt, sem):
    mp3 = os.path.join(OUT, f'seg_{i:03d}.mp3')
    wav = os.path.join(OUT, f'seg_{i:03d}.wav')
    async with sem:
        for k in range(4):
            try:
                await edge_tts.Communicate(txt, VOICE, rate=RATE).save(mp3)
                if os.path.getsize(mp3) > 1000:
                    break
            except Exception as e:
                print('retry', i, k, e, flush=True)
                await asyncio.sleep(2 + 3 * k)
        else:
            raise RuntimeError(f'TTS failed for {i}')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), wav], check=True)
    a, _ = sf.read(wav, dtype='float32')
    thr = 0.01 * np.max(np.abs(a))
    nz = np.where(np.abs(a) > thr)[0]
    a = a[max(0, nz[0] - int(0.04 * SR)): nz[-1] + int(0.08 * SR)]
    sf.write(wav, a, SR)
    print(i, round(len(a) / SR, 2), txt[:24], flush=True)
    return i, wav, len(a) / SR


async def main():
    sem = asyncio.Semaphore(3)
    jobs = [one(i, prep(s), sem) for i, s in enumerate(S) if 't' in s]
    res = {i: (w, d) for i, w, d in await asyncio.gather(*jobs)}
    last = max(res)
    man = []
    for i, s in enumerate(S):
        if 't' not in s:
            man.append(dict(i=i, chap=True, dur=s['dur']))
        else:
            w, d = res[i]
            man.append(dict(i=i, file=w, dur=d, gap=END_HOLD if i == last else GAP))
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
    print('total', sum(m['dur'] + m.get('gap', 0) for m in man))

asyncio.run(main())
