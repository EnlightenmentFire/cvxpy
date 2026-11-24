# -*- coding: utf-8 -*-
"""按 TTS 前端同样的分词+注音流程，列出每句里多音字的实际读音，供人工核对。"""
import sys, os, re, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text, LEX
import jieba, jieba.posseg as psg, logging; jieba.setLogLevel(logging.ERROR)
from misaki import zh
g2p = zh.ZHG2P(version='1.1')            # 初始化 pypinyin 词库
from pypinyin import lazy_pinyin, pinyin, Style, load_phrases_dict
from lex import register; register(LEX)
COMMON = set('的了一不是在有人和这个们上来到大地为子中你说生国年着就那要得出也时可以会后能对于过家十用发天如然作方成者多日都三小军二无同么经法当起与好看学进种将还分此心前面又定见只主没公从')
only = [int(x) for x in sys.argv[1:]]
for i, l in enumerate(L):
    if only and i not in only: continue
    t = tts_text(l[2]); out = []
    for w, pos in psg.lcut(t):
        if not re.search(r'[一-鿿]', w): continue
        py = lazy_pinyin(w, style=Style.TONE, neutral_tone_with_five=True)
        for ch, p in zip(w, py):
            hs = pinyin(ch, heteronym=True, style=Style.TONE)[0]
            if len(hs) > 1 and (ch not in COMMON or only): out.append(f"{w}[{ch}={p}]")
    print(i, l[1], ' '.join(out))
