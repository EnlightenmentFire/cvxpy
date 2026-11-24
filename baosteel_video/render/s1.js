// ===== 冷启动 / 片名 / 一 差距 =====
(function(){
// ---------- cold open ----------
{const A=SEC.cold;const s=Film.scene('cold',0,A.end,{xin:1.2,xout:.6,push:0});
 const cv=canvas(s);const c=cv.getContext('2d');
 const COLS=120,ROWS=192,PX=9,PY=10;const R=rng(7);const jit=new Float32Array(COLS*ROWS);for(let i=0;i<jit.length;i++)jit[i]=R();
 const bc0=45,br0=86;// 30x20 block
 const t3=T('c3'),tAdmin=K('c3','行政人员'),t4=T('c4'),tBig=K('c4','行政人员'),t5=T('c5'),t6=T('c6');
 s.on(t=>{c.clearRect(0,0,W,H);if(t<tAdmin-.3)return;
   const zp=E.io(P(t,tBig-.2,tBig+2.4));const z=lerp(2.9,1,zp);const cx=540,cy=lerp(1010,960,zp);const px=PX*z,py=PY*z;
   const grow=E.o(P(t,tAdmin-.3,tAdmin+1.6));const wave=P(t,tBig,tBig+2.6);const maxd=Math.hypot(COLS/2,ROWS/2*1.1);
   const dimAll=1-.86*E.io(P(t,t6-.2,t6+1.2));
   for(let r=0;r<ROWS;r++){const y=cy+(r-ROWS/2)*py;if(y<-py||y>H)continue;
    for(let q=0;q<COLS;q++){const x=cx+(q-COLS/2)*px;if(x<-px||x>W)continue;const i=r*COLS+q;
     const inb=q>=bc0&&q<bc0+30&&r>=br0&&r<br0+20;
     if(inb){const k=((r-br0)*30+(q-bc0))/600;if(k>grow)continue;c.fillStyle=`rgba(255,${122+jit[i]*40|0},26,${dimAll})`}
     else{if(t<tBig)continue;const d=Math.hypot(q-COLS/2,(r-ROWS/2)*1.1)/maxd;const a=clamp((wave*1.25-d)*6);if(a<=0)continue;const g=150+jit[i]*70|0;c.fillStyle=`rgba(${g},${g+8},${g+16},${a*.62*dimAll})`}
     drawFigure(c,x,y,px,py)}}});
 // location
 const loc=s.add('div','left:64px;top:330px','abs');loc.innerHTML=`<div class="mono" id="cdate" style="font-size:44px;letter-spacing:.08em;color:#ff9a4a"></div><div class="serif" style="font-size:150px;line-height:1.1;margin-top:10px">鞍山</div><div style="font-size:32px;color:#aeb7bf;margin-top:6px;font-weight:500">辽宁 · 鞍山钢铁公司所在地</div>`;
 s.io(loc,.5,t3-.5,{y:0});s.type(loc.querySelector('#cdate'),'1978.09.18',.7,9);
 const mp=MapView(s,0,760,1080,560,{stroke:'#5f7f99',sw:1.3});mp.view(MAP.places.anshan[0]+1.5,MAP.places.anshan[1]+1.2,62);
 mp.mark('anshan','鞍山',1.2,t3-.5,{});mp.mark('beijing','北京',1.6,t3-.5,{col:'#8fa3b5',fs:28,side:'l',tc:'#9fb0bf'});
 s.io(mp.sv,.6,t3-.5,{y:0,max:.9});
 nameTag(s,'邓小平','时任国务院副总理',64,660,T('c2'),t3-.5);nameTag(s,'邓小平','时任国务院副总理',64,300,t3-.1,t5+3.4);
 // labels during counting
 const plate=s.add('div','left:0;top:340px;width:1080px;height:540px;background:linear-gradient(rgba(8,12,17,0),rgba(8,12,17,.93) 14%,rgba(8,12,17,.93) 86%,rgba(8,12,17,0))','abs');s.io(plate,t3-.2,t6+.3,{y:0});
 const l1=s.add('div','left:64px;top:420px;width:952px','abs');l1.innerHTML=`<div style="font-size:36px;color:#c9d1d8;font-weight:500">日本一家钢铁企业 · 年产 <b style="color:#fff">600 万吨</b>钢</div><div style="display:flex;align-items:baseline;gap:22px;margin-top:6px"><span style="font-size:40px;font-weight:700">行政人员</span><span class="num" id="n600" style="font-size:250px;line-height:1;color:#ff7a1a">0</span><span style="font-size:60px;font-weight:900;color:#ff7a1a">人</span></div>`;
 s.io(l1,t3,tBig-.3,{y:20});const n600=l1.querySelector('#n600');s.on(t=>{n600.textContent=fmt(600*E.o(P(t,tAdmin-.2,tAdmin+1.5)))});
 const l2=s.add('div','left:0;top:392px;width:1080px','abs');l2.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:flex-end;padding:0 64px"><div style="font-size:36px;color:#c9d1d8;font-weight:500;line-height:1.35">鞍钢 · 年产 <b style="color:#fff">600 多万吨</b>钢<br><span style="font-size:40px;font-weight:700;color:#fff">行政人员</span></div><div style="text-align:right;line-height:1"><span style="font-size:26px;color:#ff9a4a;font-weight:700">日本企业　</span><span class="num" style="font-size:104px;color:#ff7a1a">600</span><span style="font-size:34px;color:#ff7a1a;font-weight:900"> 人</span></div></div><div style="text-align:center;margin-top:-6px"><span class="num" id="n23" style="font-size:392px;line-height:.92;color:#fff">0</span></div>`;
 s.io(l2,tBig-.1,t6+.2,{y:20});const n23=l2.querySelector('#n23');s.on(t=>{n23.textContent=fmt(23000*E.o(P(t,tBig,tBig+2.4)))});
 const x38=s.add('div','left:64px;top:1140px;width:952px;text-align:center','abs');x38.innerHTML=`<span style="display:inline-block;background:rgba(8,12,17,.9);padding:14px 34px;border:1px solid rgba(255,122,26,.7)"><span style="font-size:44px;font-weight:700">产量差不多　行政人员多出</span><span class="num" style="font-size:96px;color:#ff7a1a;line-height:1;margin:0 10px">≈38</span><span style="font-size:44px;font-weight:900;color:#ff7a1a">倍</span></span>`;
 s.io(x38,K('c5','差了')-.2,t6+.2,{y:20});
 const nx=s.add('div','left:0;top:820px;width:1080px','abs c');nx.innerHTML=`<div class="serif" style="font-size:84px;letter-spacing:.06em">一个多月后</div><div class="serif" style="font-size:84px;letter-spacing:.06em;color:#ff7a1a;margin-top:14px">日本，一个钢厂</div>`;
 s.io(nx,t6+.5,null,{y:20});}
// ---------- title ----------
{const A=SEC.title;const s=Film.scene('title',A.start,A.end,{cls:'bp',hud:false,xin:.7,xout:.6,push:.05});
 s.add('div','','bpgrid');
 const sv=svg(1080,1920,'left:0;top:0');s.add(sv);const g=document.createElementNS(NS,'g');g.setAttribute('transform','translate(540,1730) scale(1.0)');g.style.opacity=.5;sv.appendChild(g);
 addFurnace(s,g,{tin:A.start+.1,stagger:.1,dur:1.6});
 const b=s.add('div','left:0;top:430px;width:1080px','abs c');
 b.innerHTML=`<div class="mono" style="font-size:30px;letter-spacing:.3em;color:#9fc3e0">改革开放 · 第 1 期</div><div class="serif" style="font-size:132px;line-height:1.18;margin-top:36px;letter-spacing:.02em">一个厂<br>和一个国家</div><div style="width:120px;height:6px;background:#ff7a1a;margin:38px auto"></div><div class="serif" style="font-size:70px;color:#ffb070;letter-spacing:.1em">君津与宝钢</div><div class="mono" style="font-size:34px;letter-spacing:.2em;color:#9fc3e0;margin-top:26px">1977 — 1985</div>`;
 s.io(b,A.start+.4,null,{y:30,din:.9});}
// ---------- 一 差距 ----------
{const A=SEC.gap;const tA=T('a1');
 // chapter card
 chapter('gap','一','差距','有多大',A.start,tA-.1);
 // a1: delegation, map route
 {const s=Film.scene('gap1',tA-.1,T('a3')-.2,{cls:'bp'});s.add('div','','bpgrid');
  const mp=MapView(s,0,560,1080,700);const pl=MAP.places;
  s.on(t=>{const p=E.io(P(t,tA,tA+5));mp.view(lerp(pl.beijing[0]+2,(pl.beijing[0]+pl.tokyo[0])/2,p),lerp(pl.beijing[1]+1,(pl.beijing[1]+pl.tokyo[1])/2+1.2,p),lerp(60,42,p))});
  mp.mark('beijing','北京',tA+.2,null,{side:'l'});mp.mark('tokyo','东京',tA+2.6,null,{side:'t'});mp.route('beijing','tokyo',tA+1.2,2.2);
  const h=s.add('div','left:64px;top:320px','abs');h.innerHTML=`<div class="mono" style="font-size:44px;color:#ff9a4a;letter-spacing:.08em">1977.09</div><div class="serif" style="font-size:76px;line-height:1.2;margin-top:6px">一个代表团去日本</div>`;s.io(h,tA,null,{y:20});
  nameTag(s,'叶志强','时任冶金部副部长',64,1150,K('a1','副部长')-.3,null);
  defCard(s,'冶金部','当时管全国钢铁的部委',64,470,700,K('a1','也就是')-.2,null);}
 // a3-a5: bars
 {const t3=T('a3'),t4=T('a4'),t5=T('a5');const s=Film.scene('gap2',t3-.2,T('a6')-.2,{cls:'dark'});
  const base=1200,maxH=640,sc=maxH/12000;const bx=[250,640],bw=230;
  s.add('div',`left:64px;top:${base}px;width:952px;height:3px;background:#59636d`,'abs');
  const yr=s.add('div','left:64px;top:312px','abs num','');yr.style.cssText+='font-size:150px;line-height:1;color:#f1ede4';
  const ysub=s.add('div','left:380px;top:372px;font-size:34px;color:#aeb7bf;font-weight:500','abs','两国钢产量（万吨）');s.io(ysub,t3,null,{y:0});
  const yJ=K('a3','1960年'),yK=K('a4','1973年');
  s.on(t=>{const p=P(t,yK-.5,yK+.9);yr.textContent=p<=0?'1960':p>=1?'1973':String(1960+Math.round(13*E.io(p)));yr.style.opacity=P(t,yJ-.2,yJ+.3)});
  const d=[{n:'日本',c:'#d9dee3',v0:2200,v1:11900,t0:K('a3','日本'),t1:K('a4','日本'),lab1:'1.19 亿吨'},{n:'中国',c:'#ff7a1a',v0:1866,v1:2522,t0:K('a3','中国'),t1:K('a4','中国'),lab1:'2,522 万吨'}];
  d.forEach((o,i)=>{const b=s.add('div',`left:${bx[i]}px;top:${base}px;width:${bw}px;height:0;background:${o.c}`,'abs');
   const v=s.add('div',`left:${bx[i]-80}px;width:${bw+160}px;top:0;text-align:center;color:${o.c}`,'abs num');v.style.fontSize='92px';v.style.lineHeight='1';
   const n=s.add('div',`left:${bx[i]}px;width:${bw}px;top:${base+18}px;text-align:center;font-size:50px;color:${o.c}`,'abs serif',o.n);s.io(n,o.t0-.2,null,{y:0});
   s.on(t=>{const a=E.o(P(t,o.t0-.1,o.t0+1.1)),g=E.io(P(t,o.t1-.2,o.t1+1.8));const val=o.v0*a+(o.v1-o.v0)*g;const hh=val*sc;b.style.height=hh+'px';b.style.top=(base-hh)+'px';
    v.style.top=(base-hh-108)+'px';v.textContent=g>=1?o.lab1:fmt(val);v.style.opacity=a;v.style.fontSize=(g>=1&&i==0?84:92)+'px'})});
  const eq=s.add('div','left:64px;top:500px;width:952px;font-size:40px;color:#aeb7bf;font-weight:500','abs','1960 年：差不多');s.io(eq,K('a3','差不多')-.1,yK-.6,{y:10});
  const r=s.add('div','left:590px;top:560px;width:440px','abs');r.innerHTML=`<div style="font-size:38px;font-weight:700;line-height:1.35">13 年后<br>中国只有日本的</div><div class="num" style="font-size:200px;line-height:1;color:#ff7a1a">1/5</div><div class="mono" style="font-size:24px;color:#8b959f">2,522 ÷ 11,900 ≈ 21%</div>`;
  s.io(r,K('a5','变成')-.3,null,{y:20});
  const lr=s.add('div','left:64px;top:1268px;font-size:23px;color:#8b959f','abs','劳动生产率：报告称日本「比中国高 10 倍以上」');s.io(lr,t5+.2,null,{y:0});s.sub=true;}
 // a6-a8: Kimitsu & furnace explainer
 {const t6=T('a6'),t7=T('a7'),t9=T('a9');const s=Film.scene('gap3',t6-.2,t9-.2,{cls:'bp'});s.add('div','','bpgrid');
  const h=s.add('div','left:64px;top:318px','abs');h.innerHTML=`<div class="serif" style="font-size:92px;line-height:1.15">君津制铁所</div><div style="font-size:34px;color:#c3d6e6;font-weight:500;margin-top:8px">日本 千叶县 · 东京湾边</div>`;s.io(h,K('a6','君津')-.5,t7-.4,{y:20});
  const pre=s.add('div','left:64px;top:330px;font-size:64px','abs serif','再看一个厂');s.io(pre,t6,K('a6','君津')-.6,{y:10});
  defCard(s,'新日铁','新日本制铁，当时日本最大的钢铁公司',64,470,860,K('a6','新日铁')-.2,K('a6','1971')-.4);
  const sv=svg(1080,1920,'left:0;top:0');s.add(sv);
  // three furnaces
  const gs=[[-1,235,.52],[0,540,.52],[1,845,.52]].map((a,i)=>{const g=document.createElementNS(NS,'g');sv.appendChild(g);g._x=a[1];addFurnace(s,g,{tin:t6+.15+i*.3,stagger:.05,dur:.9,order:['ground','shell','bands','frame','bustle','uptake','downcomer','dust']});return g});
  s.on(t=>{const p=E.io(P(t,t7-.4,t7+.6));const q=0;
    gs.forEach((g,i)=>{const sc=i==1?lerp(.52,1.12,p-q*p):lerp(.52,.52,p);const x=lerp(g._x,i==1?430:g._x,p-q*p);g.setAttribute('transform',`translate(${x},1210) scale(${sc})`);g.style.opacity=i==1?1:1-(p-q*p)*.95})});
  const fl=s.add('div','left:64px;top:1222px;font-size:30px;color:#c3d6e6;font-weight:500','abs','<span class="num" style="font-size:44px;color:#fff">1 · 2 · 3</span>　号高炉（1968—1971 年相继点火）');s.io(fl,K('a6','三座')-.3,t7-.4,{y:0});
  const big=s.add('div','left:64px;top:500px;width:952px','abs');big.innerHTML=`<div style="font-size:40px;font-weight:700">1971 年 · 三座高炉</div><div style="display:flex;align-items:baseline;gap:16px"><span style="font-size:44px;font-weight:700">年产能</span><span class="num" style="font-size:230px;line-height:1.05;color:#ff7a1a">1,000</span><span style="font-size:62px;font-weight:900;color:#ff7a1a">万吨</span></div>`;
  s.io(big,K('a6','形成')-.6,t7-.3,{y:20});
  // explainer callouts for furnace (centre furnace enlarged at x=430)
  const ex=s.add('div','left:0;top:0;width:1080px;height:1920px','abs');
  ex.innerHTML=`<div class="abs" style="left:64px;top:320px;font-size:36px;font-weight:500;color:#c3d6e6"><b class="serif" style="font-size:92px;color:#fff">高炉</b>　把铁矿石炼成铁水的炉子</div>
   <div class="abs" style="left:64px;top:600px;font-size:30px;line-height:1.3;color:#fff;font-weight:700">铁矿石、焦炭 →<br><span style="font-size:24px;color:#9fc3e0;font-weight:500">从炉顶装入</span></div>
   <div class="abs" style="left:64px;top:1010px;font-size:30px;line-height:1.3;color:#fff;font-weight:700">热风 →<br><span style="font-size:24px;color:#9fc3e0;font-weight:500">吹进炉内</span></div>
   <div class="abs" style="left:560px;top:1130px;font-size:30px;line-height:1.3;color:#ff9a4a;font-weight:700">→ 铁水<br><span style="font-size:24px;color:#9fc3e0;font-weight:500">从炉底流出</span></div>
   <div class="abs" style="left:660px;top:700px;width:380px;border-left:5px solid #ff7a1a;padding-left:18px;font-size:34px;line-height:1.4;font-weight:700">炉子多大<br>基本决定一个厂<br>能出多少铁</div>`;
  const kids=[...ex.children];s.io(kids[0],t7,t9+.2,{y:10});s.io(kids[1],K('a7','铁矿石')-.2,t9+.2,{y:10});s.io(kids[2],K('a7','炼成'),t9+.2,{y:10});s.io(kids[3],K('a7','铁水'),t9+.2,{y:10});s.io(kids[4],K('a7','炉子多大')-.2,t9+.2,{x:20,y:0});
  // glow inside the big furnace
  const glow=s.add('div','left:330px;top:1040px;width:200px;height:170px;background:radial-gradient(closest-side,rgba(255,150,40,.75),rgba(255,122,26,0));mix-blend-mode:screen','abs');s.io(glow,K('a7','铁水')-.3,t9+.2,{y:0});}
 // a9-a11: circles
 {const t9=T('a9'),t10=T('a10'),t11=T('a11');const s=Film.scene('gap4',t9-.2,A.end,{cls:'dark'});
  const r1=170,r2=r1*Math.sqrt(2.39);const cy=830;const x1=64+r1+10,x2=1080-64-r2-4;
  const c1=s.add('div',`left:${x1-r1}px;top:${cy-r1}px;width:${2*r1}px;height:${2*r1}px;border-radius:50%;border:5px solid #d9dee3;background:rgba(217,222,227,.1)`,'abs');
  const c2=s.add('div',`left:${x2-r2}px;top:${cy-r2}px;width:${2*r2}px;height:${2*r2}px;border-radius:50%;border:5px solid #ff7a1a;background:rgba(255,122,26,.14)`,'abs');
  s.io(c1,t9-.2,null,{y:0,s:-.4,din:.9});s.io(c2,K('a9','中国')-.2,null,{y:0,s:-.4,din:1.1});
  const L1=s.add('div',`left:${x1-190}px;top:${cy-92}px;width:380px;text-align:center`,'abs');L1.innerHTML=`<div class="serif" style="font-size:40px">君津一个厂</div><div class="num" style="font-size:104px;line-height:1">1,000</div><div style="font-size:28px;font-weight:700;color:#aeb7bf">万吨 · 年产能</div>`;s.io(L1,t9,null,{y:0});
  const L2=s.add('div',`left:${x2-240}px;top:${cy-120}px;width:480px;text-align:center;color:#ffb070`,'abs');L2.innerHTML=`<div class="serif" style="font-size:46px">中国全国</div><div class="num" style="font-size:150px;line-height:1;color:#ff7a1a">2,390</div><div style="font-size:28px;font-weight:700">万吨 · 1975 年产量</div>`;s.io(L2,K('a9','中国'),null,{y:0});
  const hd=s.add('div','left:64px;top:316px;width:952px','abs');hd.innerHTML=`<div class="serif" style="font-size:66px;line-height:1.25">一个厂　对　一个国家</div><div style="font-size:30px;color:#aeb7bf;font-weight:500;margin-top:6px">圆的面积按吨数画</div>`;s.io(hd,t9-.1,null,{y:16});
  const res=s.add('div','left:64px;top:1112px;width:952px;text-align:center','abs');res.innerHTML=`<span style="font-size:40px;font-weight:700">全国所有钢厂加起来 = </span><span class="num" style="font-size:120px;color:#ff7a1a;line-height:1">2.39</span><span style="font-size:40px;font-weight:700"> 个君津</span>`;s.io(res,K('a10','也只是')-.2,null,{y:20});
  const note=s.add('div','left:64px;top:1256px;width:952px;text-align:center;font-size:23px;color:#8b959f','abs','君津为设计产能，非当年实际产量');s.io(note,t10+.5,null,{y:0});}
}
})();
// chapter card used by all sections
function chapter(id,no,title,sub,t0,t1){const s=Film.scene('ch_'+id,t0,t1,{cls:'bp',hud:false,xin:.35,xout:.35,push:.03});s.add('div','','bpgrid');
 const b=s.add('div','left:0;top:640px;width:1080px','abs c');b.innerHTML=`<div class="num" style="font-size:40px;letter-spacing:.3em;color:#9fc3e0">— ${no} —</div><div class="serif" style="font-size:190px;line-height:1.15;letter-spacing:.06em;margin-top:10px">${title}</div><div class="serif" style="font-size:60px;color:#ffb070;letter-spacing:.2em;margin-top:8px">${sub||''}</div>`;
 s.io(b,t0+.1,null,{y:24,din:.5});return s}
