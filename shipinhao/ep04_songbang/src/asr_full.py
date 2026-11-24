# 自检：把成品音轨（含配乐）做语音识别，和稿子逐句对，列出不一致处
import sys, re, json, difflib, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
import zhconv
f=sys.argv[1]
w,sr=sf.read(f); w=w.mean(1) if w.ndim>1 else w; w=resample_poly(w,16000,sr).astype(np.float32)
m=WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
segs,_=m.transcribe(w, language="zh", beam_size=5, vad_filter=True, initial_prompt="以下是普通话的句子。国营厂的厂长、经理。项南，黄文麟，滕能香，傅大文。")
hyp=zhconv.convert("".join(s.text for s in segs),'zh-cn')
d=json.load(open('audio/narration.json',encoding='utf-8'))
ref="".join(c["text"] for l in d["lines"] for c in l["clauses"])
num={'1984':'一九八四','55':'五十五','50':'五十','22':'二十二','23':'二十三','24':'二十四','30':'三十','49':'四十九','10':'十','3':'三','4':'四','5':'五','8':'八'}
def norm(s):
    s=re.sub(r"[^一-鿿0-9]","",s)
    for k in sorted(num,key=len,reverse=True): s=s.replace(k,num[k])
    return s
a,b=norm(ref),norm(hyp)
sm=difflib.SequenceMatcher(None,a,b,autojunk=False); err=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal':
        err+=max(i2-i1,j2-j1); print(tag, a[max(0,i1-6):i1]+'['+a[i1:i2]+']'+a[i2:i2+6], '→', '['+b[j1:j2]+']')
print('CER %.3f  ref %d chars'%(err/len(a),len(a)))
