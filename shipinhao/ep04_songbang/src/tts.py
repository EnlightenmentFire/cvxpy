# -*- coding: utf-8 -*-
"""旁白合成：Kokoro-82M v1.1-zh（Apache-2.0）。
逐句合成 → 去首尾静音 → 用模型输出的时长(pred_dur)把每个分句对齐到时间 → 写出 narration.wav + timeline.json
用法: python tts.py --voice zm_011 --speed 1.05 [--only 0.1,0.2] [--out audio/xxx]
"""
import argparse, json, os, re, sys
import numpy as np, soundfile as sf, torch

sys.path.insert(0, os.path.dirname(__file__))
from script import L

SR = 24000
PUNC = "，。；：？！、"
REPO = "hexgrad/Kokoro-82M-v1.1-zh"

# 读音修正：直接改音素串（注音+声调），只影响读音，不影响字幕。逐条依据见 g2p_check.py 的输出。
PATCH = [
    ("ㄧ4ㄐ又3ㄅㄚ1ㄙㄭ4", "ㄧ1ㄐ又3ㄅㄚ1ㄙㄭ4"),      # 一九八四：yī
    ("ㄘㄥ2ㄘㄥ5", "ㄘㄥ2ㄘㄥ2"),                  # 层层：céng céng
    ("ㄉㄧ4/ㄧ2阳4", "ㄉㄧ4ㄧ1/阳4"),              # 第一样：dì yī
    ("ㄧ2ㄅㄟ5ㄗㄭ5", "ㄧ2ㄅㄟ4ㄗㄭ5"),              # 一辈子：bèi
    ("ㄕㄤ4ㄒ压5/ㄈㄨ2ㄉ中4", "ㄕㄤ4ㄒ压4/ㄈㄨ2ㄉ中4"),  # 上下浮动：xià
    ("ㄐ月2ㄅㄨ4/ㄕ十4", "ㄐ月2/ㄅㄨ2ㄕ十4"),          # 绝不是：bú shì
    ("ㄓㄣ1ㄕ十5", "ㄓㄣ1ㄕ十4"),                  # 真是：shì
    ("ㄌㄠ3ㄆㄛ5ㄆㄛ5", "ㄌㄠ3ㄆㄛ2ㄆㄛ5"),          # 老婆婆：lǎo pó po
    ("ㄉ中4ㄊㄢ5ㄅㄨ5ㄉㄜ5", "ㄉ中4ㄊㄢ5ㄅㄨ5ㄉㄜ2"),  # 动弹不得：dé
    ("ㄊ中1ㄊ中5", "ㄊ中1ㄊ中1"),                  # 通通：tōng tōng
]


def patch_ps(ps):
    for x, y in PATCH:
        ps = ps.replace(x, y)
    return ps


def split_clauses(marked):
    """把带标记文本切成分句：[(display, spoken, punc)]"""
    out, buf, depth = [], "", 0
    for ch in marked:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        buf += ch
        if depth == 0 and ch in PUNC:
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    res = []
    for c in out:
        disp = re.sub(r"\{([^|}]*)\|([^}]*)\}", r"\1", c)
        spk = re.sub(r"\{([^|}]*)\|([^}]*)\}", r"\2", c)
        spk = re.sub(r"[「」《》]", "", spk)
        res.append((disp, spk))
    # 引号收尾：把只剩引号的碎片并回上一句
    merged = []
    for d, s in res:
        if merged and not re.sub(r"[%s\s]" % PUNC, "", s):
            merged[-1] = (merged[-1][0] + d, merged[-1][1] + s)
        else:
            merged.append((d, s))
    return merged


def trim(w, thr=0.012, pad=0.04):
    env = np.abs(w)
    k = int(SR * 0.01)
    env = np.convolve(env, np.ones(k) / k, "same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return w, 0
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(w), idx[-1] + int(pad * SR * 2))
    return w[a:b], a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="zm_011")
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="audio/narration")
    ap.add_argument("--nogap", action="store_true")
    a = ap.parse_args()
    from kokoro import KModel, KPipeline

    model = KModel(repo_id=REPO).to("cpu").eval()
    pipe = KPipeline(lang_code="z", repo_id=REPO, model=model)
    only = set(a.only.split(",")) if a.only else None

    track, tl, t = [], [], 0.0
    lead = 0.5 if not only else 0.2
    track.append(np.zeros(int(lead * SR), dtype=np.float32))
    t = lead
    for ln in L:
        if only and ln["id"] not in only:
            continue
        clauses = split_clauses(ln["text"])
        # 按句号类切成"句"，每句单独合成
        sents, cur = [], []
        for d, s in clauses:
            cur.append((d, s))
            if s[-1] in "。？！":
                sents.append(cur)
                cur = []
        if cur:
            sents.append(cur)
        line_start = t
        cl_out = []
        for si, sent in enumerate(sents):
            text = "".join(s for _, s in sent)
            ps, _ = pipe.g2p(text)
            ps = patch_ps(ps)
            assert len(ps) < 500, (ln["id"], len(ps))
            n_ps = len(ps)
            spd = a.speed * (1.0 if n_ps <= 83 else max(0.86, 1 - (n_ps - 83) / 500))  # 长句防抢拍
            wavs, phs, durs = [], "", []
            for r in pipe.generate_from_tokens(ps, voice=a.voice, speed=spd):
                w = r.audio.numpy().astype(np.float32)
                pd = r.pred_dur.numpy().astype(float)
                spf = len(w) / pd.sum()
                # token i (0=BOS) ↔ phoneme char i-1
                off = sum(len(x) for x in wavs)
                cum = np.cumsum(pd) * spf + off
                phs += r.phonemes
                durs += list(cum[1 : 1 + len(r.phonemes)])
                wavs.append(w)
            w = np.concatenate(wavs)
            w2, a0 = trim(w)
            # 分句边界：音素串里的标点
            pidx = [i for i, ch in enumerate(phs) if ch in ",.!?;:、，。？！；："]
            n = len(sent)
            if len(pidx) >= n and all(i < len(durs) for i in pidx):
                # 取前 n-1 个内部边界 + 结尾
                inner = [durs[i] for i in pidx[: n - 1]] if len(pidx) == n else None
            else:
                inner = None
            if inner is None:
                # 回退：按字数比例
                lens = np.array([max(1, len(re.sub(r"[%s]" % PUNC, "", s))) for _, s in sent], float)
                inner = list((np.cumsum(lens) / lens.sum() * len(w2) + a0)[:-1])
                method = "prop"
            else:
                method = "dur"
            bounds = [a0] + [min(max(b, a0), a0 + len(w2)) for b in inner] + [a0 + len(w2)]
            for ci, (d, s) in enumerate(sent):
                cl_out.append(dict(text=d, start=round(t + (bounds[ci] - a0) / SR, 3), end=round(t + (bounds[ci + 1] - a0) / SR, 3), m=method))
            track.append(w2)
            t += len(w2) / SR
            if si < len(sents) - 1:
                g = 0.32
                track.append(np.zeros(int(g * SR), dtype=np.float32))
                t += g
        line_end = t
        tl.append(dict(id=ln["id"], scene=ln["scene"], start=round(line_start, 3), end=round(line_end, 3), gap=ln["gap"], clauses=cl_out, src=ln["src"]))
        g = 0.3 if a.nogap else ln["gap"]
        track.append(np.zeros(int(g * SR), dtype=np.float32))
        t += g
        print(ln["id"], "%.2f-%.2f" % (line_start, line_end), [c["m"] for c in cl_out], flush=True)
    wav = np.concatenate(track)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    sf.write(a.out + ".wav", wav, SR)
    json.dump(dict(voice=a.voice, speed=a.speed, total=round(len(wav) / SR, 3), lines=tl), open(a.out + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("total %.2fs" % (len(wav) / SR))


if __name__ == "__main__":
    main()
