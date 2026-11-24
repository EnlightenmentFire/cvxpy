// 用法: node src/still.js out_dir name=time[,name=time...]   time 可为 "cue+偏移" 如 c0_2+2.5
const { chromium } = require('playwright'); const path=require('path'); const fs=require('fs');
(async()=>{
  const out=process.argv[2]; fs.mkdirSync(out,{recursive:true});
  const jobs=process.argv[3].split(',').map(s=>s.split('='));
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  p.on('console',m=>{if(m.type()==='error')console.log('ERR',m.text())}); p.on('pageerror',e=>console.log('PAGEERR',e.message));
  p.on('requestfailed',r=>console.log('REQFAIL',r.url()));await p.goto('http://127.0.0.1:8765/src/index.html'); await p.waitForFunction('typeof E!=="undefined"&&E.ready');
  for(const [name,spec] of jobs){
    const t=await p.evaluate(spec=>{const m=spec.match(/^([a-z]\w*?)([+-][\d.]+)?$/i); if(m&&window.TIM[m[1]]) return window.TIM[m[1]][0]+parseFloat(m[2]||0); return parseFloat(spec);},spec);
    await p.evaluate(t=>renderAt(t),t); await p.screenshot({path:path.join(out,name+'.png')}); console.log(name,t.toFixed(2));
  }
  await b.close();
})();
