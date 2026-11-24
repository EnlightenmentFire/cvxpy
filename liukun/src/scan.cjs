const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => { const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('[err]', e.message)); await p.goto('file://' + path.join(__dirname, 'index.html')); await p.evaluate(() => window.ready);
  const t0 = parseFloat(process.argv[2]), t1 = parseFloat(process.argv[3]), step = parseFloat(process.argv[4]), tag = process.argv[5] || 'a'; let i = 0;
  for (let t = t0; t < t1; t += step) { const d = await p.evaluate(t => { try { renderAt(t); } catch (e) { return 'ERR ' + e.message; } const c = document.createElement('canvas'); c.width = 270; c.height = 480; c.getContext('2d').drawImage(document.getElementById('c'), 0, 0, 270, 480); return c.toDataURL('image/jpeg', .85).split(',')[1]; }, t);
    if (d.startsWith('ERR')) { console.log(t, d); continue; } fs.writeFileSync(path.join(__dirname, '..', 'out', 'scan', `${tag}${String(i++).padStart(4, '0')}_${t.toFixed(1)}.jpg`), Buffer.from(d, 'base64')); }
  await b.close(); })();
