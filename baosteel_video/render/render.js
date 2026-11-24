// node render.js stills <t1,t2,...> <outdir> [safe]   |   node render.js frames <f0> <f1> <out.mp4> [crf]
const {chromium}=require('playwright');const {spawn}=require('child_process');const path=require('path');const fs=require('fs');
(async()=>{const mode=process.argv[2];const b=await chromium.launch({args:['--disable-web-security','--font-render-hinting=none']});
 const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
 p.on('console',m=>{if(m.type()==='error'||m.type()==='warning')console.log('[page]',m.text())});p.on('pageerror',e=>console.log('[pageerror]',e.message));
 await p.goto('file://'+path.join(__dirname,'film.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
 if(mode==='stills'){const ts=process.argv[3].split(',').map(Number);const out=process.argv[4];fs.mkdirSync(out,{recursive:true});
  if(process.argv[5]==='safe')await p.evaluate(()=>document.getElementById('safe').style.display='block');
  for(const t of ts){await p.evaluate(t=>Film.render(t),t);await p.screenshot({path:path.join(out,`t${t.toFixed(1).padStart(6,'0')}.png`)});}
 }else{const f0=+process.argv[3],f1=+process.argv[4],out=process.argv[5],crf=process.argv[6]||'17';
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf',crf,'-pix_fmt','yuv420p','-r','30',out],{stdio:['pipe','inherit','inherit']});
  const t0=Date.now();
  for(let f=f0;f<f1;f++){await p.evaluate(t=>Film.render(t),f/30);const buf=await p.screenshot({type:'jpeg',quality:96});
   if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
   if((f-f0)%300===0)console.log(`frame ${f}/${f1} ${((Date.now()-t0)/1000).toFixed(0)}s`);}
  ff.stdin.end();await new Promise(r=>ff.on('close',r));}
 await b.close()})();
