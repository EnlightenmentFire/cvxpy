# -*- coding: utf-8 -*-
"""对 ASR 不过关的句子换 seed 重配，每轮重配→后期→回读，保留回读最好的一版（原始段落文件一起保留）。
python asr_fix.py ROUNDS id1 id2 ...
"""
import json, os, shutil, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "/tmp/claude-0/work/tts/raw"
rounds = int(sys.argv[1]); ids = sys.argv[2:]
rep = lambda: json.load(open(f"{HERE}/asr_report.json"))
best = {i: rep()[i]["sim"] for i in ids}
for k in range(rounds):
    todo = [i for i in ids if best[i] < 0.95]
    if not todo:
        break
    bak = f"/tmp/claude-0/work/tts/bak"; os.makedirs(bak, exist_ok=True)
    for i in todo:
        for f in glob.glob(f"{RAW}/{i}_*"):
            shutil.copy(f, bak)
    env = dict(os.environ, RETRY="1", F0_LO="82", NTRY="1", SEED0=str(3000 + 97 * k))
    subprocess.run(["python3", f"{HERE}/tts_gen.py"] + todo, env=env, check=True, capture_output=True)
    subprocess.run(["python3", f"{HERE}/voice_post.py"] + todo, check=True, capture_output=True)
    subprocess.run(["python3", f"{HERE}/asr_check.py"] + todo, check=True, capture_output=True, env=dict(os.environ, ASR_THREADS="4"))
    r = rep()
    for i in todo:
        print(f"round {k} {i}: {best[i]:.3f} -> {r[i]['sim']:.3f} {r[i]['hyp']}", flush=True)
        if r[i]["sim"] > best[i]:
            best[i] = r[i]["sim"]
        else:  # 还原
            for f in glob.glob(f"{bak}/{i}_*"):
                shutil.copy(f, RAW)
            subprocess.run(["python3", f"{HERE}/voice_post.py", i], check=True, capture_output=True)
            rr = rep(); rr[i]["sim"] = best[i]; json.dump(rr, open(f"{HERE}/asr_report.json", "w"), ensure_ascii=False, indent=1)
    shutil.rmtree(bak)
print("final", best)
