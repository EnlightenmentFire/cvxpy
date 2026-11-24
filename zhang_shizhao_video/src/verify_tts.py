# 用语音识别回听每句配音，按无声调拼音比对，找出读错/漏读的句子
import sys, os, re, difflib, json
sys.path.insert(0,'/home/user/cvxpy/zhang_shizhao_video/src')
import whisper
from pypinyin import lazy_pinyin
from script import S
SEG=sys.argv[1]; only=set(sys.argv[2].split(',')) if len(sys.argv)>2 else None
m=whisper.load_model('medium',device='cpu')
han=lambda x:''.join(re.findall(r'[一-鿿〇]',x))
bad=[]
for i,c,k,t,tts in S:
    if only and i not in only: continue
    f=f'{SEG}/{i}.wav'
    if not os.path.exists(f): print('MISSING',i); continue
    r=m.transcribe(f,language='zh',initial_prompt='以下是普通话的句子。',fp16=False,condition_on_previous_text=False)
    hyp=han(r['text']); ref=han(tts or t)
    a=lazy_pinyin(ref); b=lazy_pinyin(hyp)
    ratio=difflib.SequenceMatcher(None,a,b).ratio()
    flag='' if ratio>=0.93 else '  <<<<'
    print(f'{i} {ratio:.2f}{flag}\n   REF {ref}\n   HYP {hyp}',flush=True)
    if ratio<0.93: bad.append(i)
print('BAD',','.join(bad))
