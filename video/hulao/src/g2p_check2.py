import sys, os, re, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text, LEX
import jieba, jieba.posseg as psg, logging; jieba.setLogLevel(logging.ERROR)
from misaki import zh
g2p = zh.ZHG2P(version='1.1')
from pypinyin import lazy_pinyin, Style
from lex import register; register(LEX)
CH = set(sys.argv[1]) if len(sys.argv) > 1 else set('将为还得都与行分当只没重降率载处强称传相数少好长更曾创丧难干冠尽期恶')
for i, l in enumerate(L):
    t = tts_text(l[2]); out = []
    for w, pos in psg.lcut(t):
        py = lazy_pinyin(w, style=Style.TONE, neutral_tone_with_five=True)
        if len(py) != len(w): continue
        for ch, p in zip(w, py):
            if ch in CH: out.append(f"{w}[{ch}={p}]")
    if out: print(i, l[1], ' '.join(out))
