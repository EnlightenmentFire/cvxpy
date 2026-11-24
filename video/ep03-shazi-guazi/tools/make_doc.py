"""out/旁白稿与史料核对.md = 旁白稿（从 script.py 生成）+ 手写的核对表。"""
import re, sys, json
sys.path.insert(0, '.')
import script
def disp(t): return re.sub(r'\{([^|}]*)\|[^}]*\}', r'\1', t).replace('/', '')
TL = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'build/timeline.json'))
out = ['# 雇八个人算不算资本家——傻子瓜子', '', '改革开放系列 第 3 期（企业家线）· 旁白稿与史料核对', '',
       f'成片时长约 {int(TL["total"]//60)} 分 {int(TL["total"]%60)} 秒。旁白范围：1963 年至 1984 年 10 月；片尾一句 1988 年 4 月宪法修正案条文。', '', '## 一、旁白稿', '']
for sid, title, L in script.SECTIONS:
    s = TL['secs'][sid]
    out.append(f'### {title}（{int(s["s"]//60)}:{int(s["s"]%60):02d}）'); out.append('')
    for lid, text, *_ in L: out.append(disp(text)); out.append('')
out.append(open('tools/verify_notes.md', encoding='utf-8').read())
open('out/旁白稿与史料核对.md', 'w', encoding='utf-8').write('\n'.join(out))
print('doc ok')
