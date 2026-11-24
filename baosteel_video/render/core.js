// ---- core: time helpers, scene registry, HUD ----
const W=1080,H=1920;
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)), lerp=(a,b,t)=>a+(b-a)*t;
const P=(t,a,b)=>clamp((t-a)/(b-a));
const E={io:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,o:x=>1-Math.pow(1-x,3),o5:x=>1-Math.pow(1-x,5),i:x=>x*x*x,lin:x=>x,
  back:x=>{const c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
const TLi={}; TL.lines.forEach(l=>TLi[l.id]=l);
const SEC={}; TL.sections.forEach(s=>SEC[s.id]=s);
const T=id=>TLi[id].start, TE=id=>TLi[id].end;
// time at which a keyword inside a line is spoken (estimated inside its subtitle chunk)
function K(id,word){const l=TLi[id];for(const s of l.subs){const i=s.text.indexOf(word);if(i>=0)return s.start+(s.end-s.start)*i/Math.max(1,s.text.length)}
  const i=l.sub.indexOf(word);if(i<0){console.warn('K miss',id,word);return l.start}return l.start+(l.end-l.start)*i/l.sub.length}
function rng(seed){let a=seed>>>0;return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function el(tag,cls,style,html){const e=document.createElement(tag);if(cls)e.className=cls;if(style)e.style.cssText=style;if(html!=null)e.innerHTML=html;return e}
const NS='http://www.w3.org/2000/svg';
function svg(w,h,style,inner){const s=document.createElementNS(NS,'svg');s.setAttribute('width',w);s.setAttribute('height',h);s.setAttribute('viewBox',`0 0 ${w} ${h}`);if(style)s.style.cssText=style;if(inner)s.innerHTML=inner;return s}
const fmt=n=>Math.round(n).toLocaleString('en-US');
const Film={scenes:[],
  scene(id,t0,t1,o={}){const root=el('div','scene '+(o.cls||''));const s={id,t0,t1,root,anims:[],xin:o.xin??.5,xout:o.xout??.5,theme:o.theme||'dark',hud:o.hud??true,push:o.push??.035,
      add(e,style,cls,html){const x=(typeof e==='string')?el(e,cls,style,html):e;root.appendChild(x);return x},
      on(fn){s.anims.push(fn);return s},
      // fade/slide element in at tin, out at tout (absolute seconds)
      io(e,tin,tout,q={}){const din=q.din??.55,dout=q.dout??.4,y=q.y??26,x=q.x??0,sc=q.s??0,drift=q.drift??0;
        s.anims.push(t=>{const a=E.o(P(t,tin,tin+din)),b=tout==null?0:E.i(P(t,tout,tout+dout));const o=a*(1-b)*(q.max??1);e.style.opacity=o;
          if(o<=0){e.style.visibility='hidden';return}e.style.visibility='visible';
          const k=1-a;e.style.transform=`translate(${x*k}px,${y*k+(-drift*(t-tin))}px) scale(${1+sc*k})`+(q.rot?` rotate(${q.rot}deg)`:'')});return e},
      // stroke draw-on for svg paths with pathLength=1
      draw(e,tin,dur){e.setAttribute('pathLength','1');e.style.strokeDasharray='1';s.anims.push(t=>{e.style.strokeDashoffset=1-E.io(P(t,tin,tin+dur))});return e},
      type(e,text,tin,cps=14){s.anims.push(t=>{const n=Math.floor(clamp((t-tin)*cps,0,text.length));if(e._n!==n){e._n=n;e.textContent=text.slice(0,n)}});return e}};
    document.getElementById('scenes').appendChild(root);Film.scenes.push(s);return s},
  init(){Film.hud={hdr:document.getElementById('hdr'),hr:document.getElementById('hr'),src:document.getElementById('src'),sub:document.getElementById('sub')};Film.render(0)},
  render(t){
    let theme='dark',hud=true,top=null;
    for(const s of Film.scenes){const vis=t>=s.t0-.02&&t<s.t1+s.xout;
      if(!vis){if(s._v){s.root.style.display='none';s._v=false}continue}
      if(!s._v){s.root.style.display='block';s._v=true}
      const a=(s.xin>0?E.io(P(t,s.t0,s.t0+s.xin)):1)*(1-(s.xout>0?E.io(P(t,s.t1,s.t1+s.xout)):0));
      s.root.style.opacity=a;
      const pp=P(t,s.t0,s.t1);s.root.style.transform=`scale(${1+s.push*pp})`;
      for(const f of s.anims)f(t);
      if(t>=s.t0&&t<s.t1){theme=s.theme;hud=s.hud;top=s}}
    // HUD
    const h=Film.hud;const pp=theme==='paper';
    h.hdr.className=pp?'pp':'';h.src.className=pp?'pp':'';
    const sec=TL.sections.find(x=>t>=x.start&&t<x.end);
    h.hdr.style.opacity=hud?1:0;h.hr.textContent=sec&&sec.name.includes('　')?sec.name:(sec&&sec.id==='cold'?'1978 · 鞍山':'');
    let line=null,chunk=null;for(const l of TL.lines){if(t>=l.start-.05&&t<l.end+.25){line=l;for(const c of l.subs)if(t>=c.start-.05)chunk=c}}
    const showSub=hud&&chunk&&(!top||top.sub!==false);
    if(showSub){if(h.sub._t!==chunk.text){h.sub._t=chunk.text;h.sub.innerHTML='<span>'+chunk.text+'</span>'}h.sub.style.opacity=1}else h.sub.style.opacity=0;
    const srcl=TL.lines.find(l=>t>=l.start-.2&&t<l.end+.5&&l.src);
    if(hud&&srcl){if(h.src._t!==srcl.src){h.src._t=srcl.src;h.src.textContent='出处｜'+srcl.src}h.src.style.opacity=E.o(P(t,srcl.start-.2,srcl.start+.3))*(1-P(t,srcl.end+.2,srcl.end+.5))}else h.src.style.opacity=0;
  }};
