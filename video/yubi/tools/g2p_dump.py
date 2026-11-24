# 打印每句 TTS 文本经 Kokoro(misaki-zh) 前端后的拼音/音素，用于人工检查多音字
import sys, os, re, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from script import L, tts_text
from misaki.zh_frontend import ZHFrontend
import jieba.posseg as psg
from pypinyin import lazy_pinyin, Style
fe = ZHFrontend()
for i, l in enumerate(L):
    t = tts_text(l[2]); out = []
    try:
        ws = fe.tone_modifier.pre_merge_for_modify(psg.lcut(t))
    except Exception:
        ws = [(w.word, w.flag) for w in psg.cut(t)]
    for w, pos in ws:
        if re.match(r'[一-鿿]', w): out.append(f"{w}[{' '.join(lazy_pinyin(w, style=Style.TONE3, neutral_tone_with_five=True))}]")
        else: out.append(w)
    print(i, l[1], ' '.join(out))
