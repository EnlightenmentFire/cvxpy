"""逐句旁白稿：sentences.json / sentences.txt（供盒子上重新配音）。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
out = sys.argv[1]
L = all_lines()
json.dump([dict(id=d["id"], scene=d["scene"], tts=tts_text(d["say"]), text=d["say"], subtitle=d["sub"]) for d in L],
          open(f"{out}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{out}/sentences.txt", "w").write("\n".join(tts_text(d["say"]) for d in L) + "\n")
print(len(L))
