# 没有配音时按字数估算时间轴；有配音后由 build_audio.py 覆盖 timings.js
import re, json, sys
sys.path.insert(0,'src')
from script import S
CPS=4.5; GAP=0.32; CH_GAP=2.8
EXTRA={'c0_2':1.4,'c7_3':0}
t=0.6; out={}; prev=None
for i,c,k,txt,tts in S:
    if prev is not None and c!=prev: t+=CH_GAP
    n=len(re.findall(r'[一-鿿〇]',txt)); d=n/CPS+0.25
    out[i]=[round(t,3),round(t+d,3)]; t+=d+GAP+EXTRA.get(i,0); prev=c
out['_end']=[round(t+3.0,3),round(t+3.0,3)]
open('src/timings.js','w').write('window.TIM='+json.dumps(out)+';')
print('total',t+3)
