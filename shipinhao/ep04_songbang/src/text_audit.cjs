// 自检：导出全片所有上屏文字 + 字幕，扫敏感/禁用词和清单外人名
const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + path.resolve(__dirname, 'film.html')); await pg.evaluate(() => window.ready);
  const r = await pg.evaluate(() => ({ scenes: SCENES.map(s => [s.name, s.t0.toFixed(1), s.root.innerText.replace(/\s+/g, ' ')]), subs: SUBS.map(s => s.text), strip: document.getElementById('strip').innerText.replace(/\s+/g, ' '), long: SUBS.filter(s => s.text.length > 19).map(s => s.text), gaps: SUBS.map((s, i) => i ? +(s.start - SUBS[i - 1].end).toFixed(2) : 0).filter(g => g < 0) }));
  const all = r.scenes.map(s => s[2]).join('\n') + '\n' + r.subs.join('\n') + r.strip;
  fs.writeFileSync('/tmp/alltext.txt', r.scenes.map(s => `## ${s[0]} @${s[1]}\n${s[2]}`).join('\n\n') + '\n\n## 字幕\n' + r.subs.join('\n'));
  const ban = ['而如今', '如今', '反观', '今天', '后来又', '后来', '现在', '当下', '至今', '英明', '远见', '魄力', '伟大', '高瞻', '果断', '敢为', '先驱', '石破', '呐喊', '一锤定音', '改变了全国', '1986', '1985', '1987', '民营', '下岗', '国企改革', '总书记', '主席', '总理', '徐明新', '胡平', '童大林', '游廷', '龚雄', '汪建华', '董福森', '杜进兴', '吴晓波', '习', '邓', '赵', '胡', '江', '万里', '晋江', '企业家'];
  for (const w of ban) { const i = all.indexOf(w); if (i >= 0) console.log('HIT', w, '→', all.slice(Math.max(0, i - 12), i + 14).replace(/\n/g, ' ')); }
  const names = (all.match(/项南|黄文麟|滕能香|傅大文/g) || []).reduce((m, x) => (m[x] = (m[x] || 0) + 1, m), {});
  console.log('人名出现次数', JSON.stringify(names)); console.log('超长字幕', r.long); console.log('字幕重叠', r.gaps.length, ' 字幕条数', r.subs.length);
  await b.close();
})();
