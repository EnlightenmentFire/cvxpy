// ===== 二 东京和君津 / 三 打桩 / 四 吵起来 =====
(function(){
const G=(sv,tf)=>{const g=document.createElementNS(NS,'g');if(tf)g.setAttribute('transform',tf);sv.appendChild(g);return g};
const PATH=(par,d,cls,style)=>{const p=document.createElementNS(NS,'path');p.setAttribute('d',d);p.setAttribute('class',cls||'ln');if(style)p.style.cssText=style;par.appendChild(p);return p};
// ---------- 二 东京和君津 ----------
{const A=SEC.tokyo;const b1=T('b1'),b2=T('b2'),b3=T('b3'),b4=T('b4'),b5=T('b5'),b6=T('b6'),b8=T('b8');
 chapter('tokyo','二','东京','和君津',A.start,b1-.1);
 {const s=Film.scene('tk1',b1-.1,b5-.2,{cls:'dark'});
  // audience: ~400 heads
  const cv=canvas(s);const c=cv.getContext('2d');const R=rng(11);const heads=[];
  let y=1010,sz=30;for(let r=0;r<16;r++){const n=Math.round(1180/(sz*1.18));const off=(r%2)*sz*.6-40;for(let i=0;i<n;i++)heads.push([off+i*sz*1.18+R()*6,y+R()*6,sz*(.92+R()*.16),.25+r*.04+R()*.08,R()]);y+=sz*.82;sz*=1.085}
  const HN=heads.length;
  s.on(t=>{c.clearRect(0,0,W,H);const gl=c.createRadialGradient(540,880,40,540,880,700);gl.addColorStop(0,'rgba(255,214,150,.20)');gl.addColorStop(1,'rgba(255,214,150,0)');c.fillStyle=gl;c.fillRect(0,300,W,1300);
   const p=P(t,b1,b1+2.2);for(let i=0;i<HN;i++){const h=heads[i];const a=clamp(p*1.3-h[4]*.3)*clamp((h[1]-940)/60);if(a<=0)continue;const v=14+h[3]*26|0;c.fillStyle=`rgba(${v},${v+3},${v+7},${a})`;drawHead(c,h[0],h[1],h[2])}
   // camera flashes
   for(let k=0;k<6;k++){const ph=((t*0.9+k*.37)%1.7);if(ph<.09){const h=heads[(Math.floor(t*0.9/1.7+k*13.3)*37+k*91)%HN];c.fillStyle=`rgba(255,255,255,${.9*(1-ph/.09)})`;c.beginPath();c.arc(h[0],h[1]-h[2]*.5,3+h[2]*.08,0,6.3);c.fill();c.fillStyle=`rgba(255,255,255,${.25*(1-ph/.09)})`;c.beginPath();c.arc(h[0],h[1]-h[2]*.5,14+h[2]*.4,0,6.3);c.fill()}}});
  const hd=s.add('div','left:64px;top:318px;width:952px','abs');hd.innerHTML=`<div class="mono" style="font-size:44px;color:#ff9a4a;letter-spacing:.08em">1978.10.25</div><div class="serif" style="font-size:70px;line-height:1.2;margin-top:4px">东京 · 日本记者俱乐部</div>`;s.io(hd,b1,null,{y:16});
  const n4=s.add('div','left:64px;top:560px;width:952px;text-align:center','abs');n4.innerHTML=`<span style="font-size:44px;font-weight:700">到场约 </span><span class="num" id="n400" style="font-size:260px;line-height:1;color:#ff7a1a">0</span><span style="font-size:44px;font-weight:700"> 人</span><div style="font-size:28px;color:#aeb7bf;font-weight:500">记者、外国特派员、摄影摄像人员</div>`;
  s.io(n4,K('b1','到场')-.3,b2-.2,{y:20});const e4=n4.querySelector('#n400');s.on(t=>{e4.textContent=fmt(400*E.o(P(t,K('b1','到场'),K('b1','到场')+1.4)))});
  nameTag(s,'邓小平','时任国务院副总理',64,520,b2-.1,b4-.2);
  const q1=s.add('div','left:64px;top:610px;width:952px;font-size:74px','q');q1.innerHTML=`「首先承认<br>我们的<span style="color:#ff7a1a">落后</span>，<br>老老实实承认落后<br>就有希望。<span id="q1b">再就是<br>善于学习。」</span>`;s.io(q1,K('b2','首先')-.2,b3-.25,{y:20});
  const q1b=q1.querySelector('#q1b');s.on(t=>{q1b.style.opacity=E.o(P(t,K('b2','再就是')-.2,K('b2','再就是')+.4))});
  const q2=s.add('div','left:64px;top:640px;width:952px;font-size:78px','q');q2.innerHTML=`「长得很丑<br>却要打扮得<br>像美人一样，<br><span style="color:#ff7a1a">那是不行的。</span>」`;s.io(q2,K('b3','长得')-.2,b4-.25,{y:20});
  const q3=s.add('div','left:64px;top:560px;width:952px','abs');q3.innerHTML=`<div style="font-size:46px;font-weight:700;line-height:1.5">一个大国的领导人<br>当着几百名外国记者</div><div class="serif" style="font-size:104px;line-height:1.3;color:#ff7a1a;margin-top:10px">说自己落后</div><div style="font-size:40px;font-weight:700;margin-top:14px;color:#d9dee3">这在当时很少见</div>`;s.io(q3,b4,null,{y:20});}
 {const s=Film.scene('tk2',b5-.2,A.end,{cls:'bp'});s.add('div','','bpgrid');
  const sv=svg(1080,1920,'left:0;top:0');s.add(sv);
  // steelworks skyline by the sea
  [[230,.40],[540,.46],[850,.40]].forEach((a,i)=>{const g=G(sv,`translate(${a[0]},1215) scale(${a[1]})`);addFurnace(s,g,{tin:b5+.1+i*.3,stagger:.06,dur:1.0,sw:3.4})});
  const sea=G(sv);PATH(sea,'M0,1217 L1080,1217','ln');for(let i=0;i<3;i++){const p=PATH(sea,`M${-40+i*60},${1238+i*17} `+Array.from({length:12},(_,k)=>`q25,-8 50,0 t50,0`).join(' '),'ln','opacity:'+(.5-i*.08));s.on(t=>{p.setAttribute('transform',`translate(${Math.sin(t*.6+i)*14},0)`)})}
  const ship=G(sv,'translate(770,1262)');PATH(ship,'M-120,0 L120,0 L96,26 L-100,26 Z M-60,0 L-60,-22 L-10,-22 L-10,0 M-40,-22 L-40,-40 L-26,-40 L-26,-22 M20,0 L20,-12 L90,-12 L90,0','ln','stroke-width:2.6');s.on(t=>{ship.setAttribute('transform',`translate(${770-(t-b5)*9},${1262+Math.sin(t*1.3)*2})`)});
  const hd=s.add('div','left:64px;top:318px;width:952px','abs');hd.innerHTML=`<div class="mono" style="font-size:44px;color:#ff9a4a;letter-spacing:.08em">1978.10.26 上午</div><div class="serif" style="font-size:92px;line-height:1.2;margin-top:4px">君津制铁所</div>`;s.io(hd,b5,K('b6','你们')-.5,{y:16});
  nameTag(s,'稻山嘉宽','时任新日铁会长',64,560,K('b6','稻山')-.3,b8-.3);nameTag(s,'斋藤英四郎','时任新日铁社长',64,640,K('b6','斋藤')-.3,b8-.3);
  const q=s.add('div','left:64px;top:560px;width:952px;font-size:76px;text-shadow:0 0 30px #0e2136','q');q.innerHTML=`你们就照<br>这个工厂的<span style="color:#ff7a1a">样子</span>，<br>帮我们<span style="color:#ff7a1a">建设一个</span>。`;
  const plate=s.add('div','left:0;top:520px;width:1080px;height:420px;background:linear-gradient(rgba(14,33,54,0),rgba(14,33,54,.88) 15%,rgba(14,33,54,.88) 85%,rgba(14,33,54,0))','abs');s.io(plate,K('b6','你们')-.3,b8-.3,{y:0});s.root.appendChild(q);
  s.on(t=>{const p=E.io(P(t,K('b6','你们')-.4,K('b6','你们')+.2));for(const e of s.root.querySelectorAll('.tag')){e.style.marginTop=(-p*235)+'px'}});
  s.io(q,K('b6','你们')-.2,b8-.3,{y:20});
  
  // b8: two days
  const two=s.add('div','left:64px;top:330px;width:952px','abs');two.innerHTML=`<div style="display:flex;gap:28px;align-items:stretch"><div style="flex:1;border:2px solid #8fbfe3;padding:22px 24px;background:rgba(14,33,54,.85)"><div class="mono" style="font-size:36px;color:#9fc3e0">10.25 东京</div><div class="serif" style="font-size:58px;line-height:1.3;margin-top:8px">当众<br>承认落后</div></div><div style="flex:1;border:2px solid #ff7a1a;padding:22px 24px;background:rgba(14,33,54,.85)"><div class="mono" style="font-size:36px;color:#ff9a4a">10.26 君津</div><div class="serif" style="font-size:58px;line-height:1.3;margin-top:8px;color:#ffb070">要一个<br>一样的厂</div></div></div><div class="serif c" style="font-size:66px;margin-top:40px">只隔了一天</div>`;
  s.io(two,b8,null,{y:20});}}
// ---------- 三 打桩 ----------
{const A=SEC.pile;const d1=T('d1'),d2=T('d2'),d3=T('d3'),d4=T('d4'),d5=T('d5'),d6=T('d6'),d7=T('d7');
 chapter('pile','三','打桩','1978.12.23',A.start,d1-.1);
 {const s=Film.scene('pl1',d1-.1,d3-.2,{cls:'bp'});s.add('div','','bpgrid');
  const mp=MapView(s,0,700,1080,620);const pl=MAP.places;s.on(t=>{const p=E.io(P(t,d1,d2+3));mp.view(lerp(pl.baoshan[0]-1.5,pl.baoshan[0]+.15,p),lerp(pl.baoshan[1]-1.2,pl.baoshan[1]+.1,p),lerp(52,210,p))});
  mp.mark('baoshan','上海 · 宝山',K('d2','宝山')-.6,null,{side:'l',sub:'长江入海口南岸'});
  const yl=s.add('div','left:120px;top:880px;font-size:30px;color:#9fc3e0;letter-spacing:.3em','abs serif','长　江');s.io(yl,K('d2','长江')-.3,null,{y:0});
  // december timeline
  const tl=s.add('div','left:64px;top:320px;width:952px','abs');tl.innerHTML=`<div class="mono" style="font-size:40px;color:#ff9a4a;letter-spacing:.08em">1978.12</div>
   <div style="position:relative;height:330px;margin-top:20px"><div class="abs" style="left:0;right:0;top:54px;height:3px;background:#8fbfe3;opacity:.6"></div>
   <div class="abs it" style="left:0;top:0;width:330px"><div class="num" style="font-size:46px;color:#9fc3e0">18 — 22</div><div style="width:300px;height:14px;background:#8fbfe3;opacity:.55;margin-top:0"></div><div style="font-size:30px;font-weight:700;margin-top:12px;line-height:1.3">十一届三中全会</div></div>
   <div class="abs it" style="left:330px;top:0;width:300px"><div class="num" style="font-size:46px;color:#fff">22 <span style="font-size:28px;font-family:'Noto Sans CJK SC'">晚</span></div><div style="width:18px;height:18px;border-radius:50%;background:#fff;margin-top:-2px"></div><div style="font-size:30px;font-weight:700;margin-top:10px;line-height:1.3">总协议签字<br><span style="font-size:24px;color:#9fc3e0;font-weight:500">上海 · 中方与新日铁</span></div></div>
   <div class="abs it" style="left:650px;top:0;width:300px"><div class="num" style="font-size:46px;color:#ff7a1a">23</div><div style="width:22px;height:22px;border-radius:50%;background:#ff7a1a;margin-top:-4px;box-shadow:0 0 0 7px #ff7a1a44"></div><div class="serif" style="font-size:42px;margin-top:8px;line-height:1.25;color:#ffb070">打下第一根桩</div></div></div>`;
  const it=tl.querySelectorAll('.it');s.io(tl,d1-.05,null,{y:10});[K('d2','十一届')-.4,d1+.2,K('d2','打下')-.5].forEach((tt,i)=>s.io(it[i],tt,null,{y:16}));
  // pile driver
  const sv=svg(1080,1920,'left:0;top:0');s.add(sv);const g=G(sv,'translate(830,1240)');const tp=K('d2','打下')-.6;
  const rig=PATH(g,'M-70,0 L70,0 M-40,0 L-8,-330 M40,0 L8,-330 M-8,-330 L8,-330 M-34,-70 L34,-70 M-27,-150 L27,-150 M-19,-230 L19,-230 M-34,-70 L27,-150 M34,-70 L-27,-150 M-27,-150 L19,-230 M27,-150 L-19,-230','ln','stroke-width:2.6');s.draw(rig,tp,1.0);
  const grd=PATH(g,'M-230,0 L190,0 '+Array.from({length:14},(_,i)=>`M${-220+i*30},0 l-16,18`).join(' '),'ln','stroke-width:2;opacity:.8');s.draw(grd,tp-.3,.8);
  const pile=document.createElementNS(NS,'rect');pile.setAttribute('x',-9);pile.setAttribute('width',18);pile.setAttribute('height',190);pile.setAttribute('fill','#ff7a1a');g.appendChild(pile);
  const ham=document.createElementNS(NS,'rect');ham.setAttribute('x',-20);ham.setAttribute('width',40);ham.setAttribute('height',46);ham.setAttribute('fill','#dfe7ee');g.appendChild(ham);
  s.on(t=>{const u=t-K('d2','打下');const n=clamp(Math.floor(u/.55)+1,0,7);const ph=clamp((u/.55)%1);const hit=u<0?0:n-1+E.i(clamp(ph*2.2));const y=-190+clamp(hit,0,7)*24;pile.setAttribute('y',y);pile.style.opacity=P(t,tp+.4,tp+.9);
    const lift=u<0||n>=7?1:(ph<.45?1-E.i(ph/.45):E.o((ph-.45)/.55));ham.setAttribute('y',y-46-lift*120);ham.style.opacity=P(t,tp+.4,tp+.9)});}
 {const s=Film.scene('pl2',d3-.2,d5-.2,{cls:'dark'});
  const a=s.add('div','left:64px;top:320px;width:952px','abs');a.innerHTML=`<div style="font-size:38px;font-weight:700;color:#aeb7bf">宝钢 · 计划年产</div><div style="display:flex;gap:60px;margin-top:6px"><div><span style="font-size:44px;font-weight:900">铁 </span><span class="num" style="font-size:150px;line-height:1">650</span><span style="font-size:36px;font-weight:700"> 万吨</span></div><div><span style="font-size:44px;font-weight:900;color:#ff7a1a">钢 </span><span class="num" style="font-size:150px;line-height:1;color:#ff7a1a">671</span><span style="font-size:36px;font-weight:700;color:#ff7a1a"> 万吨</span></div></div>`;s.io(a,d3,null,{y:20});
  const tb=K('d3','相当于')-.3;const b=s.add('div','left:64px;top:600px;width:952px','abs');b.innerHTML=`<div style="font-size:30px;color:#aeb7bf;font-weight:500">1978 年全国钢产量 <span class="num" style="font-size:44px;color:#fff">3,178</span> 万吨</div><div style="position:relative;height:74px;margin-top:10px;background:#3a444e"><div id="pb" style="position:absolute;left:0;top:0;bottom:0;background:#ff7a1a"></div><div id="pbl" class="num" style="position:absolute;left:14px;top:6px;font-size:54px;color:#10161d">671</div></div><div style="font-size:40px;font-weight:700;margin-top:12px">一个厂 ≈ 全国的 <span class="num" style="font-size:84px;color:#ff7a1a;line-height:1">1/5</span></div>`;
  s.io(b,tb,d4-.25,{y:20});const pb=b.querySelector('#pb');s.on(t=>{pb.style.width=(671/3178*100*E.io(P(t,tb+.3,tb+1.5)))+'%'});
  const tm=d4;const m=s.add('div','left:64px;top:600px;width:952px','abs');m.innerHTML=`<div style="font-size:38px;font-weight:700;color:#aeb7bf">总投资 · 当时的估计</div><div><span class="num" style="font-size:150px;line-height:1.05;color:#ff7a1a">200—300</span><span style="font-size:44px;font-weight:900;color:#ff7a1a"> 亿元</span></div>
   <div style="font-size:30px;color:#aeb7bf;font-weight:500;margin-top:26px">国家一年的财政收入　<span style="color:#fff">1977 年 874 亿 · 1978 年 1,132 亿</span></div>
   <div style="position:relative;height:74px;margin-top:10px;background:#3a444e"><div id="mb" style="position:absolute;left:0;top:0;bottom:0;background:repeating-linear-gradient(-45deg,#ff7a1a 0 10px,#ff9a4a 10px 20px)"></div><div id="mb2" style="position:absolute;left:0;top:0;bottom:0;background:#ff7a1a"></div><div style="position:absolute;right:12px;top:16px;font-size:28px;color:#c9d1d8;font-weight:500">1,132 亿（1978）</div></div>
   <div style="font-size:40px;font-weight:700;margin-top:14px">≈ 国家一年收入的 <span class="num" style="font-size:84px;color:#ff7a1a;line-height:1">1/4</span> 上下<span style="font-size:26px;color:#8b959f;font-weight:500">　本片估算</span></div>`;
  s.io(m,tm,null,{y:20});const mb=m.querySelector('#mb'),mb2=m.querySelector('#mb2');const tq=K('d4','粗算');s.on(t=>{const p=E.io(P(t,tq-.2,tq+1.2));mb2.style.width=(200/1132*100*p)+'%';mb.style.width=(300/1132*100*p)+'%'});}
 {const s=Film.scene('pl3',d5-.2,A.end,{cls:'paper',theme:'paper'});
  nameTag(s,'稻山嘉宽','时任新日铁会长',64,330,d5,d6-.3);
  const w=s.add('div','left:64px;top:440px;width:952px','abs');w.innerHTML=`<div class="serif" style="font-size:120px;line-height:1.2">忧心忡忡</div><div style="font-size:38px;font-weight:700;margin-top:18px;line-height:1.5">怕工程半途出事</div><div style="font-size:30px;line-height:1.55;margin-top:30px;color:#4a4338;border-top:2px solid #1e1a15;padding-top:20px;font-weight:500">此前，新日铁在武汉援建的一米七轧机工程<br>建设受到严重干扰。<br>稻山问：会不会再次发生那样的事。<br><span style="font-size:24px;color:#6b6252">—— 陈锦华的回忆</span></div>`;s.io(w,K('d5','忧心')-.4,d6-.3,{y:20});
  // eggs vs hen
  const eg=s.add('div','left:64px;top:330px;width:952px','abs');const eggs=Array.from({length:7},(_,i)=>`<svg class="egg" width="110" height="110" viewBox="0 0 200 200" style="position:relative">${ICON.egg('#1e1a15')}</svg>`).join('');
  eg.innerHTML=`<div style="font-size:34px;font-weight:700;color:#4a4338">天天买鸡蛋</div><div style="display:flex;gap:6px;margin:6px 0 0 -14px">${eggs}</div><div class="serif" style="font-size:58px;margin-top:4px">买钢材 <span style="font-size:34px;font-family:'Noto Sans CJK SC';font-weight:700;color:#4a4338">谁也没有意见</span></div>
   <div style="height:3px;background:#1e1a15;margin:34px 0;opacity:.5"></div>
   <div id="hen" style="display:flex;align-items:center;gap:30px"><svg width="330" height="330" viewBox="0 0 200 200" style="position:relative">${ICON.hen('#c23b2a')}</svg><div><div style="font-size:34px;font-weight:700;color:#4a4338">买一只母鸡回家<br>天天下蛋</div><div class="serif" style="font-size:84px;color:#c23b2a;line-height:1.2;margin-top:6px">买钢厂</div><div style="font-size:34px;font-weight:700;color:#c23b2a">意见通通来了</div></div></div>`;
  s.io(eg,K('d6','你们')-.3,null,{y:20});const es=eg.querySelectorAll('.egg');const te=K('d6','你们');es.forEach((e,i)=>s.on(t=>{e.style.opacity=P(t,te+i*.22,te+i*.22+.25)}));
  const hen=eg.querySelector('#hen');s.on(t=>{const p=E.o(P(t,K('d6','而要')-.2,K('d6','而要')+.6));hen.style.opacity=p;hen.style.transform=`translateY(${(1-p)*24}px)`});}}
// ---------- 四 吵起来 ----------
{const A=SEC.debate;const e1=T('e1'),e2=T('e2'),e3=T('e3'),e5=T('e5'),e8=T('e8'),e9=T('e9'),e10=T('e10'),e11=T('e11'),e12=T('e12'),e13=T('e13'),e14=T('e14'),e15=T('e15');
 chapter('debate','四','吵起来','1979 — 1980',A.start,e1-.1);
 {const s=Film.scene('db1',e1-.1,e3-.2,{cls:'dark'});
  const a=s.add('div','left:64px;top:330px;font-size:104px;line-height:1.2','abs serif','意见<br>真的来了');s.io(a,e1,e2-.2,{y:20});
  const hd=s.add('div','left:64px;top:318px','abs');hd.innerHTML=`<div class="mono" style="font-size:44px;color:#ff9a4a;letter-spacing:.08em">1979 年起</div>`;s.io(hd,e2,null,{y:10});
  defCard(s,'调整','国家压缩基本建设规模，砍掉一批项目',64,400,900,K('e2','调整')-.3,null);
  const R=rng(5);const N=9;const tc=K('e2','砍项目')-.2;
  for(let i=0;i<N;i++){const big=i===3;const w=big?900:260+R()*420;const y=600+i*66;const row=s.add('div',`left:64px;top:${y}px;width:${w}px;height:${big?56:44}px;background:${big?'#ff7a1a':'#56616c'}`,'abs');
   if(big)row.innerHTML=`<span class="serif" style="position:absolute;left:16px;top:2px;font-size:36px;color:#10161d">宝钢　全国最大的建设项目</span>`;
   const cut=!big&&[0,2,5,6,8].includes(i);const tt=tc+i*.14;s.on(t=>{const a=E.o(P(t,e2+.3+i*.08,e2+.8+i*.08));row.style.opacity=a*(cut?1-.75*P(t,tt,tt+.4):1);row.style.transform=`scaleX(${a})`;row.style.transformOrigin='left'});
   if(cut){const x=s.add('div',`left:${64+w+14}px;top:${y-4}px;font-size:36px;color:#c23b2a;font-weight:900`,'abs','✕ 停、缓');s.io(x,tt,null,{y:0,x:-10})}}
  const lb=s.add('div','left:64px;top:1210px;font-size:26px;color:#8b959f','abs','示意：横条代表在建项目，非实际数据');s.io(lb,e2+.6,null,{y:0});}
 {const s=Film.scene('db2',e3-.2,e8-.2,{cls:'paper',theme:'paper'});
  const hd=s.add('div','left:64px;top:318px','abs');hd.innerHTML=`<div class="mono" style="font-size:40px;color:#9c3a1c;letter-spacing:.06em">1979.06.16 · 国务院财经委员会</div>`;s.io(hd,e3,e5-.3,{y:10});
  nameTag(s,'陈云','时任国务院副总理、国务院财经委主任',64,390,K('e3','陈云')-.3,null);
  const qs=[["应该说宝钢是<br><span style='color:#c23b2a'>仓促上马</span>的。",K('e3','仓促')-.5,''],["<span style='color:#c23b2a'>干到底</span>……<br>举棋不定不好。",K('e3','干到底')-.4,'「干到底」是李先念的话，陈云表示「我赞成这个意见」'],["买设备，同时也要<br>买技术，买专利。",K('e3','举棋')-.1,'']];
  qs.forEach((q,i)=>{const e=s.add('div',`left:64px;top:${490+i*228}px;width:952px;border-top:3px solid #1e1a15;padding-top:14px`,'abs');e.innerHTML=`<div class="q" style="position:relative;font-size:${i==2?54:66}px">「${q[0]}」</div>${q[2]?`<div style="font-size:23px;color:#6b6252;margin-top:6px">${q[2]}</div>`:''}`;s.io(e,q[1],e5-.3,{y:20})});
  // e5: 60 years vs 6 years
  nameTag(s,'陈锦华','时任上海市委副书记、宝钢工程指挥部政委',64,470,K('e5','陈锦华')-.3,null);
  const b=s.add('div','left:64px;top:580px;width:952px','abs');b.innerHTML=`<div class="serif" style="font-size:44px">鞍钢 → 600 万吨钢</div><div style="position:relative;height:70px;margin-top:8px"><div id="b60" style="position:absolute;left:0;top:0;bottom:0;background:#1e1a15"></div></div><div><span class="num" style="font-size:120px;line-height:1.05">60</span><span style="font-size:40px;font-weight:900"> 多年</span></div>
   <div class="serif" style="font-size:44px;margin-top:28px;color:#c23b2a">宝钢 → 600 万吨钢</div><div style="position:relative;height:70px;margin-top:8px"><div id="b6" style="position:absolute;left:0;top:0;bottom:0;background:#c23b2a"></div></div><div style="color:#c23b2a"><span style="font-size:40px;font-weight:900">不到 </span><span class="num" style="font-size:120px;line-height:1.05">6</span><span style="font-size:40px;font-weight:900"> 年</span><span class="serif" style="font-size:54px;margin-left:30px;color:#1e1a15">是不是真的能做得到？</span></div>`;
  s.io(b,K('e5','鞍钢')-.3,null,{y:20});const b60=b.querySelector('#b60'),b6=b.querySelector('#b6');const t60=K('e5','花了'),t6=K('e5','宝钢连');s.on(t=>{b60.style.width=(100*E.io(P(t,t60-.2,t60+1.6)))+'%';b6.style.width=(10*E.io(P(t,t6,t6+.6)))+'%'});
  const kids=b.children;[3,4,5].forEach(i=>{const k=kids[i];s.on(t=>{k.style.opacity=E.o(P(t,t6-.3,t6+.3))})});}
 {const s=Film.scene('db3',e8-.2,e13-.2,{cls:'dark'});
  const cv=canvas(s);const c=cv.getContext('2d');const R=rng(3);const seats=[];for(let r=0;r<13;r++){const rad=250+r*56;const n=Math.round(rad*Math.PI*.78/30);for(let i=0;i<n;i++){const a=Math.PI*(.11+.78*i/(n-1));seats.push([540-Math.cos(a)*rad*1.06,700+Math.sin(a)*rad*.86,R(),r])}}
  s.on(t=>{c.clearRect(0,0,W,H);const p=P(t,e8,e8+2);const dim=1-.72*E.io(P(t,e10-.4,e10+.3));c.fillStyle=`rgba(143,191,227,${.5*dim})`;c.fillRect(380,640,320,16);c.fillRect(440,610,200,12);
   for(const q of seats){const a=clamp(p*1.5-q[2]*.5);if(a<=0)continue;const v=90+q[2]*60|0;c.fillStyle=`rgba(${v},${v+12},${v+24},${a*.75*dim})`;c.beginPath();c.arc(q[0],q[1],7,0,6.3);c.fill();c.fillRect(q[0]-8,q[1]+8,16,8)}});
  const hd=s.add('div','left:64px;top:318px;width:952px','abs');hd.innerHTML=`<div class="mono" style="font-size:44px;color:#ff9a4a;letter-spacing:.08em">1980.09</div><div class="serif" style="font-size:64px;line-height:1.25;margin-top:4px">五届全国人大三次会议</div>`;s.io(hd,e8,e10-.3,{y:16});
  const q0=s.add('div','left:64px;top:520px;font-size:38px;font-weight:700;background:rgba(10,15,21,.8);padding:6px 14px','abs','代表们就宝钢 <span style="color:#ff7a1a">质询</span> 冶金部');s.io(q0,K('e8','代表们'),e9-.2,{y:10});
  const df=defCard(s,'质询','人大代表当面向政府部门提问，<br>部门必须回答',64,480,900,e9,e10-.3);df.style.background='rgba(10,15,21,.86)';df.style.padding='14px 22px';
  // counters
  const cn=s.add('div','left:64px;top:318px;width:952px;display:flex;justify-content:space-between','abs');cn.innerHTML=[['5','个代表团','北京、天津、上海等'],['4','次质询',''],['60','条意见','']].map(a=>`<div class="ct"><span class="num" style="font-size:190px;line-height:1;color:#ff7a1a">${a[0]}</span><div style="font-size:38px;font-weight:900;margin-top:-6px">${a[1]}</div><div style="font-size:24px;color:#aeb7bf;font-weight:500;height:30px">${a[2]}</div></div>`).join('');
  s.io(cn,e10-.1,e12-.3,{y:0});const cts=cn.querySelectorAll('.ct');[K('e10','5个'),K('e10','先后'),K('e10','提了')].forEach((tt,i)=>s.on(t=>{const p=E.o(P(t,tt-.15,tt+.35));cts[i].style.opacity=p;cts[i].style.transform=`translateY(${(1-p)*20}px)`}));
  const qq=[['工厂会不会滑到长江里去？','地基是软土层',K('e11','工厂')],['外国人会不会在矿石上卡我们？','矿石靠进口',K('e11','外国人')],['宝钢是不是无底洞？','投资',K('e11','是不是')],['13 年能不能收回投资？','冶金部称投产后 13 年可收回',K('e11','13年')]];
  qq.forEach((q,i)=>{const e=s.add('div',`left:64px;top:${640+i*152}px;width:952px;background:#e7dfca;color:#1e1a15;padding:16px 24px 14px;box-shadow:0 8px 24px #0008`,'abs');e.innerHTML=`<div style="font-size:23px;color:#6b6252;font-weight:700;letter-spacing:.1em">${q[1]}</div><div class="serif" style="font-size:${i==1?50:54}px;line-height:1.25">${q[0]}</div>`;s.io(e,q[2]-.25,e12-.3,{y:24,rot:[-.8,.6,-.4,.7][i]})});
  // newspaper
  const np=s.add('div','left:90px;top:330px;width:900px;height:900px;background:#e2d9c0;color:#1e1a15;padding:34px 40px;box-shadow:0 16px 50px #000a','abs');
  const col=n=>Array.from({length:n},()=>`<div style="height:9px;background:#1e1a15;opacity:.16;margin-bottom:9px;width:${86+((n*7)%14)}%"></div>`).join('');
  np.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:flex-end;border-bottom:5px double #1e1a15;padding-bottom:10px"><div class="serif" style="font-size:54px;letter-spacing:.1em">人民日报</div><div class="mono" style="font-size:24px;text-align:right;line-height:1.35">1980 年 9 月 5 日<br>第 4 版</div></div>
   <div style="font-size:30px;font-weight:700;margin-top:26px;letter-spacing:.06em">就宝钢建设中的一些问题</div><div class="serif" style="font-size:66px;line-height:1.25;margin-top:6px">人大北京代表<br>向冶金部提出质询</div><div style="font-size:26px;font-weight:700;margin-top:14px;line-height:1.5;color:#3a342b">唐克等当场回答，表示认真听取专家意见，把宝钢建设好</div>
   <div style="display:flex;gap:26px;margin-top:26px"><div style="flex:1">${col(15)}</div><div style="flex:1">${col(15)}</div><div style="flex:1">${col(15)}</div></div>
   <div style="position:absolute;right:26px;bottom:18px;font-size:22px;color:#6b6252">标题照录原报 · 版面为示意</div>`;
  s.io(np,e12+.1,null,{y:40,rot:-1.5,din:.7});}
 {const s=Film.scene('db4',e13-.2,A.end,{cls:'paper',theme:'paper'});
  const hd=s.add('div','left:64px;top:318px;font-size:32px;color:#4a4338;font-weight:700','abs','一位上海代表说（陈锦华听人转述）');s.io(hd,e13,e14-.3,{y:10});
  const q=s.add('div','left:64px;top:400px;width:952px;font-size:60px','q');q.innerHTML=`「宝钢要花 <span style="color:#c23b2a">200 个亿</span>，<br>全国 <span style="color:#c23b2a">10 亿人</span>，<br>一个人 <span style="color:#c23b2a">20 块钱</span>，<br>我 20 块钱还不能买<br>一个<span style="color:#c23b2a">发言权</span>哪？」`;s.io(q,K('e13','宝钢')-.3,e14-.3,{y:20});
  const eq=s.add('div','left:64px;top:920px;width:952px;border-top:3px solid #1e1a15;padding-top:20px;display:flex;align-items:baseline;justify-content:space-between','abs');
  eq.innerHTML=`<span class="p"><span class="num" style="font-size:120px;line-height:1">200</span><span style="font-size:34px;font-weight:900">亿元</span></span><span class="p num" style="font-size:80px">÷</span><span class="p"><span class="num" style="font-size:120px;line-height:1">10</span><span style="font-size:34px;font-weight:900">亿人</span></span><span class="p num" style="font-size:80px">=</span><span class="p" style="color:#c23b2a"><span class="num" style="font-size:150px;line-height:1">20</span><span style="font-size:34px;font-weight:900">元/人</span></span>`;
  s.io(eq,K('e13','宝钢')+.2,e14-.3,{y:0});const ps=eq.querySelectorAll('.p');[K('e13','200'),K('e13','全国')-.1,K('e13','全国'),K('e13','一个人')-.1,K('e13','一个人')+.1].forEach((tt,i)=>s.on(t=>{ps[i].style.opacity=E.o(P(t,tt,tt+.35))}));
  const m=s.add('div','left:64px;top:400px;width:952px','abs');m.innerHTML=`<div style="font-size:40px;font-weight:700;color:#4a4338">意思是：</div><div class="serif" style="font-size:88px;line-height:1.3;margin-top:10px">钱是大家的，<br>花钱的人<br>得把<span style="color:#c23b2a">账</span>讲清楚。</div>`;s.io(m,e14,e15-.3,{y:20});
  const z=s.add('div','left:64px;top:400px;width:952px','abs');z.innerHTML=`<div class="serif" style="font-size:84px;line-height:1.35">宝钢不是<br>一句话定下来的。</div><div class="serif" style="font-size:84px;line-height:1.35;color:#c23b2a;margin-top:26px">它被一条一条地<br>问过。</div>`;s.io(z,e15,null,{y:20});}}
})();
