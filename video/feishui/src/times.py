import json, sys
tl = json.load(open('src/timeline.json')); L = {l['id']: l for l in tl['lines']}
ids = sys.argv[1:]
out = []
for i in ids:
    k, _, f = i.partition('@'); l = L[k]; fr = float(f) if f else 0.6
    out.append(f"{l['start'] + (l['end'] - l['start']) * fr:.2f}")
print(' '.join(out))
