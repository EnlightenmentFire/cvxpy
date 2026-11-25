# -*- coding: utf-8 -*-
"""旁白拼接 + 音效 / 环境声（numpy 合成）+ 配乐（MusicGen 片段，src/score.py 拼好的 audio/music.wav）→ 按《配乐规范》侧链混音。
  音乐：削 3 kHz 约 4 dB、开头淡入 2 秒；音乐和音效一起由旁白做侧链压缩（有旁白时比人声低约 15–18 dB，停顿时自动回升）；
  整体 loudnorm 到 -16 LUFS、真峰值不超过 -1.5 dBTP（两遍，线性增益）；结尾淡出 3 秒。
输出 audio/narration.wav、audio/fx.wav、audio/mix.wav；另出无配乐版 audio/mix_nomusic.wav（发布时可用视频号音乐库另配）。
用法：python src/audio.py [nomusic]"""
import json, os, sys, subprocess, re, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sound import *
from loud import lufs, blocks
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f"{ROOT}/src/timeline.json"))
TOTAL = TL['total'] + 0.6
N = int(TOTAL * SR)
LN = lambda s, k: [l for l in TL['lines'] if l['sec'] == s and l['k'] == k][0]
A = lambda s, k: LN(s, k)['start']
E = lambda s, k: LN(s, k)['end']
CK = lambda s, k, j: LN(s, k)['chunks'][min(j, len(LN(s, k)['chunks']) - 1)]['start']
S = TL['secs']
AU = f"{ROOT}/audio"
# 侧链与电平（实测校准：有旁白时音乐比人声低约 16 dB；见 report()）
MUSIC_DB = float(os.environ.get('MUSIC_DB', '0'))      # 音乐总增益（music.wav 已按 -20 LUFS 基准排好层次）
FX_DB = float(os.environ.get('FX_DB', '0'))
SC = dict(threshold=float(os.environ.get('SC_THR', '0.035')), ratio=float(os.environ.get('SC_RATIO', '10')), attack=15, release=500)


def narration():
    buf = np.zeros(N)
    for l in TL['lines']:
        a, sr = sf.read(os.path.join(os.environ.get("LINES_DIR", f"{ROOT}/audio/lines"), f"{l['i']:03d}.wav")); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
        i = int(l['start'] * SR); buf[i:i + len(a)] += a[: N - i]
    buf = fft_filter(buf, 50, None, 4)          # 50 Hz 高通
    w = int(0.03 * SR); e = np.sqrt(np.convolve(buf ** 2, np.ones(w) / w, 'same')) + 1e-6
    thr = 0.09; g = np.where(e > thr, (thr / e) ** 0.45, 1.0); g = np.convolve(g, np.ones(w) / w, 'same')
    buf = buf * g
    # 人声统一到约 -18 dBFS RMS（只按有声段计算）
    w2 = int(0.05 * SR); en = np.sqrt(np.convolve(buf ** 2, np.ones(w2) / w2, 'same')); act = en > en.max() * 0.05
    rms = np.sqrt((buf[act] ** 2).mean()); buf = buf * (10 ** (-18 / 20) / rms)
    return buf


def fx():
    """音效与环境声：只跟画面事件走，不承担配乐。章节卡、片名各一记低鼓作转场。"""
    perc = np.zeros((N, 2)); fx = np.zeros((N, 2)); amb = np.zeros((N, 2))
    # 转场：片名、章节卡
    add(perc, taiko(50, 2.2, 1.2), A('cold', 2) - 0.12, 0.6)
    add(perc, taiko(46, 2.8, 1.3), S['title']['start'] + 0.1, 0.9)
    for sid in ('s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'):
        g = 0.5 if sid in ('s7', 's8') else 0.8
        add(perc, taiko(52, 2.2, 1.1), S[sid]['card'][0] + 0.1, 0.8 * g); add(fx, whoosh(1.1, 200, 1500)[::-1].copy(), S[sid]['card'][0] - 1.0, 0.22 * g)
    # 冷启动：箭入、钉住、纸卷、翻面、射出
    add(fx, arrow_fly(0.6), 0.28, 0.95, -0.6); add(fx, thunk(), 0.88, 1.0, 0.1)
    add(fx, paper(1.2), 1.15, 0.7, 0.0); add(fx, paper(0.7), A('cold', 1) + 0.3, 0.6, 0.1)
    add(fx, paper(0.6), A('cold', 3) + 0.3, 0.6, 0.0); add(fx, arrow_fly(0.6)[::-1].copy() * 0.5 + arrow_fly(0.6) * 0.5, A('cold', 3) + 0.8, 0.95, -0.5)
    # 壹：542 大雪的风
    add(amb, wind(6, 1.6, 0.2), A('s1', 2) + 1.8, 1.0)
    # 贰：大军南下、挖河、堆山
    add(fx, rumble(A('s2', 3) - A('s2', 1) + 1, 36, 1.0), A('s2', 1) - 0.2, 0.8)
    for k in range(10): add(fx, dig(), CK('s2', 3, 2) - 0.2 + k * 0.22, 0.5, rng.uniform(-0.4, 0.4))
    for k in range(14): add(fx, taiko(84, 0.35, 0.2) * 0.4, A('s2', 4) + 0.6 + k * 0.42, 0.45, rng.uniform(-0.5, 0.5))
    # 叁：挖地道、火
    for k in range(18): add(fx, taiko(70, 0.3, 0.3) * 0.35, A('s3', 0) + 1.0 + k * 0.6, 0.4, rng.uniform(-0.5, 0.5))
    f0 = CK('s3', 1, 2) + 0.2; add(fx, whoosh(1.4, 200, 1400), f0 - 0.2, 0.7); add(fx, fire(A('s3', 4) + 0.6 - f0, 1.0), f0, 0.9)
    for k in range(5): add(fx, whoosh(0.5, 150, 700), f0 + 0.2 + k * 0.8, 0.45)
    # 肆：四组对招
    T = lambda k: A('s4', k)
    hit1 = T(1) + 0.9; curtain = CK('s4', 1, 1) + 0.1; hit2 = curtain + 0.9; hit3 = A('s4', 2) + 0.8
    add(fx, rumble(1.2, 50, 0.8), T(1) - 0.2, 0.8); add(fx, psum(crash(1.0) * 0.6, thunk()), hit1, 0.9)
    add(fx, whoosh(0.6, 300, 1800), curtain, 0.5); add(fx, thunk(0.3) * 0.3, hit2, 0.5); add(fx, thunk(0.3) * 0.3, hit3, 0.5)
    add(fx, whoosh(1.4, 200, 1200), T(4) + 0.2, 0.6); add(fx, fire(2.0, 0.8), T(4) + 0.4, 0.6)
    cut = A('s4', 5) - 0.25; add(fx, whoosh(0.3, 2000, 7000), cut, 0.8, 0.3); add(fx, clank_lite(), cut + 0.05, 0.5, 0.3); add(fx, whoosh(0.9, 800, 200), cut + 0.15, 0.6); add(fx, thunk(0.4) * 0.6, cut + 1.1, 0.6)
    burn = T(7) + 1.4; fallT = CK('s4', 7, 2) + 0.4; add(fx, fire(fallT - burn + 0.6, 0.7), burn, 0.6); add(fx, crash(2.4), fallT, 1.0)
    for k in range(6): add(fx, thunk(0.25) * 0.5, A('s4', 8) + 0.3 + k * 0.22, 0.6, rng.uniform(-0.3, 0.3))
    add(fx, rumble(2.6, 60, 1.0), T(10) + 0.5, 0.8)
    for k in range(2): add(fx, arrow_fly(0.4), CK('s4', 11, 2) + k * 0.5 - 0.2, 0.6, -0.4); add(fx, clank_lite(0.3), CK('s4', 11, 2) + k * 0.5 + 0.2, 0.35, 0.3)
    # 伍：夜风；悬赏令再射入
    add(amb, wind(S['s6']['start'] - S['s5']['start'], 1.0, 0.09), S['s5']['start'], 0.8)
    add(fx, arrow_fly(0.6), CK('s5', 10, 2) - 0.25, 0.35, -0.4); add(fx, thunk(), CK('s5', 10, 2) + 0.45, 0.3)     # 压在“你们何必陪他送死”上，放轻
    # 陆：风
    add(amb, wind(S['s7']['start'] - S['s6']['start'] + 1, 1.0, 0.12), S['s6']['start'], 0.9)
    # 柒：风声贯穿；歌词前后音乐收掉，只剩风（风在 hush 处略抬）
    w7 = wind(S['s8']['card'][0] - S['s7']['start'] + 1.5, 1.4, 0.1); tt = np.arange(len(w7)) / SR + S['s7']['start']
    up = lambda a, z: np.clip(np.minimum((tt - a) / 0.8, (z - tt) / 0.8), 0, 1)      # 只在歌词前的静场和念完后的两秒抬风，不压歌词
    w7 *= 1 + 1.0 * np.maximum(up(S['s7']['hush'] - 0.8, A('s7', 4) + 0.3), up(E('s7', 4) - 0.3, A('s7', 5) + 0.3))
    add(amb, w7, S['s7']['start'], 1.0)
    # 捌：侯景
    add(fx, whoosh(1.0, 300, 1600), CK('s8', 0, 2) + 0.3, 0.5)
    # 玖：斛律光之死一记低鼓；北周东征
    add(perc, taiko(42, 3.5, 1.3), CK('s9', 8, 1), 0.6)
    add(fx, rumble(A('s9', 10) - A('s9', 9), 40, 0.9), A('s9', 9) + 0.3, 0.8)
    # 收尾：雪夜的风
    add(amb, wind(TOTAL - S['s10']['start'], 1.0, 0.08), S['s10']['start'], 0.8)
    return reverb(perc, 2.0, 0.28) * 0.95 + reverb(fx, 1.4, 0.2) * 0.8, amb


def psum(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out


def dig(dur=0.4):
    n = int(dur * SR); tt = np.arange(n) / SR
    return taiko(90, dur, 0.2)[:n] * 0.4 + fft_filter(rng.normal(size=n) * np.exp(-tt / 0.04), 200, 1500, 2) * 0.4


def clank_lite(dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for f, d in ((1310, 0.06), (2140, 0.05), (3370, 0.035)): x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt / d)
    return x * 0.3


def ff(*a): subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', *a], check=True)


def measure_i(p):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])


def mixdown(music, out):
    """规范的侧链链路：旁白分两路，一路进混音，一路做侧链；音乐削 3 kHz、淡入 2 秒，与音效一起被压。"""
    pre, pre2, duck = f"{ROOT}/cache/premix.wav", f"{ROOT}/cache/premix2.wav", out.replace('.wav', '_bed.wav')
    ins = ['-i', f"{AU}/narration.wav", '-i', f"{AU}/fx.wav"] + (['-i', music] if music else [])
    g = f"[0:a]asplit=2[v][sc];[1:a]volume={FX_DB}dB[f];"
    # 音乐 + 音效整体晚 80 毫秒进入压缩器 = 侧链“前瞻” 80 毫秒：旁白一开口音乐已经压下去，句首第一个字不被盖住（80 毫秒的音画差察觉不到）
    if music: g += f"[2:a]volume={MUSIC_DB}dB,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2[m];[m][f]amix=inputs=2:duration=first:normalize=0,adelay=80|80,atrim=end={TOTAL:.3f}[bed];"
    else: g += f"[f]adelay=80|80,atrim=end={TOTAL:.3f}[bed];"
    g += (f"[bed][sc]sidechaincompress=threshold={SC['threshold']}:ratio={SC['ratio']}:attack={SC['attack']}:release={SC['release']},"
          f"afade=t=out:st={TL['total'] - 3:.2f}:d=3,asplit=2[d1][d2];"
          f"[v][d1]amix=inputs=2:duration=first:normalize=0[o]")
    ff(*ins, '-filter_complex', g, '-map', '[o]', '-c:a', 'pcm_f32le', pre, '-map', '[d2]', '-c:a', 'pcm_f32le', duck)
    # 先把整体增益推到 -16 LUFS 附近，同时用限幅器把样本峰值压在 -2.8 dBFS 以下（给真峰值留余量），
    # 再做 loudnorm 两遍：先测，再按实测值线性归一（不做动态压缩，保住音乐与人声的相对关系）
    g0 = -16.0 - measure_i(pre)
    ff('-i', pre, '-af', f"alimiter=level_in={10 ** (g0 / 20):.5f}:limit={10 ** (-2.8 / 20):.5f}:attack=3:release=60:level=false", '-c:a', 'pcm_f32le', pre2)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', pre2, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    tmp = out.replace('.wav', '.tmp.wav')            # 先写临时文件再原子替换：正在编码的 ffmpeg 读的旧文件不受影响
    r2 = subprocess.run(['ffmpeg', '-y', '-hide_banner', '-i', pre2, '-af', ln, '-ar', '48000', '-c:a', 'pcm_s24le', tmp], capture_output=True, text=True).stderr
    os.replace(tmp, out)
    m2 = json.loads(r2[r2.rindex('{'):r2.rindex('}') + 1])
    gain = g0 + float(m2['output_i']) - float(m2['input_i'])
    return dict(normalization_type=m2['normalization_type'], gain_db=round(gain, 2), pre_tp=m['input_tp'], pre_lra=m['input_lra']), duck, gain


def report(out, duck, gain, music):
    """核对：成片响度 / 真峰值；有旁白时音乐（含音效）比人声低多少；高潮留白处音乐抬到多少。"""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', out, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); LRA = float(re.findall(r'LRA:\s+(-?[\d.]+) LU', r)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
    k = 10 ** (gain / 20)
    v, _ = sf.read(f"{AU}/narration.wav"); b, _ = sf.read(duck); v = v * k; b = b * k
    vI = lufs(v)
    t, mv = blocks(v); _, mb = blocks(b); Lv = -0.691 + 10 * np.log10(mv + 1e-12); Lb = -0.691 + 10 * np.log10(mb + 1e-12)
    act = Lv > vI - 8; d = (Lb - Lv)[act]
    res = dict(mix_I=I, mix_LRA=LRA, mix_TP=TP, voice_I=round(vI, 1), under_voice_median=round(float(np.median(d)), 1),
               under_voice_p10=round(float(np.percentile(d, 10)), 1), under_voice_p90=round(float(np.percentile(d, 90)), 1))
    if music:
        def win(a, z): s = (t + 0.2 >= a) & (t + 0.2 <= z); return round(float(-0.691 + 10 * np.log10(mb[s].mean() + 1e-12) - vI), 1)
        res['climax_gap_vs_voice'] = win(E('s5', 13) + 0.3, A('s5', 14) - 0.1)
        res['s10_gap_vs_voice'] = win(E('s9', 11) + 0.3, A('s10', 0) - 0.1)
        res['card_s4_vs_voice'] = win(S['s4']['card'][0] + 0.2, S['s4']['card'][1])
        res['hush_vs_voice'] = win(S['s7']['hush'] + 0.1, A('s7', 4) - 0.05)
    return res


def main():
    os.makedirs(AU, exist_ok=True)
    nar = narration(); sf.write(f"{AU}/narration.wav", np.stack([nar, nar], 1), SR, subtype='FLOAT')
    ev, amb = fx(); vI = lufs(np.stack([nar, nar], 1))
    # 音效：最响的 3 秒比旁白低约 7 dB；环境风声：比旁白低约 21 dB（之后与音乐一起被旁白侧链压低）
    from loud import short_term
    ev *= 10 ** ((vI - 7 - short_term(ev)[1].max()) / 20)
    act = np.abs(amb).sum(1) > 1e-4; amb *= 10 ** ((vI - 21 - lufs(amb[act])) / 20)
    sf.write(f"{AU}/fx.wav", ev + amb, SR, subtype='FLOAT')
    out = {}
    for name, music in (('mix', f"{AU}/music.wav"), ('mix_nomusic', None)):
        if name == 'mix' and not os.path.exists(music): continue
        if name == 'mix_nomusic' and 'nomusic' not in sys.argv: continue
        ln, duck, gain = mixdown(music, f"{AU}/{name}.wav"); rep = report(f"{AU}/{name}.wav", duck, gain, music)
        out[name] = dict(loudnorm=ln, **rep); print(name, json.dumps(out[name], ensure_ascii=False), flush=True)
    json.dump(out, open(f"{ROOT}/cache/mix_report.json", 'w'), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
