"""逐句合成旁白，产出 build/narration.wav 与 build/timeline.{json,js}。

模型：hexgrad/Kokoro-82M-v1.1-zh（Apache-2.0，中文语料由龙猫数据授权给模型作者）。
用法：python tts.py [--voice zf_006] [--speed 0.92] [--only L01,L02] [--sample out.wav]
"""
import argparse, json, re, sys, hashlib
from pathlib import Path
import numpy as np, soundfile as sf, torch
from kokoro import KModel, KPipeline
from script import LINES

REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
SR = 24000
ROOT = Path(__file__).parent
BUILD = ROOT / 'build'; (BUILD / 'lines').mkdir(parents=True, exist_ok=True)

EN = {  # 字母词读音（Kokoro 音素）
    'MBTI': 'ˌɛmbˌitˌiˈI', 'J': 'ʤˈA', 'P': 'pˈi', 'JP': 'ʤˈA pˈi',
}
def en_callable(text):
    key = text.strip().upper()
    if key in EN: return EN[key]
    raise KeyError(f'no pronunciation for English token {text!r}')

PUNC_TXT = '，。：；？！、…—'
def clauses(text):
    """按标点切成小句，返回 [(小句文字, 是否以强停顿结尾)]。引号书名号不切。"""
    out, cur = [], ''
    for ch in text:
        if ch in PUNC_TXT:
            if cur.strip(): out.append(cur.strip())
            cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def disp(s):
    return s.strip()

def pack_subs(cl, maxlen=17):
    """相邻小句合并成不超过 maxlen 字的字幕条；返回 [[小句下标...]]。"""
    groups, cur, n = [], [], 0
    for i, c in enumerate(cl):
        L = len(c)
        if cur and n + L + 1 > maxlen: groups.append(cur); cur, n = [], 0
        cur.append(i); n += L + (1 if n else 0)
    if cur: groups.append(cur)
    return groups

def speed_fn(base):
    def f(len_ps):  # 官方脚本的经验做法：音素串越长越容易抢拍，稍微放慢
        k = 1.0
        if len_ps > 83: k = 1 - min(len_ps - 83, 100) / 500
        return base * k
    return f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', default='zf_006'); ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--only'); ap.add_argument('--sample'); ap.add_argument('--tag', default='')
    a = ap.parse_args()
    model = KModel(repo_id=REPO).to('cpu').eval()
    pipe = KPipeline(lang_code='z', repo_id=REPO, model=model, en_callable=en_callable)
    pack = pipe.load_voice(a.voice)
    lines = LINES
    if a.only:
        ids = a.only.split(','); lines = [l for l in LINES if l['id'] in ids]
    t = 0.6 if not a.sample else 0.15           # 片头留白
    audio, tl_lines, subs, report = [np.zeros(int(t * SR), np.float32)], {}, [], []
    for ln in lines:
        text = ln.get('say', ln['text'])
        ps, _ = pipe.g2p(text)
        for a_, b_ in ln.get('fix', []):        # 个别多音字手工改音素
            assert a_ in ps, (ln['id'], a_, ps); ps = ps.replace(a_, b_)
        assert '❓' not in ps, (ln['id'], ps)
        assert len(ps) <= 400, (ln['id'], len(ps))
        key = hashlib.md5(f'{a.voice}|{a.speed}|{ps}'.encode()).hexdigest()[:12]
        cache = BUILD / 'lines' / f'{key}.npz'
        if cache.exists():
            z = np.load(cache); wav, dur = z['wav'], z['dur']
        else:
            torch.manual_seed(0)
            out = KPipeline.infer(model, ps, pack, speed_fn(a.speed * ln.get('speed', 1.0)))
            wav, dur = out.audio.numpy().astype(np.float32), out.pred_dur.numpy()
            np.savez(cache, wav=wav, dur=dur)
        # 逐音素时长 → 每个标点的时间点
        per = len(wav) / SR / dur.sum()
        cum = np.cumsum(dur) * per                 # dur[0] 是起始符
        toks = list(ps)
        assert len(dur) == len(toks) + 2, (len(dur), len(toks))
        bounds = [cum[i + 1] for i, ch in enumerate(toks) if ch in ',.:;?!…—']   # 标点结束时刻
        # 去掉首尾静音
        env = np.abs(wav); thr = 0.012
        nz = np.where(env > thr)[0]; a0 = max(0, nz[0] - int(0.03 * SR)); a1 = min(len(wav), nz[-1] + int(0.10 * SR))
        seg = wav[a0:a1]; off = a0 / SR; L = len(seg) / SR
        cl = clauses(ln.get('sub', ln['text']))
        cl_say = clauses(text)
        if len(bounds) >= len(cl_say) - 1 and len(cl) == len(cl_say):
            # 文本小句数与音素标点数对得上：用模型时长
            bs = bounds[:len(cl) - 1] if len(bounds) == len(cl) - 1 else bounds[:len(cl) - 1]
            edges = [0.0] + [min(max(b - off, 0), L) for b in bs] + [L]
            how = 'dur'
        else:
            w = np.array([len(c) + 1.5 for c in cl], float); edges = [0.0] + list(np.cumsum(w) / w.sum() * L); how = 'prop'
        s0 = t
        tl_lines[ln['id']] = dict(s=round(s0, 3), e=round(s0 + L, 3))
        if not ln.get('nosub'):
            for g in pack_subs(cl, ln.get('maxlen', 17)):
                subs.append(dict(s=round(s0 + edges[g[0]], 3), e=round(s0 + edges[g[-1] + 1], 3), text=' '.join(disp(cl[i]) for i in g), line=ln['id']))
        for k, c in enumerate(cl):   # 小句级时间点，供画面对拍：L05.2 = 第 5 行第 3 小句
            tl_lines[f"{ln['id']}c{k}"] = dict(s=round(s0 + edges[k], 3), e=round(s0 + edges[k + 1], 3))
        gap = ln.get('gap', 0.38)
        audio += [seg, np.zeros(int(gap * SR), np.float32)]
        t += L + gap
        report.append(f"{ln['id']} {s0:7.2f} {L:5.2f}s {how} n_ps={len(ps):3d} | {text}\n      {ps}")
    # 字幕之间别留碎缝：相邻字幕间隔 < 0.3s 时把前一条延到后一条开始
    for i in range(len(subs) - 1):
        if 0 < subs[i + 1]['s'] - subs[i]['e'] < 0.3: subs[i]['e'] = subs[i + 1]['s']
    total = t + (2.6 if not a.sample else 0.2)
    audio.append(np.zeros(int((total - t) * SR), np.float32))
    wav = np.concatenate(audio)
    if a.sample:
        sf.write(a.sample, wav, SR); print('sample', a.sample, round(len(wav) / SR, 2), 's'); return
    sf.write(BUILD / f'narration{a.tag}.wav', wav, SR)
    tl = dict(duration=round(total, 3), voice=a.voice, speed=a.speed, lines=tl_lines, subs=subs)
    (BUILD / 'timeline.json').write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    (BUILD / 'timeline.js').write_text('window.TL = ' + json.dumps(tl, ensure_ascii=False) + ';')
    (BUILD / 'tts_report.txt').write_text('\n'.join(report))
    print('total', round(total, 2), 's;', len(subs), 'subs')

if __name__ == '__main__':
    main()
