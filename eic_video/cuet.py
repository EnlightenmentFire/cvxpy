import json,sys
tl=json.load(open('/tmp/claude-0/work/timeline.json'))
pre=sys.argv[1]; off=float(sys.argv[2]) if len(sys.argv)>2 else 2.5
print(" ".join(str(round(l['start']+off,1)) for l in tl['lines'] if l['id'].startswith(pre)))
