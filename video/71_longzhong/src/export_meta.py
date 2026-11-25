# -*- coding: utf-8 -*-
"""导出：字幕 narration.srt、逐句时间轴 timeline.json、逐句旁白稿 sentences.txt/json。usage: python export_meta.py OUTDIR"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import TL
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
T = TL()
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.', ',')
with open(f'{out}/narration.srt', 'w', encoding='utf-8') as f:
    for i, (c0, c1, s, _) in enumerate(T.subs, 1):
        f.write(f'{i}\n{ts(c0)} --> {ts(c1)}\n{s}\n\n')
rows = [dict(id=d['id'], scene=d['sc'], start=round(T.s[d['id']], 3), end=round(T.e[d['id']], 3), say=d['say'], sub=d['sub']) for d in T.L]
json.dump(dict(total=round(T.total, 3), fps=25, lines=rows), open(f'{out}/timeline.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump([dict(id=d['id'], text=d['say']) for d in T.L], open(f'{out}/sentences.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(f'{out}/sentences.txt', 'w', encoding='utf-8').write('\n'.join(d['say'] for d in T.L) + '\n')
print('exported', len(T.subs), 'subtitle cues,', len(rows), 'lines')
