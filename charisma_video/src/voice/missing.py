import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import script
meta = json.load(open(os.path.join(os.path.dirname(__file__), "lines", "meta.json")))
args = []
for seg in script.SEGMENTS:
    idx = [str(i) for i, l in enumerate(seg["lines"]) if l.get("k") != "en" and f"{seg['id']}_{i:02d}" not in meta]
    if idx:
        args.append(seg["id"] + ":" + ",".join(idx))
print(" ".join(args))
