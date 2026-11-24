# -*- coding: utf-8 -*-
"""回听质检 + 字幕对齐：用 Whisper 转写每段配音，与稿子按拼音比对；并给出每个字幕块的起始时间。"""
import sys, json, re, os, difflib, numpy as np, soundfile as sf
sys.path.insert(0, '/home/user/work/vid')
from script import BEATS, say_text
from timeline import chunks, nchar
from pypinyin import lazy_pinyin
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
m = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get('ASR_THREADS', '4')))
def load(f):
    a, sr = sf.read(f, dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    return resample_poly(a, 16000, sr).astype('float32') if sr != 16000 else a
def cjk(s): return re.findall(r'[一-鿿]', s)
def norm(p):  # 模糊音归一
    p = re.sub(r'^(zh|ch|sh)', lambda k: k.group(1)[0], p); p = re.sub(r'ng$', 'n', p); return p
OKP = {('撰','传'),('督','都'),('环','还'),('末','没'),('己','给'),('位','为'),('翔','降'),('鲁','橹'),('鲁','橹'),('居','沮'),('俊','濬'),('俊','浚'),('洁','孑'),('匠','将'),('吊','调'),('屈','曲'),('擒','禽'),('糜','麋')}
only = sys.argv[1:]
align = json.load(open('align.json')) if os.path.exists('align.json') else {}
rep = json.load(open('qc.json')) if os.path.exists('qc.json') else {}
for b in BEATS:
    bid = b['id']; f = f'wav/{bid}.wav'
    if only and bid not in only: continue
    if not os.path.exists(f): continue
    if not only and bid in rep and rep[bid].get('mtime') == os.path.getmtime(f): continue
    segs, info = m.transcribe(load(f), language='zh', word_timestamps=True, initial_prompt='以下是普通话的句子。三国志，关羽，糜芳，士仁，吕蒙，陆逊，于禁，曹仁，樊城，江陵。', condition_on_previous_text=False)
    A = []
    for s in segs:
        for w in s.words:
            cs = cjk(w.word)
            for i, ch in enumerate(cs): A.append((ch, w.start + (w.end - w.start) * i / max(1, len(cs)), w.end))
    Ech = cjk(say_text(b)); Ep = [norm(x) for x in lazy_pinyin(Ech)]; Ap = [norm(x) for x in lazy_pinyin([a[0] for a in A])]
    sm = difflib.SequenceMatcher(None, Ep, Ap, autojunk=False)
    tmap = [None] * len(Ech); matched = 0; last_end = None
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): tmap[blk.a + k] = A[blk.b + k][1]; matched += 1; last_end = A[blk.b + k][2]
    ratio = matched / max(1, len(Ech))
    # 未匹配的字按相邻插值
    idx = [i for i, v in enumerate(tmap) if v is not None]
    if idx:
        tm = np.interp(range(len(tmap)), idx, [tmap[i] for i in idx]).tolist()
    else: tm = [0.0] * len(tmap)
    starts = []; off = 0
    for (s, q, n) in chunks(b['text']):
        k = len(cjk(s)); starts.append(tm[min(off, len(tm) - 1)] if tm else None); off += len(cjk(s)) if True else n
    # chunks() 里文本经过了标点裁剪，但汉字数不变，可直接累加
    align[bid] = starts
    miss = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal' and (''.join(Ech[i1:i2]), ''.join(a[0] for a in A[j1:j2])) not in OKP: miss.append((''.join(Ech[i1:i2]), ''.join(a[0] for a in A[j1:j2])))
    dur = sf.info(f).duration
    rep[bid] = dict(ratio=round(ratio, 3), miss=miss, last_end=last_end, tail=''.join(x[0] for x in A[sm.get_matching_blocks()[-2].b + sm.get_matching_blocks()[-2].size:]) if len(sm.get_matching_blocks()) > 1 else '', asr=''.join(a[0] for a in A), mtime=os.path.getmtime(f), dur=dur, n=len(Ech))
    print(bid, round(ratio, 2), round(dur, 1), miss, flush=True)
    json.dump(align, open('align.json', 'w')); json.dump(rep, open('qc.json', 'w'), ensure_ascii=False, indent=1)
