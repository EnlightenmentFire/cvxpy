# -*- coding: utf-8 -*-
"""由 script.py 生成旁白稿（含出处层级）。"""
from script import BEATS, SECTIONS
from timeline import TL
T = TL()
def mmss(t): return '%d:%04.1f' % (int(t // 60), t % 60)
L = ['# 关羽失荆州：麋芳为什么开城 —— 旁白稿与出处', '',
     '> 建安二十四年（219）。全片约 %s，1080×1920 / 30fps。' % mmss(T.total),
     '> 引文层级：**正史**＝《三国志》正文；**裴注**＝裴松之注所引；**通鉴**＝《资治通鉴》；**今人**＝后人论说；**解读**＝本片推论。演义情节不用。', '']
names = {0: '冷开场', 7: '收尾'}
cur = None
for b in BEATS:
    if b['sec'] != cur:
        cur = b['sec']
        ttl = names.get(cur) or ('%s　%s（%s）' % SECTIONS[cur])
        L += ['', '## ' + ttl, '']
    tag = '〔解读〕' if b.get('tag') else ''
    L.append('**[%s]** %s%s' % (mmss(T.s[b['id']]), tag, b['text']))
    c = b.get('cite')
    if c:
        L.append('')
        L.append('> 〔%s〕%s：%s' % (c['level'], c['src'], c['q'].replace('／', ' ／ ')))
        if c.get('note'): L.append('> 　　注：' + c['note'])
    L.append('')
open('/home/user/work/vid/旁白稿.md', 'w').write('\n'.join(L))
print('ok', len(L))
