# -*- coding: utf-8 -*-
"""Qwen3-TTS 逐句合成旁白（可断点续跑）。

python qnarr.py OUTDIR [行id,行id,...]

每个片段：最多 5 个 seed；通过条件 = 中位音高 85–105 Hz 且 ASR（Whisper 回读，Paraformer 复核）
无调拼音相似度 ≥ 0.9 且关键词全部读对。都不通过时取最好的一条，并写进报告。
"""
import json
import os
import re
import sys
import time

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qtts  # noqa: E402
import script  # noqa: E402
from tts import split_line  # noqa: E402

SR = qtts.SR
TEMPO_NARR = float(os.environ.get("TEMPO_NARR", "1.3"))
TEMPO_QUOTE = float(os.environ.get("TEMPO_QUOTE", "1.16"))
PAUSE_CAP = 0.4
SEEDS = [1234, 2345, 3456, 4567, 5678, 6789, 7890]

# 关键词：必须在 ASR 拼音里找到（任一 ASR 命中即可）
KEYWORDS = ["京口", "建康", "刘裕", "桓玄", "北府", "王谧", "刁逵", "樗蒲", "寄奴", "魏书", "宋书", "通鉴", "社钱",
            "覆舟山", "罗落桥", "江乘", "皇甫敷", "吴甫之", "何无忌", "孟昶", "桓修", "桓谦", "刘牢之", "萧方等",
            "赵翼", "王愉", "素族", "寒人", "门阀", "豪强", "海盐", "孙恩", "石头城", "还不上", "还钱", "长刀",
            "称力", "辟易", "瞋目", "矫情", "刀把子", "淝水", "孙无终", "竹里", "镇江", "南京", "姨母", "奶妈"]

_PF = {}


def paraformer(wav):
    if "m" not in _PF:
        from funasr import AutoModel
        _PF["m"] = AutoModel(model="paraformer-zh", disable_update=True, hub="hf", log_level="ERROR")
    import librosa
    w16 = librosa.resample(wav.astype(np.float32), orig_sr=SR, target_sr=16000)
    r = _PF["m"].generate(input=w16)
    return r[0]["text"].replace(" ", "")


def contains(seq, sub):
    n = len(sub)
    return any(seq[i:i + n] == sub for i in range(len(seq) - n + 1)) if n else True


def check(display, wav):
    want = qtts.syllables(display)
    wt, words = qtts.asr(wav)
    sw = qtts.syllables(wt)
    sim_w = qtts.similarity(want, sw)
    pt = paraformer(wav)
    sp = qtts.syllables(pt)
    sim_p = qtts.similarity(want, sp)
    keys = [k for k in KEYWORDS if k in display]
    bad = []
    for k in keys:
        ks = qtts.syllables(k)
        if not (contains(sw, ks) or contains(sp, ks)):
            bad.append(k)
    return dict(whisper=wt, paraformer=pt, sim_w=round(sim_w, 3), sim_p=round(sim_p, 3),
                sim=round(max(sim_w, sim_p), 3), bad_keys=bad, words=words)


def synth_segment(display, is_quote, log, seeds=None, target=None):
    ttxt = qtts.tts_text(display)
    best = None
    tries = []
    for seed in (seeds or SEEDS[: qtts.MAX_TRIES]):
        t0 = time.time()
        w = qtts.gen(ttxt, seed)
        w = qtts.trim_and_cap(w, cap=PAUSE_CAP)
        f0 = qtts.median_f0(w)
        c = check(display, w)
        nhan = len(re.findall(r"[\u4e00-\u9fff0-9]", display))
        ok_f0 = (qtts.F0_LO <= f0 <= qtts.F0_HI) if nhan >= 8 else (75 <= f0 <= 115)
        ok_asr = c["sim"] >= qtts.ASR_OK and not c["bad_keys"]
        info = dict(seed=seed, f0=round(f0, 1), raw_dur=round(len(w) / SR, 2), secs=round(time.time() - t0, 1),
                    **{k: v for k, v in c.items() if k != "words"})
        tries.append(dict(info))
        log(f"    seed {seed}: f0={f0:5.1f} simW={c['sim_w']:.3f} simP={c['sim_p']:.3f} bad={c['bad_keys']} "
            f"({info['secs']}s)  P:{c['paraformer']}")
        if target is not None:
            ok_f0 = abs(f0 - target) < 6
        score = (ok_f0 and ok_asr, ok_asr, ok_f0, -abs(f0 - (target or 95)), c["sim"])
        if best is None or score > best[0]:
            best = (score, w, info, c["words"])
        if ok_f0 and ok_asr:
            break
    _, w, info, words = best
    tempo = TEMPO_QUOTE if is_quote else TEMPO_NARR
    w2 = qtts.stretch(w, tempo)
    w2 = qtts.trim_and_cap(w2, cap=PAUSE_CAP)
    words = [(x, a / tempo, b / tempo) for x, a, b in words]
    info.update(tries=tries, ok=bool(best[0][0]), tempo=tempo, dur=round(len(w2) / SR, 2))
    return w2, info, words


QUOTE_MIN = 4


def split_line_q(text):
    """Qwen 用的分段：引文（≥4 字的「」）单独成段，慢读；人名之类的短「」留在句中；
    引文前 ≤4 字的引子并进引文段，避免两三个字单独合成。"""
    # 先把短「」换成普通引号，再交给原来的切分
    def demote(m):
        inner = m.group(1)
        return ("「" + inner + "」") if len(re.findall(r"[\u4e00-\u9fff]", inner)) >= QUOTE_MIN else ("“" + inner + "”")
    t2 = re.sub(r"「([^」]*)」", demote, text)
    pieces = split_line(t2)
    merged = []
    for seg, is_q, pause in pieces:
        if merged and is_q and not merged[-1][1] and len(re.findall(r"[\u4e00-\u9fff]", merged[-1][0])) <= 4 \
                and not merged[-1][0].endswith(("。", "？", "！")):
            prev = merged.pop()
            merged.append((prev[0] + seg, True, pause))
        else:
            merged.append((seg, is_q, pause))
    return merged


def char_times(display, words, dur, t_off):
    """把 Whisper 的逐字时间对到原文的每个内容字上；对不上的按比例插值"""
    han = re.findall(r"[一-鿿0-9]", display)
    n = len(han)
    if n == 0:
        return []
    # ASR 字序列
    asr_chars = []
    for wd, a, b in words:
        cs = re.findall(r"[一-鿿0-9]", wd)
        for i, ch in enumerate(cs):
            asr_chars.append((ch, a + (b - a) * i / len(cs), a + (b - a) * (i + 1) / len(cs)))
    want = qtts.syllables(display)
    got = qtts.syllables("".join(c for c, _, _ in asr_chars))
    times = [None] * n
    if len(want) == n and len(got) == len(asr_chars):
        import difflib
        sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
                for k in range(i2 - i1):
                    times[i1 + k] = asr_chars[j1 + k][1:]
    # 插值补齐
    for i in range(n):
        if times[i] is None:
            prev = next((j for j in range(i - 1, -1, -1) if times[j] is not None), None)
            nxt = next((j for j in range(i + 1, n) if times[j] is not None), None)
            a0 = times[prev][1] if prev is not None else 0.0
            b0 = times[nxt][0] if nxt is not None else dur
            ia = prev if prev is not None else -1
            ib = nxt if nxt is not None else n
            span = (b0 - a0) / (ib - ia)
            times[i] = (a0 + span * (i - ia - 1 + 0.0), a0 + span * (i - ia))
    return [(han[i], t_off + times[i][0], t_off + times[i][1]) for i in range(n)]


def run(outdir, ids=None):
    os.makedirs(outdir, exist_ok=True)
    rep_path = os.path.join(outdir, "report.json")
    report = json.load(open(rep_path)) if os.path.exists(rep_path) else {}
    meta_path = os.path.join(outdir, "meta.json")
    meta = {m["id"]: m for m in json.load(open(meta_path))} if os.path.exists(meta_path) else {}
    logf = open(os.path.join(outdir, "log.txt"), "a")

    def log(s):
        print(s, flush=True)
        logf.write(s + "\n"); logf.flush()

    for d in script.LINES:
        if ids and d["id"] not in ids:
            continue
        if d["id"] in meta and os.path.exists(os.path.join(outdir, d["id"] + ".wav")):
            continue
        log(f"[{d['id']}] {d['text']}")
        pieces = split_line_q(d["text"])
        segs = []   # (wav, words, info)
        for seg, is_q, pause in pieces:
            log(f"  seg{'(引)' if is_q else ''}: {seg}")
            w, info, words = synth_segment(seg, is_q, log)
            segs.append([w, words, dict(text=seg, quote=is_q, **info)])

        def assemble():
            wavs, words_all, t = [], [], 0.0
            for k, ((seg, is_q, pause), (w, words, info)) in enumerate(zip(pieces, segs)):
                for ch, a, b in char_times(seg, words, len(w) / SR, t):
                    words_all.append([ch, a, b, is_q])
                wavs.append(w); t += len(w) / SR
                p = min(PAUSE_CAP, pause)
                if p and k < len(pieces) - 1:
                    wavs.append(np.zeros(int(p * SR), np.float32)); t += p
            return np.concatenate(wavs).astype(np.float32), words_all

        wav, words_all = assemble()
        lf0 = qtts.median_f0(wav)
        rounds = 0
        while not (qtts.F0_LO <= lf0 <= qtts.F0_HI) and rounds < 2:
            rounds += 1
            low = lf0 < qtts.F0_LO
            order = sorted(range(len(segs)), key=lambda i: segs[i][2]["f0"] if low else -segs[i][2]["f0"])
            i = order[0]
            log(f"  整句中位音高 {lf0:.1f} Hz 超范围，重做第 {i+1} 段（{segs[i][2]['f0']} Hz）")
            seg, is_q, _ = pieces[i]
            w, info, words = synth_segment(seg, is_q, log, seeds=[8901 + 111 * rounds + k for k in range(4)], target=95.0)
            cand = list(segs); cand[i] = [w, words, dict(text=seg, quote=is_q, **info)]
            old = segs; segs = cand
            wav2, words2 = assemble()
            f2 = qtts.median_f0(wav2)
            if abs(f2 - 95) < abs(lf0 - 95):
                wav, words_all, lf0 = wav2, words2, f2
            else:
                segs = old
        log(f"  整句中位音高 {lf0:.1f} Hz")
        infos = [x[2] for x in segs]
        sf.write(os.path.join(outdir, d["id"] + ".wav"), wav, SR)
        meta[d["id"]] = dict(id=d["id"], dur=len(wav) / SR, words=words_all, f0=round(lf0, 1))
        report[d["id"]] = infos
        json.dump(list(meta.values()), open(meta_path, "w"), ensure_ascii=False, indent=1)
        json.dump(report, open(rep_path, "w"), ensure_ascii=False, indent=1)
        log(f"  => {len(wav)/SR:.2f}s")


if __name__ == "__main__":
    out = sys.argv[1]
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    run(out, ids)
