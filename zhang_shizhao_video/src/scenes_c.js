// 场景（三）：第四至六章、收尾
const CH4='肆 · 有容',CH5='伍 · 两个桃子',CH6='陆 · 老虎总长';
function tigerSeal(root,x,y,size,dark){ // “虎”字圆印（甲寅＝虎年）
  const e=h('div','abs black trad','虎',root,{left:x+'px',top:y+'px',width:size+'px',height:size+'px',borderRadius:'50%',border:`${Math.round(size*.05)}px solid ${dark?'#c23a2b':'#a5281d'}`,color:dark?'#c23a2b':'#a5281d',fontSize:size*.62+'px',textAlign:'center',lineHeight:size*.84+'px',boxShadow:`inset 0 0 0 ${Math.round(size*.03)}px ${dark?'#15120f':'#e9dfc8'}, inset 0 0 0 ${Math.round(size*.045)}px ${dark?'#c23a2b':'#a5281d'}`});
  return e;}
function magCover(root,x,y,w,hh,sub1,sub2){
  const c=h('div','abs',null,root,{left:x+'px',top:y+'px',width:w+'px',height:hh+'px',background:'#e9dfc8',border:'3px solid #1b1814',boxShadow:'0 16px 40px rgba(27,24,20,.4)'});
  h('div','abs',null,c,{left:'18px',top:'18px',right:'18px',bottom:'18px',border:'2px solid #1b1814'});
  h('div','abs v black trad inkf','甲寅',c,{right:'60px',top:'60px',fontSize:w*.3+'px',letterSpacing:'10px',lineHeight:'1'});
  h('div','abs v bold trad',sub1,c,{left:'70px',top:'70px',fontSize:w*.062+'px',letterSpacing:'8px'});
  h('div','abs v sans',sub2,c,{left:'130px',top:'70px',fontSize:w*.044+'px',letterSpacing:'6px',color:'#3a332b'});
  tigerSeal(c,w*.1,hh-w*.36-46,w*.36);
  return c;}

// ── 第四章 ───────────────────────────────────────────────
E.add({id:'jiayin',nokb:true,a:C('c4_1')-.1,b:C('c4_2')-.1,chap:CH4,
  build(r,s){h('div','bg old',null,r);
    s.cam=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',transformOrigin:'540px 700px'});
    s.cv=magCover(s.cam,220,300,640,800,'第一卷第一號','中華民國三年五月 · 東京');
    s.cap=h('div','abs sans','封面为示意重排 · 甲寅年即虎年',r,{left:'220px',top:'1114px',fontSize:'24px',letterSpacing:'2px',color:'#6b6052'});
    s.tag=personTag(r,'章士钊','33 岁 · 流亡东京 · 笔名“秋桐”',64,1160,'di');
  },
  update(t,lt,s){const a=C('c4_1'),d=CE('c4_1')-a;const z=P(t,a,d+.5,ease.io2);s.cam.style.transform=`scale(${lerp(.94,1,z)}) rotate(${lerp(-2,-.6,z)}deg)`;
    fin(s.tag,t,a+d*.3,.5,20);s.cap.style.opacity=P(t,a+d*.5,.5);}
});
quoteScene({id:'yourong',a:C('c4_2')-.1,b:C('c4_5')-.05,chap:CH4,who:'秋桐《政本》<br>《甲寅》第一期 · 1914',
  cols:['為政有本','本何在','曰在有容','何謂有容','曰不好同惡異'],x:1000,y:440,fs:86,pitch:132,dots:[null,null,[2,3],null,[1,2,3,4,5]],
  qa:C('c4_2')+.1,qd:(CE('c4_2')-C('c4_2'))-.5,
  gloss:[['好同惡異＝亲近相同的，厌恶不同的',250,470]],
  plain:{html:'政治的根本，是<mark>容得下人</mark>：不因为你跟我一样就亲近你，也不因为你跟我不一样就容不得你。',at:C('c4_3')-.1,out:C('c4_4')-.1,y:1050,fs:44},
  plain2:{html:'那时人人都想消灭对手，他却说：<br><mark>留着对手，才叫政治。</mark>',at:C('c4_4'),y:1050,fs:47,lab:'厉害在哪儿'},
  src:['原文','《政本》，《甲寅》第1卷第1号（1914年5月10日）；经学术论文引文核对'],
});
quoteScene({id:'tiaohe',a:C('c4_5')-.1,b:C('c4_7')-.05,chap:CH4,who:'《调和立国论》<br>《甲寅》第四期 · 1914',
  cols:['調和生於相抵','成於相讓','無抵力不足以言調和','無讓德不足以言調和'],x:1000,y:470,fs:74,pitch:150,dots:[[4,5],[2,3],[1,2],[1,2]],
  qa:C('c4_6')+.1,qd:(CE('c4_6')-C('c4_6'))-.5,
  src:['原文','《调和立国论（上）》，《甲寅》第1卷第4号（1914年11月）；原句句首有“愚闻”二字'],
  build(r,s){s.k=h('div','abs',`<div class="sans" style="font-size:30px;letter-spacing:6px;color:#a5281d;font-weight:700">怎么留？</div><div class="black trad" style="font-size:150px;letter-spacing:14px;line-height:1.15">調和</div><div class="sans" style="font-size:34px;color:#3a332b;font-weight:500;line-height:1.5;margin-top:10px">他自己开了<br><b style="color:#a5281d;font-size:44px">两个条件</b></div>`,r,{left:'64px',top:'470px',width:'360px'});
    s.c1=h('div','abs black','① 抵力',r,{left:'64px',top:'910px',fontSize:'64px',color:'#2c4563'});s.c2=h('div','abs black','② 让德',r,{left:'64px',top:'1010px',fontSize:'64px',color:'#a67c2e'});},
  update(t,lt,s){fin(s.k,t,C('c4_5'),.6,24);const a=C('c4_6'),d=CE('c4_6')-a;fin(s.c1,t,a+d*.5,.5,20);fin(s.c2,t,a+d*.78,.5,20);}
});
// 拔河
function puller(parent,x,y,flip,col){const g=svg('g',{transform:`translate(${x},${y})`},parent);const b=svg('g',{},g);
  svg('circle',{cx:0,cy:-150,r:24,fill:col},b);svg('path',{d:'M-22,-122 L22,-122 L30,0 L-30,0 Z',fill:col},b);svg('path',{d:`M${flip?-18:18},-100 L${flip?-74:74},-84`,stroke:col,'stroke-width':14,'stroke-linecap':'round'},b);
  return {g,b,x,flip};}
E.add({id:'tug',a:C('c4_7')-.1,b:C('c4_9')-.05,chap:CH4,
  build(r,s){h('div','bg light',null,r);
    s.ttl=h('div','abs',`<span class="sans" style="font-size:26px;font-weight:700;letter-spacing:6px;color:#e8ddc5;background:#a5281d;padding:3px 12px 4px 16px">打个比方</span><div class="black" style="font-size:96px;letter-spacing:10px;margin-top:10px">拔河</div>`,r,{left:'64px',top:'292px'});
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    svg('line',{x1:40,y1:860,x2:1040,y2:860,stroke:'#1b1814','stroke-width':4},sv);svg('line',{x1:540,y1:830,x2:540,y2:890,stroke:'#1b1814','stroke-width':4,'stroke-dasharray':'6 6'},sv);
    s.rope=svg('path',{d:'',stroke:'#6b4a1f','stroke-width':10,fill:'none','stroke-linecap':'round'},sv);
    s.L=[150,250,350].map(x=>puller(sv,x,860,false,'#2c4563'));s.R=[730,830,930].map(x=>puller(sv,x,860,true,'#a67c2e'));
    s.flag=svg('path',{d:'M0,-12 L0,40 L-16,62 L0,52 L16,62 L0,40',fill:'#a5281d',stroke:'#a5281d','stroke-width':6,'stroke-linejoin':'round'},sv);
    s.la=h('div','abs sans','甲',r,{left:'150px',top:'640px',width:'200px',textAlign:'center',fontSize:'34px',fontWeight:'700',color:'#2c4563',letterSpacing:'4px'});
    s.lb=h('div','abs sans','乙',r,{left:'730px',top:'640px',width:'200px',textAlign:'center',fontSize:'34px',fontWeight:'700',color:'#a67c2e',letterSpacing:'4px'});
    s.t1=h('div','abs',`<span class="black" style="font-size:64px;color:#2c4563">抵力</span><span class="sans" style="font-size:36px;font-weight:500;color:#3a332b;margin-left:18px">两边力气相当，绳子才拉得住</span>`,r,{left:'64px',top:'960px'});
    s.t2=h('div','abs',`<span class="black" style="font-size:64px;color:#a67c2e">让德</span><span class="sans" style="font-size:36px;font-weight:500;color:#3a332b;margin-left:18px">两边都肯松一把手，才能收场</span>`,r,{left:'64px',top:'1070px'});
    s.x1=h('div','abs black','✕',r,{left:'930px',top:'952px',fontSize:'76px',color:'#a5281d'});s.x2=h('div','abs black','✕',r,{left:'930px',top:'1062px',fontSize:'76px',color:'#a5281d'});
    s.t3=h('div','abs bold','1914 年的中国：<span class="red">有力量的不肯让，肯让的没力量。</span>',r,{left:'64px',top:'1186px',fontSize:'42px',lineHeight:'1.35',width:'952px'});
  },
  update(t,lt,s){const a=C('c4_7'),d=CE('c4_7')-a,b=C('c4_8'),e=CE('c4_8')-b;
    fin(s.ttl,t,a,.5,20);
    const pull=P(t,a+d*.12,.6,ease.out3)*(1-P(t,a+d*.62,.8,ease.io)); // 0→1 用力，随后松手
    const un=P(t,b+.2,1.2,ease.io); // 1914：失衡
    const lean=18*pull+16*un, leanR=18*pull*(1-un);
    const shiftAll=-120*un;const jit=pull>.5&&un===0?Math.sin(t*9)*5*pull:0;
    s.L.forEach((p,i)=>{p.g.setAttribute('transform',`translate(${p.x+shiftAll*.5+jit},860)`);p.b.setAttribute('transform',`rotate(${-lean})`);});
    s.R.forEach((p,i)=>{const gone=i>0?un:0;p.g.setAttribute('transform',`translate(${p.x+shiftAll+jit},860)`);p.b.setAttribute('transform',`rotate(${leanR-un*10})`);p.g.style.opacity=1-gone*.85;});
    const lx=350+60+shiftAll*.5+jit,rx=730-60+shiftAll+jit;const sag=(1-pull)*(1-un)*46;
    s.rope.setAttribute('d',`M${lx-290},${760} L${lx},${760} Q${(lx+rx)/2},${760+sag*2} ${rx},${760} L${rx+290},${760}`);
    s.flag.setAttribute('transform',`translate(${(lx+rx)/2},${760+sag})`);
    s.la.innerHTML=un>.5?'袁世凯 · 大权在握':'甲';s.lb.innerHTML=un>.5?'反对派 · 流亡海外':'乙';s.la.style.left=(150+shiftAll*.5)+'px';s.la.style.width=un>.5?'340px':'200px';s.lb.style.left=(700+shiftAll*.6)+'px';s.lb.style.width=un>.5?'340px':'200px';
    fin(s.t1,t,a+d*.2,.5,20);fin(s.t2,t,a+d*.6,.5,20);
    [s.x1,s.x2].forEach((x,i)=>{const p=P(t,b+e*(.55+i*.25),.3,ease.back);A(x,{o:clamp(p*2),s:lerp(1.8,1,p)});});
    fin(s.t3,t,b+e*.3,.6,20);}
});
E.add({id:'take4',a:C('c4_9')-.1,b:CE('c4_9')+.9,chap:CH4,
  build(r,s){h('div','bg light',null,r);
    s.lab=h('div','abs sans','这说明什么',r,{left:'64px',top:'292px',fontSize:'26px',fontWeight:'700',letterSpacing:'6px',color:'#e8ddc5',background:'#a5281d',padding:'3px 12px 4px 16px'});
    s.st=h('div','take','他自己写下的两个条件，<br>当时的中国，<br><span class="red">一个也不具备。</span>',r,{left:'64px',top:'360px',fontSize:'74px',width:'960px'});
    s.q=[['無抵力不足以言調和',760],['無讓德不足以言調和',900]].map(([tx,y])=>{const e=h('div','abs black trad inkf',tx,r,{left:'64px',top:y+'px',fontSize:'66px',letterSpacing:'5px',color:'#6b6052',whiteSpace:'nowrap'});return e;});
    s.x=[760,900].map(y=>h('div','abs black','✕',r,{left:'880px',top:(y-14)+'px',fontSize:'90px',color:'#a5281d'}));
    s.note=h('div','abs sans','他的理论没有错——错的是时候。',r,{left:'64px',top:'1080px',fontSize:'38px',color:'#3a332b',fontWeight:'500',display:'none'});
  },
  update(t,lt,s){const a=s.a;A(s.lab,{o:P(t,a,.4)});fin(s.st,t,a+.3,.6,24);s.q.forEach((q,i)=>fin(q,t,a+1.2+i*.4,.5,20));
    s.x.forEach((x,i)=>{const p=P(t,a+2.2+i*.4,.3,ease.back);A(x,{o:clamp(p*2),s:lerp(1.8,1,p)});});}
});

// ── 第五章 ───────────────────────────────────────────────
E.add({id:'wenyan',a:C('c5_1')-.1,b:C('c5_2')-.1,chap:CH5,
  build(r,s){h('div','bg light',null,r);
    s.hd=h('div','abs sans','一九二三年八月 · 上海《新闻报》',r,{left:'64px',top:'300px',fontSize:'30px',letterSpacing:'5px',color:'#6b6052',fontWeight:'500'});
    s.w=h('div','abs v black trad inkf','文言',r,{left:'610px',top:'400px',fontSize:'270px',letterSpacing:'10px',lineHeight:'1'});
    s.bh=h('div','abs v black trad','白話',r,{left:'200px',top:'400px',fontSize:'270px',letterSpacing:'10px',lineHeight:'1',color:'transparent',webkitTextStroke:'4px #6b6052'});
    s.vs=h('div','abs sans','对',r,{left:'490px',top:'640px',width:'100px',textAlign:'center',fontSize:'44px',color:'#a5281d',fontWeight:'700'});
    s.tag=personTag(r,'章士钊','《评新文化运动》作者 · 只认文言',64,1040,'di');
    s.ex=h('div','abs bold','他举了个例子 ——',r,{left:'64px',top:'1190px',fontSize:'50px'});
  },
  update(t,lt,s){const a=C('c5_1'),d=CE('c5_1')-a;s.hd.style.opacity=P(t,a+d*.25,.5);fin(s.w,t,a,.6,30);fin(s.bh,t,a+d*.5,.6,30);s.vs.style.opacity=P(t,a+d*.5,.4);fin(s.tag,t,a+d*.2,.5,20);fin(s.ex,t,a+d*.8,.5,20);}
});
// peaches 在 scenes_a.js
E.add({id:'luxun',a:C('c5_5')-.1,b:C('c5_6')-.05,chap:CH5,
  build(r,s){h('div','bg light',null,r);
    s.tag=personTag(r,'鲁迅','本名周树人 · 这次署名“雪之”',64,300,'di');
    s.who=h('div','abs sans','《晨报副刊》<br>1923 年 9 月',r,{right:'64px',top:'304px',fontSize:'28px',letterSpacing:'4px',color:'#6b6052',fontWeight:'500',textAlign:'right',lineHeight:'1.45'});
    s.bai=h('div','abs black','两个桃子杀了三个<span style="position:relative;display:inline-block">读书人<i style="position:absolute;left:-4px;right:-4px;top:54%;height:7px;background:#a5281d;transform-origin:0 50%"></i><b style="position:absolute;left:8px;top:-66px;font-size:60px;color:#a5281d;font-family:var(--serif);white-space:nowrap;transform:rotate(-5deg)">勇士！</b></span>',r,{left:'64px',top:'560px',fontSize:'70px',letterSpacing:'2px',whiteSpace:'nowrap'});
    s.strike=s.bai.querySelector('i');s.fix=s.bai.querySelector('b');
    s.n=h('div','abs sans','《晏子春秋》里，这三人“以勇力搏虎闻”——是武士，不是书生。',r,{left:'64px',top:'680px',width:'952px',fontSize:'33px',lineHeight:'1.45',color:'#3a332b',fontWeight:'500'});
    s.q=h('div','abs black trad',null,r,{left:'64px',top:'830px',width:'952px',fontSize:'62px',lineHeight:'1.42',letterSpacing:'2px'});
    s.qs=chars(s.q,'「不但那時使三個讀書人因此送命，到現在還使一個讀書人因此出醜。」');s.qs.forEach((x,i)=>{x.classList.add('inkf');if(i>=21&&i<=25)x.style.color='#a5281d';});
    s.g=h('div','abs sans','↑ 这“一个读书人”，说的就是章士钊',r,{left:'64px',top:'1210px',fontSize:'33px',color:'#a5281d',fontWeight:'700'});
    s.src=srcTag(r,'原文','鲁迅〈“两个桃子杀了三个读书人”〉，1923年9月14日；后录入《再来一次》');
  },
  update(t,lt,s){const a=C('c5_5'),d=CE('c5_5')-a;fin(s.tag,t,a,.5,20);s.who.style.opacity=P(t,a+.2,.5);fin(s.bai,t,a+.1,.5,20);
    const k=P(t,a+d*.14,.35,ease.out3);s.strike.style.transform=`scaleX(${k})`;const f=P(t,a+d*.2,.3,ease.back);s.fix.style.opacity=clamp(f*2);s.fix.style.transform=`rotate(-5deg) scale(${lerp(1.6,1,f)})`;
    s.n.style.opacity=P(t,a+d*.24,.5);reveal(s.qs,t,a+d*.45,d*.5);s.g.style.opacity=P(t,a+d*.97,.5);fin(s.src,t,a+1,.6,12);}
});
quoteScene({id:'reply',a:C('c5_6')-.1,b:C('c5_7')-.05,chap:CH5,tag:['章士钊','两年后 · 重刊此文时加的按语','di'],who:'《甲寅》周刊<br>1925 年 9 月',
  cols:['此等小節','寧關謀篇本旨'],x:900,y:500,fs:92,pitch:190,dots:[null,[0,1]],
  qa:C('c5_6')+(CE('c5_6')-C('c5_6'))*.3,qd:(CE('c5_6')-C('c5_6'))*.3,
  gloss:[['寧＝难道',420,560]],
  plain:{html:'这点小地方，<mark>跟文章的主旨有什么关系？</mark>',at:C('c5_6')+(CE('c5_6')-C('c5_6'))*.64,y:1160,fs:44},
  src:['原文','《甲寅》周刊第1卷第9号（1925年9月12日）按语；据《鲁迅全集》注释引文'],
});
takeWebScene({id:'take5',a:C('c5_7')-.1,b:CE('c5_7')+.9,chap:CH5,html:'他那支笔，头一回碰上了<span class="red">不买账的人。</span>',fs:46,old:['zsz','ymz','zty','wzh','szs','wrn','wcq','hx','ysk'],add:['lx'],labels:{'zsz-lx':'笔战'}});

// ── 第六章 ───────────────────────────────────────────────
E.add({id:'zhizheng',a:C('c6_1')-.1,b:C('c6_2')-.05,chap:CH6,
  build(r,s){h('div','bg old',null,r);
    s.frame=h('div','abs',null,r,{left:'0',top:'300px',width:'1080px',height:'400px',overflow:'hidden',borderTop:'4px solid #1b1814',borderBottom:'4px solid #1b1814',background:'#ddd0b0'});
    s.map=GeoMap(s.frame,'eastasia',{id:'d'});s.map.city('北京',{sub:'1924',dy:-30});
    s.tag=personTag(r,'段祺瑞','临时执政 · 1924–1926',64,730,'guan');
    s.def=defBox(r,'执政府','段祺瑞 1924 到 1926 年主持的北京政府。',64,870);
    s.tl=[['1924.11','司法总长'],['1925.4','兼署教育总长'],['1925.7','专任教育总长']].map(([y,tt],i)=>h('div','abs',`<div class="sans" style="font-size:28px;color:#a5281d;font-weight:700;letter-spacing:2px">${y}</div><div class="black" style="font-size:${i?38:42}px;margin-top:4px">${tt}</div>`,r,{left:(64+i*322)+'px',top:'1130px',width:'300px',borderTop:'6px solid #1b1814',paddingTop:'12px'}));
  },
  update(t,lt,s){const a=C('c6_1'),d=CE('c6_1')-a;const M=s.map.M,[bx,by]=M.cities['北京'];const z=P(t,a,d,ease.io2);s.map.view(bx+60,by+40,540,200,lerp(.95,1.25,z));
    fin(s.tag,t,a+d*.1,.5,20);fin(s.def,t,a+d*.32,.6,24);s.tl.forEach((e,i)=>fin(e,t,a+d*(.68+i*.1),.5,20));}
});
E.add({id:'tiger',a:C('c6_2')-.1,b:C('c6_3')-.05,chap:CH6,dark:true,
  build(r,s){h('div','bg dark',null,r);
    s.cv=magCover(r,560,300,430,560,'週刊','一九二五年 · 北京');s.cv.style.transform='rotate(3deg)';
    s.t1=h('div','abs',`<div class="sans" style="font-size:30px;letter-spacing:6px;color:#e0705f;font-weight:700">整顿学风 · 下手很硬</div>`,r,{left:'64px',top:'330px'});
    s.big=h('div','abs black trad','老虎<br>總長',r,{left:'64px',top:'900px',fontSize:'220px',lineHeight:'1.05',letterSpacing:'16px',color:'#e8ddc5'});
    s.n=h('div','abs sans','甲寅年是虎年。<br>他复刊的《甲寅》周刊封面印虎，<br>时人叫它“老虎报”。',r,{left:'64px',top:'420px',width:'470px',fontSize:'33px',lineHeight:'1.55',color:'#cdbf9f',fontWeight:'400'});
    s.cap=h('div','abs sans','封面为示意重排',r,{left:'560px',top:'880px',width:'430px',textAlign:'center',fontSize:'22px',color:'#8d806a'});
  },
  update(t,lt,s){const a=C('c6_2'),d=CE('c6_2')-a;s.t1.style.opacity=P(t,a,.5);fin(s.cv,t,a+d*.3,.6,30);s.cv.style.transform+=' rotate(3deg)';s.n.style.opacity=P(t,a+d*.4,.5);s.cap.style.opacity=P(t,a+d*.5,.5)*.8;
    const p=P(t,a+d*.72,.4,ease.back);A(s.big,{o:clamp(p*2),s:lerp(1.25,1,p)});s.big.style.transformOrigin='0 50%';}
});
E.add({id:'nsd',a:C('c6_3')-.1,b:C('c6_4')-.05,chap:CH6,
  build(r,s){h('div','bg light',null,r);
    s.hd=h('div','abs',`<div class="sans" style="font-size:30px;letter-spacing:6px;color:#6b6052;font-weight:500">一九二五年八月</div><div class="black" style="font-size:54px;line-height:1.3;margin-top:8px">教育部令：<span class="red">停办</span><br>国立北京女子师范大学</div>`,r,{left:'64px',top:'292px'});
    s.tag=personTag(r,'周树人','即鲁迅 · 教育部佥事 · 女师大兼课教员',64,560,'di');
    s.side=h('div','abs bold','站在学生一边',r,{left:'64px',top:'706px',fontSize:'46px',color:'#a5281d'});
    const ranks=[['總長','部长',0],['次長','副部长',0],['參事 · 司長','',0],['僉事','中级官员 ≈ 今天的处级',1],['主事','',0]];
    s.lad=ranks.map(([n,sub,hot],i)=>h('div','abs',`<span class="black trad" style="font-size:${hot?60:42}px;letter-spacing:6px;${hot?'color:#f0e5cc':''}">${n}</span><span class="sans" style="font-size:${hot?30:26}px;margin-left:18px;font-weight:500;${hot?'color:#f0e5cc':'color:#6b6052'}">${sub}</span>`,r,{left:(64+i*34)+'px',top:(800+i*86+(i>3?22:0))+'px',width:(952-i*34)+'px',height:hot?'104px':'76px',padding:hot?'10px 22px':'8px 22px',background:hot?'#a5281d':'#efe6cf',border:'3px solid '+(hot?'#a5281d':'#1b1814')}));
    s.def=h('div','abs sans','教育部官阶（示意）',r,{right:'64px',top:'760px',fontSize:'24px',color:'#6b6052',letterSpacing:'2px'});
  },
  update(t,lt,s){const a=C('c6_3'),d=CE('c6_3')-a;fin(s.hd,t,a,.6,24);fin(s.tag,t,a+d*.36,.5,20);fin(s.side,t,a+d*.56,.5,20);
    s.def.style.opacity=P(t,a+d*.66,.4);s.lad.forEach((e,i)=>{const p=P(t,a+d*.66+i*.12,.4);A(e,{o:p*(i===3?1:.9),x:(1-p)*-30});});
    const hp=P(t,a+d*.72,.4,ease.back);s.lad[3].style.transform=`scale(${lerp(.96,1,hp)})`;}
});
E.add({id:'cheng',a:C('c6_4')-.1,b:C('c6_7')-.05,chap:CH6,
  build(r,s){h('div','bg light',null,r);
    s.hd=h('div','abs sans','一九二五年八月十二日 · 教育总长呈临时执政',r,{left:'64px',top:'300px',fontSize:'29px',letterSpacing:'3px',color:'#6b6052',fontWeight:'500'});
    s.wrap=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px'});
    s.d=vDoc(s.wrap,170,350,740,600,[
      {i:0,t:'呈',fs:64,cls:'black',top:30},
      {i:1.05,t:'茲有本部僉事周樹人',fs:44,top:30},
      {i:2.25,t:'結合黨徒',fs:60,cls:'black',top:30},{i:3.35,t:'附和女生',fs:60,cls:'black',top:30},
      {i:4.45,t:'倡設校務維持會',fs:60,cls:'black',top:30,ls:'.06em'},{i:5.55,t:'充任委員',fs:60,cls:'black',top:30},
      {i:6.65,t:'應請明令免去本職',fs:44,top:30},{i:7.6,t:'十四年八月十二日',fs:28,top:300,cls:'semi'},
    ],{pitch:82,rot:.8});
    s.ok=seal(s.wrap,'照准',200,760,160,{fs:66,bw:9});
    s.okn=h('div','abs sans','← 第二天（8 月 13 日），执政府照准',s.wrap,{left:'400px',top:'964px',fontSize:'30px',lineHeight:'1.4',color:'#a5281d',fontWeight:'700'});
    s.plain=plainBox(r,'说他拉帮结派，附和女学生，带头成立维持会，<mark>还当了委员</mark>。',64,1050,960,44);
    s.src=srcTag(r,'转引','免职呈文，据《鲁迅生平史料汇编》所录鲁迅存抄件；画面为文字重排');
    // 讽刺：有容
    s.iron=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',background:'rgba(21,18,15,.93)'});
    h('div','black trad','「為政有本，<br>　在有容。」',s.iron,{position:'absolute',left:'64px',top:'420px',fontSize:'118px',lineHeight:'1.25',letterSpacing:'6px',color:'#d9b25c'});
    h('div','sans','—— 章士钊，1914',s.iron,{position:'absolute',left:'64px',top:'740px',fontSize:'32px',letterSpacing:'4px',color:'#a99c82'});
    s.i2=h('div','bold','十一年后，写下这句话的人掌了权，<br><span style="color:#e0705f">没容下一个处级下属。</span>',s.iron,{position:'absolute',left:'64px',top:'900px',fontSize:'52px',lineHeight:'1.5',color:'#e8ddc5'});
  },
  update(t,lt,s){const a=C('c6_4'),d=CE('c6_4')-a,p=C('c6_5'),pd=CE('c6_5')-p,z=C('c6_6');
    s.hd.style.opacity=P(t,a,.5);const di=P(t,a+.1,.6);s.d.doc.style.opacity=di;
    s.d.els.forEach((el,i)=>{const hot=i>=2&&i<=5;const t0=hot?a+d*(.42+(i-2)*.145):(i<2?a+.3+i*.2:a+d*.3);el.style.opacity=hot?lerp(.22,1,P(t,t0,.35)):P(t,t0,.5);});
    fin(s.plain,t,p-.1,.6,30);stamp(s.ok,t,p+pd*.74,-8);s.okn.style.opacity=P(t,p+pd*.8,.4);
    fin(s.src,t,a+1,.6,12);
    const ip=P(t,z-.25,.6,ease.io);s.iron.style.opacity=ip;s.iron.style.visibility=ip<=0?'hidden':'visible';fin(s.i2,t,z+(CE('c6_6')-z)*.38,.6,24);}
});
E.add({id:'sue',a:C('c6_7')-.1,b:C('c6_8')-.1,chap:CH6,dark:true,
  build(r,s){h('div','bg dark',null,r);
    s.hd=h('div','abs sans','一九二五年八月二十二日',r,{left:'64px',top:'300px',fontSize:'30px',letterSpacing:'8px',color:'#a99c82'});
    s.big=h('div','abs black trad','民告官',r,{left:'64px',top:'350px',fontSize:'210px',letterSpacing:'24px',color:'#e8ddc5'});
    const box=(y,lab,n,sub,red)=>h('div','abs',`<span class="sans" style="font-size:28px;letter-spacing:8px;color:${red?'#e0705f':'#a99c82'};font-weight:700">${lab}</span><span class="black trad" style="font-size:84px;letter-spacing:8px;color:#e8ddc5;margin-left:26px;vertical-align:-14px">${n}</span><span class="sans" style="font-size:30px;color:#cdbf9f;margin-left:22px">${sub}</span>`,r,{left:'64px',top:y+'px',width:'952px',borderLeft:`10px solid ${red?'#c23a2b':'#a99c82'}`,padding:'10px 0 18px 26px'});
    s.b1=box(700,'原告','周樹人','教育部佥事');s.b2=box(960,'被告','教育部','总长 章士钊',true);
    s.ar=h('div','abs black trad','訴 ↓',r,{left:'120px',top:'856px',fontSize:'60px',color:'#c23a2b',letterSpacing:'10px'});
    s.pz=h('div','abs sans','受理：平政院 —— 专审“民告官”的行政法院',r,{left:'64px',top:'1180px',fontSize:'33px',color:'#cdbf9f',letterSpacing:'1px'});
  },
  update(t,lt,s){const a=C('c6_7'),d=CE('c6_7')-a;s.hd.style.opacity=P(t,a,.5);const p=P(t,a+d*.25,.45,ease.back);A(s.big,{o:clamp(p*2),s:lerp(1.2,1,p)});s.big.style.transformOrigin='0 50%';
    fin(s.b1,t,a+d*.3,.5,24);s.ar.style.opacity=P(t,a+d*.45,.4);fin(s.b2,t,a+d*.5,.5,24);s.pz.style.opacity=P(t,a+d*.6,.5);}
});
// calendar 在 scenes_a.js
E.add({id:'ruling',a:C('c6_10')-.1,b:C('c6_11')-.05,chap:CH6,
  build(r,s){h('div','bg light',null,r);
    s.hd=h('div','abs sans','一九二六年三月 · 平政院裁决',r,{left:'64px',top:'300px',fontSize:'30px',letterSpacing:'6px',color:'#6b6052',fontWeight:'500'});
    s.q=h('div','abs black trad',null,r,{left:'64px',top:'350px',fontSize:'94px',letterSpacing:'6px',lineHeight:'1.2',whiteSpace:'nowrap'});
    s.qs=chars(s.q,'教育部之處分\n取消之');s.qs.forEach((x,i)=>{x.classList.add('inkf');if(i>=6)x.style.color='#a5281d';});
    s.sl=seal(r,'平政院印',770,360,210,{bw:10});
    const step=(x,y,tt,sub,st)=>h('div','abs',`<div class="black" style="font-size:38px;line-height:1.15">${tt}</div><div class="sans" style="font-size:23px;margin-top:6px;font-weight:500;opacity:.8">${sub}</div>`,r,{left:x+'px',top:y+'px',width:'270px',height:'136px',padding:'16px 12px',textAlign:'center',background:st==='x'?'transparent':'#efe6cf',border:st==='x'?'4px dashed #a5281d':'3px solid #1b1814',color:st==='x'?'#a5281d':'#1b1814'});
    s.l1=h('div','abs sans','法定程序',r,{left:'64px',top:'650px',fontSize:'28px',letterSpacing:'6px',color:'#2c4563',fontWeight:'700'});
    s.r1=[step(64,696,'呈请惩戒','总长提出'),step(405,696,'惩戒委员会','依法议决'),step(746,696,'免职','执政下令')];
    s.l2=h('div','abs sans','这一次',r,{left:'64px',top:'880px',fontSize:'28px',letterSpacing:'6px',color:'#a5281d',fontWeight:'700'});
    s.r2=[step(64,926,'呈请免职','8 月 12 日'),step(405,926,'没走','这一步被跳过','x'),step(746,926,'免职','8 月 13 日')];
    s.ar=[[340,764],[681,764],[340,994],[681,994]].map(([x,y])=>h('div','abs black','→',r,{left:x+'px',top:(y-30)+'px',width:'60px',textAlign:'center',fontSize:'46px'}));
    s.why=h('div','abs',`<div class="sans" style="font-size:26px;letter-spacing:6px;color:#a5281d;font-weight:700">裁决理由</div><div class="black trad inkf" style="font-size:44px;line-height:1.4;margin-top:6px">「被告遽行呈請免職，確與現行法令規定程序不符。」</div>`,r,{left:'64px',top:'1100px',width:'952px'});
    s.src=srcTag(r,'转引','平政院裁决书，据《平政院裁决录存》录文；裁决时章士钊已离任，周树人已复职');
  },
  update(t,lt,s){const a=C('c6_10'),d=CE('c6_10')-a;s.hd.style.opacity=P(t,a,.5);reveal(s.qs,t,a+d*.2,d*.14);stamp(s.sl,t,a+d*.36,6);
    s.l1.style.opacity=P(t,a+d*.46,.4);s.r1.forEach((e,i)=>fin(e,t,a+d*(.46+i*.07),.4,20));s.ar[0].style.opacity=P(t,a+d*.52,.3);s.ar[1].style.opacity=P(t,a+d*.6,.3);
    s.l2.style.opacity=P(t,a+d*.74,.4);fin(s.r2[0],t,a+d*.74,.4,20);fin(s.r2[2],t,a+d*.8,.4,20);s.ar[2].style.opacity=P(t,a+d*.78,.3);s.ar[3].style.opacity=P(t,a+d*.8,.3);
    const p=P(t,a+d*.9,.35,ease.back);A(s.r2[1],{o:clamp(p*2),s:lerp(1.4,1,p)});
    fin(s.why,t,a+d*.52,.6,20);fin(s.src,t,a+1,.6,12);}
});
E.add({id:'stat',a:C('c6_11')-.1,b:C('c6_12')-.05,chap:CH6,
  build(r,s){h('div','bg light',null,r);
    s.h1=h('div','abs bold','一个处级官员，<span class="red">把自己的部告赢了。</span>',r,{left:'64px',top:'296px',fontSize:'54px',lineHeight:'1.3',width:'952px'});
    s.n=h('div','abs',`<div class="black" style="font-size:330px;line-height:300px;letter-spacing:-8px">10<span style="font-size:90px;letter-spacing:4px;margin-left:16px">件</span></div><div class="sans" style="font-size:34px;line-height:1.45;color:#3a332b;font-weight:500;margin-top:14px">平政院存在的十几年里（1914–1928），<br>官员为自己的职位告官署、留下裁决的案子</div>`,r,{left:'64px',top:'470px'});
    s.bars=[['取消原处分',7,'#a5281d'],['变更原处分',3,'#a67c2e'],['维持原处分',0,'#6b6052']].map(([n,v,c],i)=>{const e=h('div','abs',`<div class="sans" style="font-size:32px;font-weight:700;color:#1b1814;width:230px;display:inline-block">${n}</div><div style="display:inline-block;vertical-align:middle;height:46px;background:${c};width:0" class="bar"></div><span class="black" style="font-size:52px;margin-left:16px;color:${c};vertical-align:middle">${v}</span>`,r,{left:'64px',top:(1040+i*80)+'px',width:'952px',whiteSpace:'nowrap'});e.v=v;return e;});
    s.src=srcTag(r,'学术','聂鑫，《华东政法大学学报》2017年第2期，据《平政院裁决录存》统计');
  },
  update(t,lt,s){const a=C('c6_11'),d=CE('c6_11')-a;fin(s.h1,t,a,.5,24);fin(s.n,t,a+d*.42,.6,30);
    s.bars.forEach((e,i)=>{const p=P(t,a+d*.7+i*.2,.6);e.style.opacity=clamp(p*2);e.querySelector('.bar').style.width=(e.v*74*p)+'px';});fin(s.src,t,a+1,.6,12);}
});
E.add({id:'cat',a:C('c6_12')-.1,b:C('c7_1')-.15,chap:CH6,dark:true,
  build(r,s){h('div','bg dark',null,r);
    s.y1=h('div','abs',`<div class="black" style="font-size:120px;color:#e8ddc5;line-height:1">1912</div><div class="sans" style="font-size:30px;color:#a99c82;letter-spacing:3px;margin-top:8px">章士钊 · 署名“行严” ·《民立报》《独立周报》</div>`,r,{left:'64px',top:'292px'});
    s.tt=['論特設平政院與自由原理之不相容','論行政裁判所之不當設'].map((x,i)=>h('div','abs black trad inkf','《'+x+'》',r,{left:'40px',top:(500+i*80)+'px',fontSize:i?'50px':'50px',color:'#e8ddc5',letterSpacing:'1px',whiteSpace:'nowrap',transform:i?'':'scaleX(.93)',transformOrigin:'0 50%'}));
    s.more=h('div','abs sans','…… 前后八篇',r,{left:'64px',top:'664px',fontSize:'30px',color:'#a99c82',letterSpacing:'4px'});
    s.q=h('div','abs black trad','「貓口之鼠」',r,{left:'36px',top:'730px',fontSize:'150px',letterSpacing:'6px',color:'#d9b25c',whiteSpace:'nowrap'});
    s.g=h('div','abs sans','他的理由：让行政自己设法院审自己，<br>百姓的自由，就成了猫嘴里的老鼠。',r,{left:'64px',top:'940px',fontSize:'36px',lineHeight:'1.5',color:'#cdbf9f'});
    s.y2=h('div','abs',`<div class="black" style="font-size:120px;color:#e8ddc5;line-height:1">1926</div>`,r,{left:'64px',top:'1090px'});
    s.v=h('div','abs bold','正是这所法院，<span style="color:#e0705f">判定官府败诉。</span>',r,{left:'380px',top:'1128px',fontSize:'44px',color:'#e8ddc5',lineHeight:'1.3',width:'680px',whiteSpace:'nowrap'});
    s.src=srcTag(r,'转引','《临时约法与人民自由权》等，1912年；据王贵松《清华法学》2015年第2期。<em>只查到1911–1917年的反对文字</em>',true);
  },
  update(t,lt,s){const a=C('c6_12'),d=CE('c6_12')-a,b=C('c6_13');fin(s.y1,t,a+d*.14,.5,24);s.tt.forEach((e,i)=>{const p=P(t,a+d*.3+i*.35,.5);e.style.opacity=p;});s.more.style.opacity=P(t,a+d*.45,.4);
    const q=P(t,a+d*.82,.4,ease.back);A(s.q,{o:clamp(q*2),s:lerp(1.15,1,q)});s.q.style.transformOrigin='0 50%';s.g.style.opacity=P(t,a+d*.62,.5);
    fin(s.y2,t,b-.1,.5,24);fin(s.v,t,b+.5,.6,24);fin(s.src,t,a+1,.6,12);}
});

// ── 收尾 ─────────────────────────────────────────────────
E.add({id:'end1',a:C('c7_1')-.15,b:C('c7_2')-.1,chap:'',
  build(r,s){h('div','bg light',null,r);
    s.st=h('div','take','他靠人情，<br>在每个阵营<span class="red">都有座位。</span>',r,{left:'64px',top:'292px',fontSize:'60px',width:'960px',lineHeight:'1.25'});
    s.wrap=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',transformOrigin:'540px 1300px',transform:'scale(.88)'});s.web=Web(s.wrap,{legendY:1318});},
  update(t,lt,s){const a=s.a;fin(s.st,t,a+.1,.6,24);const tm={};['zsz','ymz','zty','wzh','szs','wrn','wcq','hx','ysk','lx'].forEach(k=>tm[k]=a-9);tm.dqr=a+.3;s.web.update(t,tm,{'zsz-lx':'免职→败诉'});s.web.lg.style.opacity=1;}
});
E.add({id:'end2',a:C('c7_2')-.1,b:C('c7_3')-.1,chap:'',dark:true,
  build(r,s){h('div','bg dark',null,r);s.q=vQuote(r,['為政有本','在有容'],760,400,170,{pitch:280,offs:[0,120],color:'#d9b25c'});
    s.n=h('div','abs sans','—— 他写下的',r,{left:'64px',top:'1220px',fontSize:'34px',letterSpacing:'8px',color:'#a99c82'});},
  update(t,lt,s){reveal(s.q.spans,t,s.a+.3,1.6);s.n.style.opacity=P(t,s.a+.2,.5);}
});
E.add({id:'end3',a:C('c7_3')-.1,b:C('c7_4')-.2,chap:'',dark:true,
  build(r,s){h('div','bg dark',null,r);
    s.d=vDoc(r,210,330,660,560,[{i:0,t:'呈',fs:60,cls:'black',top:30},{i:1.1,t:'本部僉事周樹人',fs:44,top:30},{i:2.3,t:'應請明令免去本職',fs:44,top:30},{i:3.5,t:'十四年八月十二日',fs:30,top:30,cls:'semi'},{i:4.6,t:'照准　八月十三日',fs:40,top:30,cls:'black',color:'#a5281d'}],{pitch:84,rot:-2});
    s.x=h('div','abs black trad','取消',r,{left:'330px',top:'560px',fontSize:'190px',letterSpacing:'16px',color:'#c23a2b',border:'14px solid #c23a2b',padding:'0 24px 20px 40px',lineHeight:'1.1',webkitMaskImage:'url(../assets/seal_mask.png)',webkitMaskSize:'420px 420px'});
    s.t=h('div','abs bold','最后替他上了这一课的，<br>是一张<span style="color:#e0705f">程序写错了的免职令。</span>',r,{left:'64px',top:'1000px',fontSize:'56px',lineHeight:'1.4',color:'#e8ddc5'});},
  update(t,lt,s){const a=s.a;s.d.doc.style.opacity=P(t,a,.6);const [sx,sy]=shake(t,a+1.5,10);s.d.doc.style.transform=`translate(${sx}px,${sy}px) rotate(-2deg)`;stamp(s.x,t,a+1.3,-10);fin(s.t,t,a+.3,.6,24);}
});
E.add({id:'coda',a:C('c7_4')-.2,b:TIM._end[1]+.1,chap:'',dark:true,nohud:false,fi:.8,
  build(r,s){h('div','bg dark',null,r);
    s.c=h('div','abs bold','此后几十年，时局几度翻覆，<br>他依然在每一张桌边<br><span style="color:#d9b25c">都有座位。</span>',r,{left:'64px',top:'440px',fontSize:'62px',lineHeight:'1.5',color:'#e8ddc5'});
    s.c2=h('div','abs sans','那是另一个故事了。',r,{left:'64px',top:'790px',fontSize:'40px',letterSpacing:'6px',color:'#a99c82'});
    s.end=h('div','abs',`<div class="black trad" style="font-size:120px;letter-spacing:16px;color:#e8ddc5;line-height:1.1">章士釗</div><div class="bold trad" style="font-size:42px;letter-spacing:4px;margin-top:14px;color:#d9b25c">一個在每個陣營都有座位的人</div>
      <div style="width:120px;height:3px;background:#a67c2e;margin:44px 0 30px"></div>
      <div class="sans" style="font-size:25px;line-height:1.7;color:#a99c82;letter-spacing:1px">主要出处：《申报》1903年7月 ·《甲寅》1914年 · 鲁迅《华盖集》《华盖集续编》<br>平政院裁决书 · 冯自由《革命逸史》·《章士钊全集》（回忆文字据后人引文）<br>配音：开源语音合成 · 音乐与画面：自制 · 地图轮廓：Natural Earth</div>`,r,{left:'64px',top:'420px',width:'952px'});
  },
  update(t,lt,s){const a=C('c7_4'),e=CE('c7_4');finout(s.c,t,a-.1,e+1.0,.7,24);const p=P(t,a+(e-a)*.72,.6);s.c2.style.opacity=p*(1-P(t,e+.6,.4));fin(s.end,t,e+1.2,.8,24);}
});
