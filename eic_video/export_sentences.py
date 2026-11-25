"""Export the narration sentence list (for regenerating the voice elsewhere) -> sentences.json / sentences.txt"""
import json, sys
from script_data import all_lines
out = sys.argv[1]
L = [dict(id=d["id"], text=d["say"], subtitle=d["t"], kind=d["k"]) for d in all_lines()]
json.dump(L, open(f"{out}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{out}/sentences.txt", "w").write("\n".join(d["text"] for d in L) + "\n")
print(len(L))
