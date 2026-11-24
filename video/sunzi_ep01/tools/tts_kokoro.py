# -*- coding: utf-8 -*-
"""逐行合成旁白（Kokoro-82M v1.1-zh，Apache-2.0）。

用法（在装了 kokoro / misaki[zh] 的环境里）：
  python tools/tts_kokoro.py --voice zm_010 --out build/vo_zm_010 [--only s1] [--dump]
--dump 只打印每行分词与读音，供多音字人工检查，不合成。
"""
import argparse, json, os, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import script as S

REPO = "hexgrad/Kokoro-82M-v1.1-zh"
SR = 24000


def tts_text(sub, opt):
    t = sub
    for a, b in opt.get("rep", {}).items():
        assert a in t, (a, t)
        t = t.replace(a, b)
    t = t.replace("「", "").replace("」", "").replace("《", "").replace("》", "")
    t = t.replace("·", "，").replace("——", "，")
    return t


def dump():
    from misaki.zh_frontend import ZHFrontend
    import jieba.posseg as psg
    from pypinyin import lazy_pinyin, Style
    fe = ZHFrontend()
    for seg, lid, kind, sub, opt in S.iter_lines():
        t = tts_text(sub, opt)
        out = []
        for w, pos in fe.tone_modifier.pre_merge_for_modify(psg.lcut(t)):
            if re.match(r"[一-鿿]", w):
                py = lazy_pinyin(w, style=Style.TONE3, neutral_tone_with_five=True)
                out.append(f"{w}[{' '.join(py)}]")
            else:
                out.append(w)
        print(lid, kind, " ".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="zm_010")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--qspeed", type=float, default=None, help="文言行语速（默认 speed*0.93）")
    ap.add_argument("--out", default=str(ROOT / "build" / "vo"))
    ap.add_argument("--only", default=None, help="只合成某段，如 s1")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.dump:
        return dump()
    import numpy as np, torch, soundfile as sf
    torch.set_num_threads(4)
    from kokoro import KModel, KPipeline
    model = KModel(repo_id=REPO).to("cpu").eval()
    pipe = KPipeline(lang_code="z", repo_id=REPO, model=model)
    os.makedirs(a.out, exist_ok=True)
    qs = a.qspeed or a.speed * 0.93
    meta = {}
    mpath = os.path.join(a.out, "meta.json")
    if os.path.exists(mpath):
        meta = json.load(open(mpath, encoding="utf-8"))
    for seg, lid, kind, sub, opt in S.iter_lines():
        if a.only and seg not in a.only.split(","):
            continue
        t = tts_text(sub, opt)
        wav = os.path.join(a.out, lid + ".wav")
        if os.path.exists(wav) and not a.force and meta.get(lid, {}).get("tts") == t:
            continue
        sp = qs if kind == "q" else a.speed
        chunks = [r.audio.numpy() for r in pipe(t, voice=a.voice, speed=sp)]
        w = np.concatenate(chunks).astype("float32")
        # 去首尾静音，统一留 40ms / 80ms
        env = np.abs(w)
        thr = max(0.01, env.max() * 0.02)
        idx = np.where(env > thr)[0]
        if len(idx):
            w = w[max(0, idx[0] - int(0.03 * SR)): min(len(w), idx[-1] + int(0.06 * SR))]
        sf.write(wav, w, SR)
        meta[lid] = {"tts": t, "dur": len(w) / SR, "voice": a.voice, "speed": sp}
        print(lid, f"{len(w)/SR:5.2f}s", t, flush=True)
        json.dump(meta, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
