import sys, torch, time
torch.set_num_threads(4)
from transformers import AutoProcessor, DiaForConditionalGeneration
M = "nari-labs/Dia-1.6B-0626"
proc = AutoProcessor.from_pretrained(M)
model = DiaForConditionalGeneration.from_pretrained(M, torch_dtype=torch.float32)
if sys.argv[1] == "download": sys.exit(0)
text = sys.argv[2]; out = sys.argv[1]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
torch.manual_seed(seed)
inp = proc(text=[text], padding=True, return_tensors="pt")
t = time.time()
o = model.generate(**inp, max_new_tokens=int(sys.argv[4]) if len(sys.argv)>4 else 1500, guidance_scale=3.0, temperature=1.8, top_p=0.90, top_k=45)
dec = proc.batch_decode(o); proc.save_audio(dec, out); print("gen secs", time.time()-t)
