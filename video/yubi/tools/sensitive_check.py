# -*- coding: utf-8 -*-
"""出片前自查：旁白 / 字幕（script.py）与画面文字（src/*.js 里的字符串）里有没有敏感词或现代影射词。"""
import os, re, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from script import L, SECTIONS
WORDS = ['专制', '独裁', '暴政', '极权', '政变', '革命', '民主', '自由', '人权', '主席', '总书记', '共产', '国民党', '领袖', '伟大', '万岁', '党',
         '台湾', '西藏', '新疆', '香港', '六四', '天安门', '文革', '大跃进', '饥荒', '法轮', '屠杀', '血洗', '屠城', '镇压', '维稳', '审查', '翻墙',
         '习', '毛', '邓', '江泽', '胡锦', '温家', '李克', '彭', '薄', '周永', '令计', '今天', '如今', '当下', '现在的', '现代', '我们今天', '影射', '暗示']
texts = [('旁白', l[2]) for l in L] + [('章节', s[2]) for s in SECTIONS]
for f in glob.glob(os.path.join(ROOT, 'src', '*.js')):
    for m in re.findall(r"'([^'\n]*[一-鿿][^'\n]*)'|`([^`\n]*[一-鿿][^`\n]*)`|\"([^\"\n]*[一-鿿][^\"\n]*)\"", open(f).read()):
        texts.append((os.path.basename(f), ''.join(m)))
hits = [(src, w, t) for src, t in texts for w in WORDS if w in t]
for h in hits: print('HIT', h[0], h[1], '|', h[2][:60])
print(f'checked {len(texts)} strings, {len(hits)} hits')
