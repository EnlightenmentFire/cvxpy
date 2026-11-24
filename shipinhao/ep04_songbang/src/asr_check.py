import sys, re, json
from faster_whisper import WhisperModel
m=WhisperModel("small", device="cpu", compute_type="int8")
def norm(s): return re.sub(r"[^一-鿿0-9]","",s)
def cer(a,b):
    import numpy as np
    d=np.zeros((len(a)+1,len(b)+1),int); d[:,0]=range(len(a)+1); d[0,:]=range(len(b)+1)
    for i in range(1,len(a)+1):
        for j in range(1,len(b)+1):
            d[i,j]=min(d[i-1,j]+1,d[i,j-1]+1,d[i-1,j-1]+(a[i-1]!=b[j-1]))
    return d[-1,-1]/max(1,len(a))
for f in sys.argv[1:]:
    ref="".join(c["text"] for l in json.load(open(f.replace('.wav','.json'),encoding='utf-8'))["lines"] for c in l["clauses"])
    import soundfile as sf, numpy as np
    from scipy.signal import resample_poly
    w,sr=sf.read(f); w=resample_poly(w,16000,sr).astype(np.float32)
    segs,_=m.transcribe(w, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。国营厂的厂长。")
    hyp="".join(s.text for s in segs)
    try:
        import zhconv; hyp=zhconv.convert(hyp,'zh-cn')
    except Exception: pass
    print(f.split('/')[-1], "CER %.3f"%cer(norm(ref),norm(hyp))); print("   ", hyp, flush=True)
