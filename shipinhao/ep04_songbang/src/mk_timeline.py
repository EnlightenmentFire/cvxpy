import json,sys
d=json.load(open('audio/narration.json',encoding='utf-8'))
open('src/timeline.js','w',encoding='utf-8').write('window.TL_DATA='+json.dumps(d,ensure_ascii=False)+';\n')
print('total',d['total'])
