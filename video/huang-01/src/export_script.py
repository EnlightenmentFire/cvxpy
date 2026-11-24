# -*- coding: utf-8 -*-
"""把 script.py + timeline.json 导出成可读的旁白稿（也可用来自己录音）。"""
import json, os
from script import LINES, tts_text
here = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(here, '../build/timeline.json')))
NAMES = dict(cold='冷开场', title='标题', diner='第一章 方向', octo='第二章 章鱼', rule='第三章 规则', dilemma='第四章 两难',
             sega='第五章 第一次认错：对客户', inner='第六章 第二次认错：对自己人', time='第七章 第三次认错：对“完美”', result='第八章 结果', end='收尾')
out = ['# 黄仁勋 01——先认错，再活下来 · 旁白稿', '',
       f'配音：Kokoro-82M v1.1-zh（Apache-2.0），音色 {tl["voice"]}，语速 {tl["speed"]}。全片 {int(tl["duration"]//60)} 分 {int(tl["duration"]%60)} 秒。',
       '', '读法标注：NV1 读“N-V-一”，NV2 读“N-V-二”，DirectX 读“Direct-X”，RIVA 128 读“Riva 一二八”，Windows 95 读“Windows 九五”，3D 读“三D”，CPU 读“C-P-U”。',
       '「」里是英文原话的中文译文；缩进的小字是屏幕下方配的英文原文和出处。', '']
cur = None
for l, (sc, zh, o) in zip(tl['lines'], LINES):
    if sc != cur:
        cur = sc; s = next(x for x in tl['scenes'] if x['name'] == sc)
        out += ['', f'## {NAMES[sc]}（{int(s["start"]//60)}:{int(s["start"]%60):02}–{int(s["end"]//60)}:{int(s["end"]%60):02}）', '']
    text = zh.replace('|', '').replace('¦', '')
    if o.get('q'): text = '「' + text + '」'
    gap = o.get('gap', 0.32)
    out.append(f'{text}' + (f'　〔停 {gap:g} 秒〕' if gap >= 0.8 else ''))
    if o.get('en'): out.append(f'  > *"{o["en"]}"* —— {o.get("src", "")}')
    out.append('')
open(os.path.join(here, '../旁白稿.md'), 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
