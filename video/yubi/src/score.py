# -*- coding: utf-8 -*-
"""配乐拼接（按《配乐规范》的三层起伏）：
  铺底：冷启动、壹（只有长音 / pad，很轻）
  推进：贰、叁（加入慢鼓）→ 肆（鼓点加紧）→ 伍（由推进续写到高潮；“人人有了拼死的心”后旁白停 2 秒，音乐单独出来）
  回落：陆（哀段）、柒前半；《敕勒歌》前音乐收掉，只留风声，直到捌的章节卡
  再起：捌（沉思）→ 玖（推进，续写到第二次抬起；“此人若在”之后留白）→ 收成埙独奏（拾、片尾），余音后黑场
片段来自 tools/musicgen_gen.py（MusicGen），各段之间 2–4 秒等功率交叉淡化；同一段内用“续写”接长，不循环。
选用的片段见 src/score_clips.json。输出 audio/music.wav（48 kHz 立体声；以 -20 LUFS 为 0 dB 基准排层次）。"""
import json, os, sys, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loud import lufs, short_term
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); MD = f"{ROOT}/cache/music"; SR = 48000
TL = json.load(open(f"{ROOT}/src/timeline.json")); S = TL['secs']; TOTAL = TL['total'] + 0.6; N = int(TOTAL * SR)
LN = lambda s, k: [l for l in TL['lines'] if l['sec'] == s and l['k'] == k][0]
A = lambda s, k: LN(s, k)['start']; E = lambda s, k: LN(s, k)['end']
CL = json.load(open(f"{ROOT}/src/score_clips.json"))
REF = -20.0
_cache = {}


def clip(name):
    """读入片段（32 kHz → 48 kHz），统一到 -20 LUFS。第一轮续写是直接拼接的，接缝处做 10 毫秒的淡出淡入去爆音。"""
    if name not in _cache:
        w, sr = sf.read(os.path.join(MD, name)); w = librosa.resample(w.T.astype(np.float32), orig_sr=sr, target_sr=SR).T
        for sec in CL.get('hard_seams', {}).get(name, []):
            i = int(sec * SR); n = int(0.005 * SR); r = np.cos(np.linspace(0, np.pi / 2, n))[:, None]
            w[i - n:i] *= r; w[i:i + n] *= r[::-1]
        _cache[name] = w * 10 ** ((REF - lufs(w)) / 20)
    return _cache[name]


def peak_time(w, lo=0.0, hi=None, win=2.0):
    """片段里最响的 win 秒窗口中心（在 [lo, hi] 秒之间找）。"""
    t, st = short_term(w, SR, win, 0.1); hi = hi if hi is not None else len(w) / SR
    ok = (t >= lo) & (t <= hi); return float(t[ok][np.argmax(st[ok])])


def place(buf, w, t0, t1, at, fin, fout):
    """把片段 w 从“片段时间 at”起，放到时间轴 [t0, t1]；首尾各做 fin / fout 秒等功率淡入淡出。"""
    i0, i1 = int(t0 * SR), int(t1 * SR); j0 = int(at * SR); n = min(i1 - i0, len(w) - j0)
    assert n > 0 and j0 >= 0, (t0, t1, at, len(w) / SR)
    if n < i1 - i0: print(f'  ! 片段不够长：缺 {(i1 - i0 - n) / SR:.1f} 秒（{t0:.1f}–{t1:.1f}）')
    x = w[j0:j0 + n].copy(); tt = np.arange(n) / SR
    if fin > 0: x *= np.sin(np.pi / 2 * np.clip(tt / fin, 0, 1))[:, None]
    if fout > 0: x *= np.cos(np.pi / 2 * np.clip((tt - (n / SR - fout)) / fout, 0, 1))[:, None]
    buf[i0:i0 + n] += x


def build():
    mus = np.zeros((N, 2)); X = 3.0; card = lambda s: S[s]['card'][0]; cues = []
    def cue(use, t0, t1, at=0.0, fin=X, fout=X): cues.append((use, t0, t1, at, fin, fout))
    # 铺底：冷启动是一支稀疏的埙（与片尾的埙独奏首尾呼应），片名鼓点处交叉进 pad，一直铺到壹段结束（开头的 2 秒淡入在混音链里做）
    cue('cold', 0.0, S['title']['start'] + 1.5, CL.get('cold_at', 0.0), 0, X)
    cue('bed', S['title']['start'] - 1.5, card('s2') + 1.5, CL.get('bed_at', 0.0))
    # 推进
    cue('build_a', card('s2') - 1.5, card('s3') + 1.0, CL.get('build_a_at', 0.0), X, 1.8)
    cue('build_b', card('s3') - 0.8, card('s4') + 1.0, CL.get('build_b_at', 0.0), 1.8, 1.5)     # 叁段 28 秒，一条 30 秒的片段正好够
    cue('drive', card('s4') - 0.5, card('s5') + 1.0, CL.get('drive_at', 0.0), 1.5, 2.0)          # 肆段 60 秒：30 秒片段 + 30 秒续写
    def aligned(use, t0, t1, tgt, fin=X, fout=X):
        """长片段里最响的 2 秒（只在能放得下的范围里找）对到时间轴上的 tgt。"""
        w = clip(CL[use]); L = len(w) / SR; lo, hi = tgt - t0, L - (t1 - tgt)
        if hi < lo: raise SystemExit(f'{use}: 片段 {L:.1f}s 太短，至少要 {t1 - t0:.1f}s')
        p = CL.get(use + '_peak') or peak_time(w, lo, hi); cue(use, t0, t1, p - (tgt - t0), fin, fout)
    # 伍：一条“推进→高潮”的续写长片段；最响的 2 秒对到“人人有了拼死的心”之后的留白
    aligned('s5', card('s5') - 1.0, card('s6') + 1.5, (E('s5', 13) + A('s5', 14)) / 2, 2.0, X)
    # 陆、柒前半：哀段；柒在《敕勒歌》前 0.6 秒起用 0.9 秒收掉
    cue('lament_a', card('s6') - 1.5, card('s7') + 1.5, CL.get('lament_a_at', 0.0))
    cue('lament_b', card('s7') - 1.5, S['s7']['hush'] + 0.3, CL.get('lament_b_at', 0.0), X, 0.9)
    # 捌：音乐在章节卡处回来
    cue('reflect', card('s8') + 1.3, card('s9') + 1.5, CL.get('reflect_at', 0.0), 3.0, X)
    # 玖：推进→第二次抬起的续写长片段；最响处对到“此人若在”之后的留白
    coda0 = A('s10', 0) - 1.2
    aligned('s9', card('s9') - 1.5, coda0 + 3.0, (E('s9', 11) + A('s10', 0)) / 2, X, 3.0)
    # 收尾：埙独奏，余音进片尾
    cue('coda', coda0, TOTAL, CL.get('coda_at', 0.0), 3.0, 0)
    for use, t0, t1, at, fin, fout in cues:
        place(mus, clip(CL[use]), t0, t1, at, fin, fout); print(f'{use:9s} {t0:6.1f}–{t1:6.1f}  片段 {CL[use]} 自 {at:.1f}s')
    # 先把片段自身的大起大落收一点（3 秒短时响度向 -20 LUFS 拉回 60%），层次交给下面的段落增益
    t = np.arange(N) / SR
    t2, st = short_term(mus, SR, 3.0, 0.1)
    corr = np.where(st > -45, np.clip(-0.6 * (st - REF), -8, 6), 0.0); k = 15; corr = np.convolve(corr, np.ones(k) / k, 'same')
    mus *= (10 ** (np.interp(t, t2, corr) / 20))[:, None]
    # 层次（相对 -20 LUFS 的增益，dB）：铺底轻，推进略抬，高潮全编制；留白处再抬一点
    K = [(0, -8), (S['title']['start'], -7), (card('s2') - 1, -7), (card('s2') + 2, -5), (card('s4'), -4.5), (card('s4') + 2, -3.5),
         (card('s5') - 1, -3.5), (card('s5') + 2, -6), (A('s5', 10), -4.5), (A('s5', 12), -2.5),
         (E('s5', 13) - 0.2, -2), (E('s5', 13) + 0.4, -0.5), (A('s5', 14) - 0.3, -0.5), (A('s5', 14) + 0.5, -3), (card('s6') - 1, -3.5),
         (card('s6') + 2, -6), (card('s7') + 2, -7), (card('s8'), -8), (card('s9') + 2, -7), (A('s9', 8), -5), (A('s9', 10), -3),
         (E('s9', 11) - 0.2, -3), (E('s9', 11) + 0.4, -1.5), (A('s10', 0) - 0.5, -1.5), (A('s10', 0) + 1.5, -5), (S['end']['start'], -6), (TOTAL, -8)]
    g = np.interp(t, [k[0] for k in K], [k[1] for k in K]); mus *= (10 ** (g / 20))[:, None]
    # 柒：歌词前后只留风声（风在 fx 轨里）
    h0, h1 = S['s7']['hush'] - 0.6, S['s8']['card'][0]
    mus *= (1 - np.clip((t - h0) / 0.9, 0, 1) * (t < h1))[:, None]
    sf.write(f"{ROOT}/audio/music.wav", mus.astype(np.float32), SR, subtype='FLOAT')
    t2, st = short_term(mus, SR, 3.0, 0.5)
    print('music.wav', f'{TOTAL:.1f}s', 'LUFS %.1f' % lufs(mus), ' 各段短时响度中位：', {s: round(float(np.median(st[(t2 >= S[s]['start']) & (t2 < S[s].get('end', TOTAL))])), 1) for s in ('cold', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10')})


if __name__ == '__main__':
    build()
