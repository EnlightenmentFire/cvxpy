// 逐帧渲染：node src/render.js <start_frame> <end_frame> <out.mp4> [fps=30]
const { chromium } = require('playwright'); const { spawn } = require('child_process');
(async()=>{
  const [a,b,out]=[parseInt(process.argv[2]),parseInt(process.argv[3]),process.argv[4]]; const fps=parseInt(process.argv[5]||'30');
  const br=await chromium.launch({args:['--disable-gpu','--font-render-hinting=none']});
  const p=await br.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  p.on('pageerror',e=>{console.error('PAGEERR',e.message);});
  await p.goto('http://127.0.0.1:8765/src/index.html'); await p.waitForFunction('typeof E!=="undefined"&&E.ready');
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','12','-pix_fmt','yuv420p','-r',String(fps),out],{stdio:['pipe','inherit','inherit']});
  const t0=Date.now();
  for(let f=a;f<b;f++){
    await p.evaluate(t=>renderAt(t),f/fps);
    const buf=await p.screenshot({type:'jpeg',quality:95});
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
    if((f-a)%300===0) console.log(`${out} ${f-a}/${b-a} ${((Date.now()-t0)/1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await br.close(); console.log('done',out);
})();
