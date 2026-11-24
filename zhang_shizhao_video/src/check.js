// 检查时间轴：有没有空场（没有任何场景可见）的时间段；列出场景时长
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto('http://127.0.0.1:8765/src/index.html');await p.waitForFunction('typeof E!=="undefined"&&E.ready');
const r=await p.evaluate(()=>{const gaps=[];let g=null;const errs=[];
 for(let t=0;t<E.duration;t+=0.05){try{renderAt(t)}catch(e){errs.push(t.toFixed(2)+' '+e.message);}
  const on=E.scenes.filter(s=>s.on&&parseFloat(s.el.style.opacity)>0.5).length;
  if(!on){if(!g)g=[t,t];g[1]=t;}else if(g){gaps.push(g.map(x=>+x.toFixed(2)));g=null;}}
 return {dur:E.duration,gaps,errs:errs.slice(0,5),scenes:E.scenes.map(s=>s.id+':'+s.a.toFixed(1)+'-'+s.b.toFixed(1)).join('  ')};});
console.log(JSON.stringify(r,null,1));await b.close();})();
