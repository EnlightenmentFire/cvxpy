# 生成《稿子与史料核对.md》的旁白部分
import sys, json, re
sys.path.insert(0,'src')
from script import L, display
d=json.load(open('audio/narration.json',encoding='utf-8')); T={l['id']:l for l in d['lines']}
sec={'0':'0 冷启动','1':'1 诉苦会（卡在哪）','2':'2 连夜写信·五样权力（要什么）','3':'3 一句承诺','4':'4 半小时（怎么接住的）','5':'5 一级一级','6':'6 七个星期','7':'7 收尾三句'}
out=[]; cur=None
for l in L:
    k=l['id'].split('.')[0]
    if k!=cur:
        cur=k; out.append(f"\n### {sec[k]}\n")
    t=T[l['id']]['start']; out.append(f"- `{int(t//60)}:{t%60:04.1f}` {display(l['text'])}" + (f"  \n  <sub>出处：{l['src']}</sub>" if l['src'] else ""))
n=sum(len(re.sub(r"[，。；：？！、\s「」《》]","",display(l['text']))) for l in L)
head=f"旁白共 {len(L)} 句，约 {n} 字；按样音A的语速全片 {int(d['total']//60)} 分 {int(d['total']%60)} 秒（含片名卡和批示处的静场）。\n"
open('/tmp/script_part.md','w',encoding='utf-8').write(head+"\n".join(out)+"\n")
print(head)
