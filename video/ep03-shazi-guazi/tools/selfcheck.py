"""导出前自检：人名白名单、越界词、范围。扫描旁白稿和所有画面文字。"""
import re, sys, glob
sys.path.insert(0, '.'); import script
texts = {'script.py': ' '.join(t for _, _, L in script.SECTIONS for _, t, *_ in L)}
for f in glob.glob('web/s*.js') + ['web/parts.js']: texts[f] = ' '.join(re.findall(r'[一-鿿0-9《》“”·，。？：；、（）〔〕 ]{2,}', open(f, encoding='utf-8').read()))
BAD = ['而如今', '反观', '今天的我们', '后来又', '如今', '今天', '现在的', '当下', '英明', '远见', '勇敢', '伟大', '高瞻远瞩', '1992', '1989', '1986', '1987', '1990', '2000年', '南方谈话', '南巡', '有奖销售', '官司', '民营经济', '总设计师',
       '胡耀邦', '赵紫阳', '万里', '杜润生', '习', '金涛', '徐明熙', '肖岩', '吴晓波', '周晓光', '汪道涵', '张劲夫', '黄璜', '芜湖市委书记', '省委书记', '保了', '救了', '拍板']
ok = True
for f, t in texts.items():
    for b in BAD:
        for m in re.finditer(re.escape(b), t):
            ctx = t[max(0, m.start()-12):m.end()+12]
            if b == '习' and not re.search(r'习近平|习仲勋', ctx): continue
            if b == '今天' or b == '现在的': pass
            print('!!', f, b, '→', ctx); ok = False
# years mentioned in narration
yrs = sorted(set(int(y) for y in re.findall(r'(?<!\d)(19\d\d|20\d\d)(?!\d)', texts['script.py'])))
print('旁白中的年份:', yrs)
names = ['年广久', '陈志雄', '林子力', '马克思', '陈云', '邓小平']
print('人名出现次数:', {n: sum(t.count(n) for t in texts.values()) for n in names})
print('自检', '通过' if ok else '有命中，逐条看')
