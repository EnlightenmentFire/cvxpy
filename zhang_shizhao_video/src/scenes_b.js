// 场景（二）：通用场景生成器 + 冷启动后半 + 第一至三章
// ── 通用：引文场景（竖排原文 + 白话 + 出处）────────────
function quoteScene(o){
  E.add({id:o.id,a:o.a,b:o.b,chap:o.chap,dark:!!o.dark,
    build(r,s){
      h('div','bg '+(o.dark?'dark':(o.bg||'light')),null,r);
      if(o.tag)s.tag=personTag(r,o.tag[0],o.tag[1],64,300,o.tag[2],false);
      if(o.who)s.who=h('div','abs sans',o.who,r,{right:'64px',top:(o.whoY||318)+'px',fontSize:'30px',letterSpacing:'6px',color:o.dark?'#a99c82':'#6b6052',fontWeight:'500',textAlign:'right',lineHeight:'1.5'});
      s.q=vQuote(r,o.cols,o.x||1000,o.y||492,o.fs||84,{pitch:o.pitch,offs:o.offs,dots:o.dots,color:o.dark?'#e8ddc5':''});
      s.q.spans.forEach(x=>x.classList.add('inkf'));
      s.gl=(o.gloss||[]).map(g=>h('div','abs sans',g[0],r,{left:g[1]+'px',top:g[2]+'px',fontSize:'30px',color:o.dark?'#e0705f':'#a5281d',fontWeight:'700',letterSpacing:'4px',writingMode:'vertical-rl',borderRight:'3px solid '+(o.dark?'#e0705f':'#a5281d'),paddingRight:'12px'}));
      if(o.plain){s.plain=plainBox(r,o.plain.html,64,o.plain.y||1060,960,o.plain.fs||47,o.plain.lab);if(o.dark)s.plain.style.color='#e8ddc5';}
      if(o.plain2){s.plain2=plainBox(r,o.plain2.html,64,o.plain2.y,960,o.plain2.fs||47,o.plain2.lab);if(o.dark)s.plain2.style.color='#e8ddc5';}
      if(o.src)s.src=srcTag(r,o.src[0],o.src[1],!!o.dark);
      if(o.build)o.build(r,s);
    },
    update(t,lt,s){
      const qa=o.qa,qd=o.qd;
      if(s.tag)fin(s.tag,t,s.a,.5,20);
      if(s.who)s.who.style.opacity=P(t,s.a+.2,.5);
      reveal(s.q.spans,t,qa,qd);
      s.gl.forEach((g,i)=>g.style.opacity=P(t,qa+qd*.6+i*.3,.5));
      if(s.plain){if(o.plain.out)finout(s.plain,t,o.plain.at,o.plain.out,.6,30);else fin(s.plain,t,o.plain.at,.6,30);}
      if(s.plain2)fin(s.plain2,t,o.plain2.at,.6,30);
      if(s.src)fin(s.src,t,s.a+.9,.6,12);
      if(o.update)o.update(t,lt,s);
    }});
}
// ── 通用：“这说明什么”+ 关系网 ──────────────────────────
function takeWebScene(o){
  E.add({id:o.id,a:o.a,b:o.b,chap:o.chap,
    build(r,s){h('div','bg light',null,r);
      s.lab=h('div','abs sans','这说明什么',r,{left:'64px',top:'292px',fontSize:'26px',fontWeight:'700',letterSpacing:'6px',color:'#e8ddc5',background:'#a5281d',padding:'3px 12px 4px 16px'});
      s.st=h('div','take',o.html,r,{left:'64px',top:'342px',fontSize:(o.fs||50)+'px',width:'960px'});
      s.wrap=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',transformOrigin:'540px 1300px',transform:'scale(.9)'});
      s.web=Web(s.wrap,{legendY:1318});
    },
    update(t,lt,s){const a=s.a;A(s.lab,{o:P(t,a,.4)});fin(s.st,t,o.at||a+.4,.6,24);
      const times={};for(const k of o.old)times[k]=a-9;o.add.forEach((k,i)=>times[k]=a+.5+i*.55);
      s.web.update(t,times,o.labels);s.web.lg.style.opacity=P(t,a+.2,.6);}
  });
}
function defBox(root,term,desc,x,y,color){
  return h('div','abs',`<span class="sans" style="font-size:26px;font-weight:700;letter-spacing:6px;color:#e8ddc5;background:${color||'#2c4563'};padding:3px 12px 4px 16px">名词</span>
   <div class="black" style="font-size:60px;margin-top:12px;letter-spacing:6px">${term}</div>
   <div class="sans" style="font-size:35px;line-height:1.5;margin-top:4px;font-weight:500;opacity:.86">${desc}</div>`,root,{left:x+'px',top:y+'px',width:'952px'});
}
function bigLine(root,html,y,fs,opt={}){return h('div','abs black'+(opt.trad?' trad':''),html,root,Object.assign({left:'64px',top:y+'px',width:'952px',fontSize:fs+'px',lineHeight:'1.3',letterSpacing:'3px'},opt.style||{}));}
// 重排文书（竖排、朱丝栏）
function vDoc(root,x,y,w,hh,cols,opt={}){
  const doc=h('div','abs',null,root,{left:x+'px',top:y+'px',width:w+'px',height:hh+'px',backgroundImage:'url(../assets/paper_old.jpg)',backgroundSize:'1080px 1920px',backgroundPosition:`${-x}px ${-y}px`,boxShadow:'0 16px 40px rgba(27,24,20,.4), 0 0 0 1px rgba(27,24,20,.35)',transform:`rotate(${opt.rot||0}deg)`});
  const PT=opt.pitch||74,GX=opt.gx||26,GY=opt.gy||26;
  if(!opt.nogrid){const g=h('div','abs cols',null,doc,{left:GX+'px',top:GY+'px',width:(w-2*GX)+'px',height:(hh-2*GY)+'px',border:'3px solid rgba(165,40,29,.6)'});g.style.setProperty('--pitch',PT+'px');}
  const els=cols.map(c=>{const fs=c.fs||40;const e=h('div','abs v trad '+(c.cls||'bold'),c.t,doc,{right:(GX+c.i*PT+(PT-fs)/2)+'px',top:(GY+(c.top||30))+'px',fontSize:fs+'px',lineHeight:'1',letterSpacing:c.ls||'.14em',color:c.color||'#1b1814',whiteSpace:'nowrap'});e.classList.add('inkf');return e;});
  return {doc,els,PT,GX,GY};
}

// ── 冷启动 2：平政院是什么、原告与被告 ──────────────────
E.add({id:'pzy',a:C('c0_3')-.05,b:C('c0_4')-.05,dark:true,chap:'1926 · 北京',
  build(r,s){h('div','bg dark',null,r);
    s.def=defBox(r,'平政院','北洋时期专审“民告官”的行政法院，<br>1914 年设立。',64,292,'#a5281d');s.def.style.color='#e8ddc5';
    const card=(x,lab,name,sub,red)=>h('div','abs',`<div class="sans" style="font-size:28px;letter-spacing:10px;font-weight:700;color:${red?'#a5281d':'#6b6052'}">${lab}</div><div class="black trad" style="font-size:${name.length>3?76:86}px;letter-spacing:6px;margin-top:10px;line-height:1.1">${name}</div><div class="sans" style="font-size:30px;margin-top:14px;color:#3a332b;font-weight:500;line-height:1.4">${sub}</div>`,r,{left:x+'px',top:'640px',width:'440px',height:'330px',padding:'28px 30px',backgroundImage:'url(../assets/paper_old.jpg)',backgroundSize:'1080px 1920px',backgroundPosition:`-${x}px -640px`,boxShadow:'0 14px 40px rgba(0,0,0,.6)'});
    s.c1=card(64,'原告','周樹人','教育部佥事<br>部里的中级官员');s.c2=card(576,'被告','教育部','免去他的职务',true);
    s.vs=h('div','abs black trad','訴',r,{left:'490px',top:'760px',width:'100px',height:'100px',borderRadius:'50%',background:'#a5281d',color:'#e8ddc5',fontSize:'58px',textAlign:'center',lineHeight:'96px',boxShadow:'0 0 0 6px #15120f'});
    s.arrow=h('div','abs sans','处分出自 ↓',r,{left:'576px',top:'1000px',width:'440px',textAlign:'center',fontSize:'30px',letterSpacing:'6px',color:'#e0705f',fontWeight:'700'});
    s.tag=h('div','abs',`<div class="black trad" style="font-size:112px;letter-spacing:14px;color:#e8ddc5;line-height:1.1">章士釗</div><div class="sans" style="font-size:32px;letter-spacing:6px;color:#cdbf9f;margin-top:8px">前任教育总长 · 1881 年生于湖南</div>`,r,{left:'64px',top:'1060px',width:'952px',textAlign:'right'});
  },
  update(t,lt,s){const a=C('c0_3'),d=CE('c0_3')-a;
    fin(s.def,t,a,.6,24);fin(s.c1,t,a+d*.42,.6,40);fin(s.c2,t,a+d*.62,.6,40);
    const v=P(t,a+d*.55,.4,ease.back);A(s.vs,{o:clamp(v*2),s:lerp(.4,1,v)});
    s.arrow.style.opacity=P(t,a+d*.72,.4);fin(s.tag,t,a+d*.8,.7,30);}
});
// ── 冷启动 3：三个阵营，三把椅子 ────────────────────────
function chairSVG(parent,x,y,sc){const g=svg('g',{transform:`translate(${x},${y}) scale(${sc})`,fill:'none',stroke:'#1b1814','stroke-width':7,'stroke-linecap':'round','stroke-linejoin':'round'},parent);
  svg('path',{d:'M-70,-210 Q0,-232 70,-210'},g);svg('path',{d:'M-56,-212 L-56,0 M56,-212 L56,0'},g);svg('rect',{x:-18,y:-208,width:36,height:120},g);
  svg('path',{d:'M-78,-88 L78,-88 L78,-66 L-78,-66 Z',fill:'#1b1814'},g);svg('path',{d:'M-70,-66 L-70,90 M70,-66 L70,90 M-70,40 L70,40'},g);
  svg('path',{d:'M-78,-88 L-96,-150 L-56,-150 M78,-88 L96,-150 L56,-150'},g);return g;}
E.add({id:'seats',a:C('c0_4')-.05,b:C('c1_1')-2.3,chap:'',
  build(r,s){h('div','bg light',null,r);
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    s.cols=[['革命黨','1903 —',190],['袁世凱','1912 —',540],['段祺瑞','1924 —',890]].map(([n,y,x],i)=>{
      const g=h('div','abs',null,r,{left:(x-120)+'px',top:'300px',width:'240px',textAlign:'center'});
      h('div','black trad v',n,g,{fontSize:'84px',letterSpacing:'10px',margin:'0 auto',lineHeight:'1',height:'300px'});
      h('div','sans',y,g,{fontSize:'28px',letterSpacing:'4px',color:'#6b6052',marginTop:'14px',fontWeight:'500'});
      const ch=chairSVG(sv,x,870,.92);const sl=seal(r,'章',x-34,744,68,{fill:true,fs:46});
      return {g,ch,sl};});
    s.q=h('div','abs',`<div class="black trad" style="font-size:136px;letter-spacing:18px;line-height:1.1">章士釗</div><div class="bold trad" style="font-size:47px;letter-spacing:5px;margin-top:14px;color:#a5281d">一個在每個陣營都有座位的人</div>`,r,{left:'0',top:'1030px',width:'1080px',textAlign:'center'});
  },
  update(t,lt,s){const a=C('c0_4'),d=CE('c0_4')-a;
    s.cols.forEach((c,i)=>{const t0=a+.15+i*(d*.12);fin(c.g,t,t0,.5,30);c.ch.style.opacity=P(t,t0+.2,.5);stamp(c.sl,t,a+d*.42+i*.18,(i-1)*5);});
    fin(s.q,t,a+d*.55,.8,30);}
});

// ── 第一章 ───────────────────────────────────────────────
const CH1='壹 · 一张人情网';
E.add({id:'subao',nokb:true,a:C('c1_1')-.1,b:C('c1_2')-.05,chap:CH1,
  build(r,s){h('div','bg old',null,r);
    s.cam=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',transformOrigin:'540px 700px'});
    const pg=s.pg=h('div','abs',null,s.cam,{left:'90px',top:'300px',width:'900px',height:'640px',background:'#e9dfc8',boxShadow:'0 14px 36px rgba(27,24,20,.35)',border:'2px solid #1b1814',overflow:'hidden'});
    // 报头
    h('div','abs',`<div class="v black trad inkf" style="font-size:168px;letter-spacing:8px;line-height:1">蘇報</div>`,pg,{right:'22px',top:'22px',border:'6px double #1b1814',padding:'18px 10px 22px'});
    h('div','abs v sans','上海 · 光緒二十九年',pg,{right:'262px',top:'30px',fontSize:'25px',letterSpacing:'8px',color:'#3a332b'});
    // 栏目（标题为 1903 年 6 月所刊篇目；正文以线条示意）
    s.heads=['讀革命軍','序革命軍','殺人主義','康有為與覺羅君之關係'].map((tt,i)=>{const x=440-i*134;
      const c=h('div','abs',null,pg,{left:x+'px',top:'30px',width:'120px',height:'580px',borderLeft:'2px solid rgba(27,24,20,.6)'});
      h('div','v black trad inkf',tt,c,{position:'absolute',right:'10px',top:'0',fontSize:tt.length>5?'40px':'54px',letterSpacing:'4px',lineHeight:'1'});
      for(let k=0;k<2;k++)h('div',null,null,c,{position:'absolute',left:(14+k*26)+'px',top:'8px',width:'10px',height:(430+((i*37+k*91)%140))+'px',background:'repeating-linear-gradient(to bottom,rgba(27,24,20,.5) 0,rgba(27,24,20,.5) 14px,transparent 14px,transparent 19px)'});
      return c;});
    s.cap=h('div','abs sans','篇目为 1903 年 6 月《苏报》所刊；版面为示意重排',r,{left:'90px',top:'952px',fontSize:'24px',letterSpacing:'2px',color:'#6b6052'});
    s.tag=personTag(r,'章士钊','22 岁 ·《苏报》主笔',64,1010,'di');
    s.def=h('div','abs',`<span class="sans" style="font-size:26px;font-weight:700;letter-spacing:6px;color:#e8ddc5;background:#2c4563;padding:3px 12px 4px 16px">名词</span><span class="black" style="font-size:50px;letter-spacing:6px;margin-left:18px;vertical-align:-8px">主笔</span><div class="sans" style="font-size:35px;line-height:1.45;margin-top:10px;font-weight:500;color:#3a332b">报纸的主要写手，也是言论负责人。</div>`,r,{left:'64px',top:'1150px',width:'952px'});
  },
  update(t,lt,s){const a=C('c1_1'),d=CE('c1_1')-a;const z=P(t,a,d+1,ease.io2);
    s.cam.style.transform=`scale(${lerp(1.04,1,z)})`;
    s.heads.forEach((c,i)=>{c.style.opacity=P(t,a+d*.62+i*.28,.4);});
    fin(s.tag,t,a+d*.2,.5,24);fin(s.def,t,a+d*.38,.6,24);s.cap.style.opacity=P(t,a+d*.7,.5);}
});
E.add({id:'list',a:C('c1_2')-.1,b:C('c1_3')-.05,chap:CH1,
  build(r,s){h('div','bg light',null,r);
    s.hd=h('div','abs',`<div class="sans" style="font-size:30px;letter-spacing:5px;color:#6b6052;font-weight:500">《申报》1903 年 7 月 2 日</div><div class="black trad inkf" style="font-size:92px;letter-spacing:14px;margin-top:6px">會黨成禽</div><div class="sans" style="font-size:30px;letter-spacing:3px;color:#3a332b;margin-top:2px;font-weight:500">奉命拿办的，一共六人：</div>`,r,{left:'64px',top:'292px'});
    s.feng=h('div','abs black trad','封',r,{right:'70px',top:'300px',width:'150px',height:'150px',border:'10px solid #a5281d',color:'#a5281d',fontSize:'104px',textAlign:'center',lineHeight:'126px',borderRadius:'50%',transform:'rotate(8deg)'});
    s.fengc=h('div','abs sans','苏报馆 · 7 月初查封',r,{right:'40px',top:'470px',width:'210px',textAlign:'center',fontSize:'24px',letterSpacing:'2px',color:'#a5281d',fontWeight:'700'});
    const names=[['陳範','馆主','出逃'],['錢允生','','到案'],['章炳麟','即章太炎','入狱三年'],['龍積之','','到案'],['陳吉甫','账房','被捕'],['鄒容','《革命军》作者','死于狱中']];
    s.slips=names.map(([n,who,fate],i)=>{const x=64+i*138;
      const e=h('div','abs',null,r,{left:x+'px',top:'600px',width:'122px',height:'560px',background:'#efe6cf',border:'3px solid #1b1814',boxShadow:'5px 6px 0 rgba(27,24,20,.18)'});
      h('div','v black trad inkf',n,e,{position:'absolute',left:'50%',top:'22px',transform:'translateX(-50%)',fontSize:'64px',letterSpacing:'10px',lineHeight:'1',whiteSpace:'nowrap'});
      h('div','sans',(who?who+'<br>':'')+`<b style="color:#a5281d">${fate}</b>`,e,{position:'absolute',left:'0',bottom:'14px',width:'100%',textAlign:'center',fontSize:who.length>4?'19px':'23px',lineHeight:'1.4',color:'#3a332b',fontWeight:'500'});
      return e;});
    s.hl=[2,5,4];
    s.miss=h('div','abs',null,r,{left:'892px',top:'600px',width:'124px',height:'560px',border:'4px dashed #a5281d'});
    h('div','v black trad','章士釗',s.miss,{position:'absolute',left:'50%',top:'22px',transform:'translateX(-50%)',fontSize:'64px',letterSpacing:'10px',lineHeight:'1',whiteSpace:'nowrap',color:'#a5281d'});
    h('div','sans','主笔',s.miss,{position:'absolute',left:0,bottom:'14px',width:'100%',textAlign:'center',fontSize:'23px',color:'#a5281d',fontWeight:'700'});
    s.no=h('div','abs black','不在名单',r,{left:'560px',top:'1182px',width:'456px',textAlign:'right',fontSize:'66px',letterSpacing:'6px',color:'#a5281d'});
    s.src=srcTag(r,'原文','《申报》1903年7月2日〈会党成禽〉；报上“周容”即邹容');
  },
  update(t,lt,s){const a=C('c1_2'),d=CE('c1_2')-a;
    fin(s.hd,t,a+d*.12,.5,24);stamp(s.feng,t,a+.25,8);s.fengc.style.opacity=P(t,a+.6,.4);
    s.slips.forEach((e,i)=>{const p=P(t,a+d*.2+i*.16,.45);A(e,{o:p,y:(1-p)*40});});
    // 念到章太炎、邹容、账房时依次加红框
    [[2,.42],[5,.5],[4,.66]].forEach(([i,f])=>{const p=P(t,a+d*f,.3);s.slips[i].style.boxShadow=`0 0 0 ${p*6}px rgba(165,40,29,${p*.85}),5px 6px 0 rgba(27,24,20,.18)`;});
    const m=P(t,a+d*.84,.45,ease.back);A(s.miss,{o:clamp(m*2),s:lerp(1.2,1,m)});
    const n=P(t,a+d*.93,.35,ease.back);A(s.no,{o:clamp(n*2),s:lerp(1.3,1,n)});
    fin(s.src,t,a+1,.6,12);}
});
E.add({id:'ymz',a:C('c1_3')-.1,b:C('c1_4')-.1,chap:CH1,
  build(r,s){h('div','bg light',null,r);
    s.nm=h('div','abs',`<div class="black trad" style="font-size:150px;letter-spacing:20px;line-height:1.1;text-indent:20px">俞明震</div>`,r,{left:0,top:'320px',width:'1080px',textAlign:'center'});
    const card=(x,lab,tt,sub,col)=>h('div','abs',`<div class="sans" style="font-size:26px;letter-spacing:6px;font-weight:700;color:#e8ddc5;background:${col};display:inline-block;padding:3px 12px 4px 16px">${lab}</div><div class="black" style="font-size:66px;letter-spacing:6px;margin-top:14px">${tt}</div><div class="sans" style="font-size:31px;line-height:1.45;margin-top:10px;color:#3a332b;font-weight:500">${sub}</div>`,r,{left:x+'px',top:'620px',width:'460px',height:'330px',padding:'26px 28px',background:'#efe6cf',border:'3px solid #1b1814',boxShadow:'7px 8px 0 rgba(27,24,20,.18)'});
    s.c1=card(64,'这一面','查办官','江苏候补道，奉命到上海查办苏报案','#1b1814');s.c2=card(556,'另一面','校长','南京江南陆师学堂总办，章士钊的老师','#a67c2e');
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    s.l1=svg('path',{d:'M540,520 L294,620',stroke:'#1b1814','stroke-width':5,fill:'none'},sv);s.l2=svg('path',{d:'M540,520 L786,620',stroke:'#a67c2e','stroke-width':5,fill:'none'},sv);
    s.l3=svg('path',{d:'M786,950 L786,1060',stroke:'#a67c2e','stroke-width':6,fill:'none'},sv);
    s.stu=h('div','abs',`<div style="display:inline-block;background:#a5281d;color:#f0e5cc;padding:8px 26px 12px;font-family:var(--serift);font-weight:900;font-size:66px;letter-spacing:8px">章士釗</div><div class="sans" style="font-size:31px;margin-top:12px;color:#3a332b;font-weight:500;letter-spacing:2px">陆师学堂学生 · 最受他赏识</div>`,r,{left:'486px',top:'1060px',width:'600px',textAlign:'center'});
  },
  update(t,lt,s){const a=C('c1_3'),d=CE('c1_3')-a;fin(s.nm,t,a+d*.12,.6,30);
    [s.l1,s.l2].forEach((l,i)=>l.style.opacity=P(t,a+d*(.25+i*.2),.4));fin(s.c1,t,a+d*.25,.5,30);fin(s.c2,t,a+d*.45,.5,30);
    s.l3.style.opacity=P(t,a+d*.7,.4);fin(s.stu,t,a+d*.72,.5,24);}
});
// q_yangnu 在 scenes_a.js

// 吃面
function noodleSVG(parent,x,y,sc){const g=svg('g',{transform:`translate(${x},${y}) scale(${sc})`,fill:'none',stroke:'#1b1814','stroke-width':7,'stroke-linecap':'round','stroke-linejoin':'round'},parent);
  svg('path',{d:'M-190,0 Q-170,150 -70,170 L70,170 Q170,150 190,0 Z',fill:'#efe6cf'},g);svg('path',{d:'M-80,170 L-64,198 L64,198 L80,170'},g);
  svg('ellipse',{cx:0,cy:0,rx:190,ry:36,fill:'#e2d6b8'},g);
  for(let i=0;i<5;i++)svg('path',{d:`M${-140+i*26},${-4+i%2*6} Q${-60+i*20},${-34-i*3} ${20+i*18},${-6} T${150-i*8},${2+i%2*5}`,'stroke-width':5},g);
  svg('path',{d:'M60,-20 L250,-150 M84,-6 L276,-128','stroke-width':8},g);
  const st=[-90,-10,70].map((dx,i)=>svg('path',{d:`M${dx},-60 q-26,-40 0,-80 q26,-40 0,-80 q-22,-36 0,-66`,'stroke-width':5,stroke:'#6b6052'},g));
  return {g,st};}
E.add({id:'noodle',a:C('c1_6')-.1,b:C('c1_8')-.05,chap:CH1,
  build(r,s){h('div','bg light',null,r);
    s.tag=personTag(r,'吴稚晖','爱国学社教员 · 密令点名要抓的人',64,300,'zhi');
    s.who=h('div','abs sans','吴稚晖回忆',r,{right:'64px',top:'318px',fontSize:'30px',letterSpacing:'6px',color:'#6b6052',fontWeight:'500'});
    s.d=vDoc(r,250,480,580,640,[
      {i:0,t:'兩江總督部堂 札',fs:34,cls:'black',color:'#a5281d',top:26,ls:'.2em'},
      {i:1.1,t:'照得逆犯蔡元培吳敬恆',fs:44,top:26},{i:2.2,t:'倡言革命煽亂謀逆',fs:44,top:26},
      {i:3.3,t:'著俞道會同上海道',fs:44,top:26},{i:4.5,t:'密拿',fs:84,cls:'black',top:26,ls:'.2em'},
      {i:5.4,t:'即行審實',fs:44,top:26},{i:6.25,t:'正法',fs:84,cls:'black',top:250,ls:'.2em'},
    ],{pitch:74,rot:-1.5});
    s.g1=h('div','abs sans','秘密逮捕',r,{left:'120px',top:'560px',fontSize:'34px',fontWeight:'700',color:'#a5281d',letterSpacing:'4px',writingMode:'vertical-rl'});
    s.g2=h('div','abs sans','处决',r,{left:'120px',top:'800px',fontSize:'34px',fontWeight:'700',color:'#a5281d',letterSpacing:'4px',writingMode:'vertical-rl'});
    s.g3=h('div','abs sans','吴敬恒＝吴稚晖',r,{right:'96px',top:'520px',fontSize:'30px',fontWeight:'700',color:'#a5281d',letterSpacing:'4px',writingMode:'vertical-rl'});
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);s.bowl=noodleSVG(sv,320,790,.9);
    s.q=h('div','abs black trad inkf','「笑話笑話，<br>　我們吃麵。」',r,{left:'64px',top:'1010px',fontSize:'92px',lineHeight:'1.2',letterSpacing:'4px'});
    s.n1=h('div','abs sans','<b style="color:#a5281d">每盆先吃一筷</b><br>——表示没下毒',r,{left:'650px',top:'600px',fontSize:'33px',lineHeight:'1.45',fontWeight:'500',color:'#3a332b',width:'380px'});
    s.n2=h('div','abs sans','最后劝他：<br><b style="color:#a5281d">最好到外国去留学</b>',r,{left:'650px',top:'780px',fontSize:'33px',lineHeight:'1.45',fontWeight:'500',color:'#3a332b',width:'380px'});
    s.src=srcTag(r,'回忆','吴稚晖 1943 年记述，见冯自由《革命逸史》；<em>当事人一方的说法</em>');
  },
  update(t,lt,s){const a=C('c1_6'),d=CE('c1_6')-a,b=C('c1_7'),e=CE('c1_7')-b;
    fin(s.tag,t,a,.5,20);s.who.style.opacity=P(t,a+.2,.5);
    // 公文入场，后被收走
    const pin=P(t,a+d*.3,.6),pout=P(t,b+.1,.6,ease.in2);
    s.d.doc.style.opacity=pin*(1-pout);s.d.doc.style.transform=`translate(${pout*-420}px,${(1-pin)*50+pout*260}px) rotate(${-1.5-pout*22}deg) scale(${1-pout*.3})`;
    s.d.els.forEach((el,i)=>el.style.opacity=P(t,a+d*.36+i*.14,.4));
    s.g1.style.opacity=P(t,a+d*.74,.35)*(1-pout);s.g2.style.opacity=P(t,a+d*.86,.35)*(1-pout);s.g3.style.opacity=P(t,a+d*.5,.35)*(1-pout);
    // 面
    const bp=P(t,b+e*.16,.6);s.bowl.g.style.opacity=bp;
    s.bowl.st.forEach((p,i)=>{const L=260;p.setAttribute('stroke-dasharray',`70 ${L}`);p.setAttribute('stroke-dashoffset',-(((t*60+i*90)%L)));p.style.opacity=bp*.7;});
    fin(s.q,t,b+e*.13,.6,30);fin(s.n1,t,b+e*.42,.5,20);fin(s.n2,t,b+e*.74,.5,20);
    fin(s.src,t,a+1,.6,12);}
});
E.add({id:'twov',a:C('c1_8')-.1,b:C('c1_9')-.05,chap:CH1,
  build(r,s){h('div','bg light',null,r);
    s.ttl=bigLine(r,'同一顿饭，两种说法',296,58);
    const card=(y,name,role,say,src,col)=>h('div','abs',`<div style="display:flex;align-items:baseline;gap:18px"><span class="black" style="font-size:60px;letter-spacing:6px">${name}</span><span class="sans" style="font-size:27px;color:#6b6052;font-weight:500">${role}</span></div><div class="bold" style="font-size:45px;line-height:1.4;margin-top:10px">${say}</div><div class="sans" style="font-size:25px;color:#6b6052;margin-top:10px">${src}</div>`,r,{left:'64px',top:y+'px',width:'952px',padding:'24px 30px 26px',background:'#efe6cf',borderLeft:`12px solid ${col}`,boxShadow:'6px 7px 0 rgba(27,24,20,.15)'});
    s.c1=card(410,'吴稚晖','当事人','俞明震给我看了密令，劝我出洋。','—— 1943 年记述，大意','#2c4563');
    s.c2=card(690,'章太炎','入狱者','吴稚晖「<span class="red">卖友脱逃</span>」。','—— 1903 年狱中书信，后人披露；吴始终否认','#1b1814');
    s.bot=h('div','abs',`<div class="sans" style="font-size:28px;letter-spacing:6px;color:#a5281d;font-weight:700">没人否认的一点</div><div class="black" style="font-size:56px;line-height:1.3;margin-top:8px">办案的官，放走了要抓的人。</div>`,r,{left:'64px',top:'1030px',width:'952px'});
  },
  update(t,lt,s){const a=C('c1_8'),d=CE('c1_8')-a;fin(s.ttl,t,a,.5,20);fin(s.c1,t,a+d*.05,.5,30);fin(s.c2,t,a+d*.28,.5,30);fin(s.bot,t,a+d*.58,.6,30);}
});
takeWebScene({id:'take1',a:C('c1_9')-.1,b:CE('c1_9')+.9,chap:CH1,html:'那个年代，一张人情网，<span class="red">比王法管用。</span>',old:['zsz'],add:['ymz','zty','wzh']});

// ── 第二章 ───────────────────────────────────────────────
const CH2='贰 · 不是谁的人';
// map_tokyo 在 scenes_a.js
quoteScene({id:'room',a:C('c2_2')-.1,b:C('c2_4')-.05,chap:CH2,
  tag:['章太炎 · 孙毓筠','1906 年，东京 · 两位同盟会员','zhi'],who:'章士钊致友人信',
  cols:['章太炎孫少侯','閉弟於室','強要入會','而弟不許'],x:960,y:520,fs:88,pitch:150,dots:[null,[0,3],null,[2,3]],
  qa:C('c2_2')+(CE('c2_2')-C('c2_2'))*.55,qd:(CE('c2_2')-C('c2_2'))*.42,
  gloss:[['弟＝我（对友人的自称）',310,560]],
  plain:{html:'把我关在屋里，硬逼我入会，<mark>我就是不答应</mark>。',at:C('c2_3')-.1,y:1100},
  src:['回忆','《章行严与杨怀中书》，《独立周报》创刊号（1912年9月）；<em>据后人引文</em>'],
  build(r,s){ // 一把锁
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    s.lock=svg('g',{transform:'translate(170,760)',fill:'none',stroke:'#1b1814','stroke-width':9,'stroke-linecap':'round'},sv);
    svg('rect',{x:-70,y:-30,width:140,height:150,fill:'#1b1814'},s.lock);svg('path',{d:'M-42,-30 L-42,-80 Q-42,-128 0,-128 Q42,-128 42,-80 L42,-30'},s.lock);
    svg('circle',{cx:0,cy:34,r:14,fill:'#e8ddc5',stroke:'none'},s.lock);svg('rect',{x:-5,y:40,width:10,height:40,fill:'#e8ddc5',stroke:'none'},s.lock);
    s.days=h('div','abs sans','据他回忆：<br>关了两天<br><b style="color:#a5281d">孫少侯＝孙毓筠</b>',r,{left:'50px',top:'910px',width:'240px',textAlign:'center',fontSize:'26px',color:'#6b6052',fontWeight:'500',lineHeight:1.5});
  },
  update(t,lt,s){const p=P(t,C('c2_2')+1.2,.5,ease.back);s.lock.style.opacity=clamp(p*2);s.lock.setAttribute('transform',`translate(170,760) scale(${lerp(1.4,1,p)})`);s.days.style.opacity=P(t,C('c2_2')+2.2,.5);}
});
E.add({id:'wrn',a:C('c2_4')-.1,b:C('c2_7')-.05,chap:CH2,
  build(r,s){h('div','bg old',null,r);
    // 上半：家世
    s.fam=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px'});
    s.tag=personTag(s.fam,'吴弱男','同盟会最早的女会员之一（据她自述）',64,300,'yin');
    const node=(x,y,n,role,big)=>h('div','abs',`<div style="display:inline-block;background:#efe6cf;border:3px solid #1b1814;padding:4px 22px 9px;font-weight:900;font-size:${big?72:56}px;letter-spacing:8px;box-shadow:6px 6px 0 rgba(27,24,20,.18)" class="trad">${n}</div><div class="sans" style="font-size:28px;color:#3a332b;margin-top:10px;font-weight:500;letter-spacing:1px">${role}</div>`,s.fam,{left:(x-260)+'px',top:y+'px',width:'520px',textAlign:'center'});
    s.n1=node(540,500,'吳長慶','淮军（李鸿章一系的军队）名将 · 祖父');s.n2=node(540,720,'吳保初','“清末四公子”之一 · 父亲');s.n3=node(540,950,'吳弱男','',true);
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},s.fam);
    s.ls=[svg('path',{d:'M540,650 L540,716',stroke:'#a5281d','stroke-width':6},sv),svg('path',{d:'M540,870 L540,946',stroke:'#a5281d','stroke-width':6},sv)];
    // 下半：地图到伦敦
    s.mp=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px'});
    s.frame=h('div','abs',null,s.mp,{left:'0',top:'300px',width:'1080px',height:'470px',overflow:'hidden',borderTop:'4px solid #1b1814',borderBottom:'4px solid #1b1814',background:'#ddd0b0'});
    s.map=GeoMap(s.frame,'eurasia',{id:'b'});s.map.city('东京',{left:true,sub:'',dy:-64});s.map.city('伦敦',{sub:'1909'});s.rt=s.map.route('东京','伦敦',.1);
    s.wed=h('div','abs',`<div class="black trad" style="font-size:86px;letter-spacing:8px">一九〇九　倫敦</div><div class="bold" style="font-size:50px;margin-top:8px">人没劝进会，两个人<span class="red">结了婚</span>。</div>`,s.mp,{left:'64px',top:'800px'});
    s.jk=h('div','abs black trad inkf','「賠了夫人<br>　又折兵」',s.mp,{left:'64px',top:'1000px',fontSize:'104px',lineHeight:'1.18',letterSpacing:'6px'});
    s.js=seal(s.mp,'據說',800,1040,170,{fs:70,bw:9});
    s.src=srcTag(r,'轶事','劝入会与孙中山戏言，均出自章家后人晚出的转述，<em>无同时代文献</em>');
  },
  update(t,lt,s){const a=C('c2_4'),d=CE('c2_4')-a,b=C('c2_5'),c=C('c2_6'),cd=CE('c2_6')-c;
    const sw=P(t,b-.25,.5,ease.io);s.fam.style.opacity=1-sw;s.mp.style.opacity=sw;s.fam.style.visibility=sw>=1?'hidden':'visible';s.mp.style.visibility=sw<=0?'hidden':'visible';
    fin(s.tag,t,a+d*.3,.5,20);fin(s.n3,t,a+d*.34,.5,24);
    fin(s.n1,t,a+d*.66,.5,24);fin(s.n2,t,a+d*.8,.5,24);s.ls.forEach((l,i)=>l.style.opacity=P(t,a+d*(.72+i*.12),.4));
    const M=s.map.M;const z=P(t,b,3.4,ease.io);const [tx,ty]=M.cities['东京'],[lx,ly]=M.cities['伦敦'];
    s.map.view(lerp(tx-120,M.w*.5,z),lerp(ty,M.h*.42,z),540,235,lerp(1.5,.72,z));
    s.rt.set(P(t,b+.5,2.6,ease.io));s.map.cities['伦敦'].style.opacity=P(t,b+2.6,.4);
    fin(s.wed,t,b+1.6,.6,24);
    fin(s.jk,t,c+cd*.45,.5,30);stamp(s.js,t,c+cd*.2,7);
    fin(s.src,t,a+1,.6,12);}
});
takeWebScene({id:'take2',a:C('c2_7')-.1,b:CE('c2_7')+.9,chap:CH2,html:'跟谁都是朋友，<span class="red">但不是谁的人。</span>',old:['zsz','ymz','zty','wzh'],add:['szs','wrn','wcq']});

// ── 第三章 ───────────────────────────────────────────────
const CH3='叁 · 一支笔';
quoteScene({id:'iron',a:C('c3_1')-.1,b:C('c3_3')-.05,chap:CH3,
  tag:['黄兴','同盟会领袖 · 章士钊的湖南同乡','zhi'],who:'章士钊回忆 · 1912',
  cols:['否否','吾有鐵飯碗在','公何忘耶'],x:940,y:520,fs:96,pitch:170,dots:[null,[2,3,4],null],
  qa:C('c3_1')+(CE('c3_1')-C('c3_1'))*.6,qd:(CE('c3_1')-C('c3_1'))*.36,
  plain:{html:'不用，我有铁饭碗，您忘了？<br>他的铁饭碗，就是<mark>手里这支笔</mark>。',at:C('c3_2')-.1,y:1060},
  src:['回忆','章士钊《与黄克强相交始末》，事后多年所写；<em>据后人引文</em>'],
  build(r,s){const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    s.pen=svg('g',{transform:'translate(200,930) rotate(20) scale(.85)',stroke:'#1b1814','stroke-width':6,fill:'none','stroke-linejoin':'round'},sv);
    svg('rect',{x:-16,y:-300,width:32,height:330,fill:'#a67c2e'},s.pen);svg('rect',{x:-20,y:20,width:40,height:44,fill:'#1b1814'},s.pen);
    svg('path',{d:'M-20,64 Q-26,130 0,196 Q26,130 20,64 Z',fill:'#1b1814'},s.pen);svg('path',{d:'M-6,-330 L6,-330 L6,-300 L-6,-300 Z',fill:'#a5281d'},s.pen);
    s.offer=h('div','abs sans','黄兴：各部长官多未到任，<br>你来试一个？',r,{left:'64px',top:'470px',fontSize:'30px',lineHeight:'1.45',color:'#3a332b',fontWeight:'500',width:'400px'});
  },
  update(t,lt,s){s.pen.style.opacity=P(t,C('c3_2')+.9,.6);s.offer.style.opacity=P(t,C('c3_1')+2.2,.5);}
});
E.add({id:'yuan',a:C('c3_3')-.1,b:C('c3_4')-.05,chap:CH3,
  build(r,s){h('div','bg light',null,r);
    s.tag=personTag(r,'袁世凯','中华民国大总统 · 1912 年起',64,300,'di');
    const node=(x,y,n,role,cls)=>h('div','abs',`<div style="display:inline-block;${cls==='c'?'background:#a5281d;color:#f0e5cc;':'background:#efe6cf;border:3px solid #1b1814;box-shadow:6px 6px 0 rgba(27,24,20,.18);'}padding:4px 22px 9px;font-weight:900;font-size:62px;letter-spacing:8px" class="trad">${n}</div><div class="sans" style="font-size:27px;color:#3a332b;margin-top:10px;font-weight:500">${role}</div>`,r,{left:(x-240)+'px',top:y+'px',width:'480px',textAlign:'center'});
    s.wcq=node(540,500,'吳長慶','淮军将领 · 统领“庆军”');s.ysk=node(250,820,'袁世凱','1881 年投奔吴长庆<br>在他军中起家');s.wrn=node(830,820,'吳弱男','吴长庆的孙女');s.zsz=node(830,1080,'章士釗','吴家的孙女婿','c');
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},r);
    s.l=[svg('path',{d:'M440,560 L290,816',stroke:'#77705f','stroke-width':6,fill:'none'},sv),svg('path',{d:'M640,560 L800,816',stroke:'#a5281d','stroke-width':6,fill:'none'},sv),svg('path',{d:'M830,985 L830,1076',stroke:'#a5281d','stroke-width':6,fill:'none'},sv),
      svg('path',{d:'M400,1010 Q560,1150 650,1130',stroke:'#1b1814','stroke-width':6,fill:'none','stroke-dasharray':'4 14','stroke-linecap':'round'},sv)];
    s.lb=[['旧部',356,704,'#77705f'],['祖孙',730,704,'#a5281d'],['夫妻',830,1030,'#a5281d'],['拉拢',500,1120,'#1b1814']].map(([tx,x,y,c])=>h('div','abs sans',tx,r,{left:x+'px',top:y+'px',transform:'translate(-50%,-50%)',fontSize:'25px',fontWeight:'700',letterSpacing:'2px',color:'#efe6cf',background:c,padding:'1px 10px 3px'}));
    s.def=h('div','abs sans','<b style="color:#2c4563">吴长庆</b>：淮军将领，袁世凯年轻时在他军中起家。',r,{left:'64px',top:'1236px',fontSize:'30px',color:'#3a332b',fontWeight:'500'});
  },
  update(t,lt,s){const a=C('c3_3'),d=CE('c3_3')-a;fin(s.tag,t,a+d*.1,.5,20);
    fin(s.ysk,t,a+d*.3,.5,24);fin(s.wcq,t,a+d*.46,.5,24);s.l[0].style.opacity=s.lb[0].style.opacity=P(t,a+d*.52,.4);
    fin(s.zsz,t,a+d*.72,.5,24);fin(s.wrn,t,a+d*.82,.5,24);s.l[1].style.opacity=s.lb[1].style.opacity=P(t,a+d*.86,.4);s.l[2].style.opacity=s.lb[2].style.opacity=P(t,a+d*.9,.4);
    s.l[3].style.opacity=s.lb[3].style.opacity=P(t,a+d*.96,.4);s.def.style.opacity=P(t,a+d*.5,.5);}
});
quoteScene({id:'offer',a:C('c3_4')-.1,b:C('c3_6')-.05,chap:CH3,
  tag:['袁世凯','大总统','di'],who:'章士钊回忆',
  cols:['欲總長','總長之','欲公使','公使之'],x:980,y:500,fs:88,pitch:128,offs:[0,120,0,120],
  qa:C('c3_4')+(CE('c3_4')-C('c3_4'))*.4,qd:(CE('c3_4')-C('c3_4'))*.55,
  src:['回忆','章士钊《与黄克强相交始末》；<em>据后人引文</em>。北大校长任命见 1912 年 10 月任免令'],
  build(r,s){
    s.cards=[['總長','部长'],['公使','驻外使节'],['北京大學校長','1912 年 10 月任命']].map(([tt,sub],i)=>{const e=h('div','abs',`<div class="black trad" style="font-size:${tt.length>2?38:60}px;letter-spacing:${tt.length>2?1:6}px;line-height:1.15;white-space:nowrap">${tt}</div><div class="sans" style="font-size:25px;color:#6b6052;margin-top:8px;font-weight:500">${sub}</div>`,r,{left:(64+i*322)+'px',top:'1010px',width:'300px',height:'190px',padding:'22px 20px',textAlign:'center',background:'#efe6cf',border:'3px solid #1b1814',boxShadow:'6px 6px 0 rgba(27,24,20,.18)',display:'flex',flexDirection:'column',justifyContent:'center'});return e;});
    s.no=seal(r,'未就',900,1120,124,{fs:50,bw:7});
    s.lab=h('div','abs sans','袁世凯开出的价码',r,{left:'64px',top:'950px',fontSize:'30px',letterSpacing:'6px',color:'#a5281d',fontWeight:'700'});
    s.gl2=h('div','abs sans','“之”＝给他<br>想当什么，就给什么',r,{left:'64px',top:'560px',fontSize:'32px',lineHeight:'1.5',color:'#a5281d',fontWeight:'700',width:'380px'});
  },
  update(t,lt,s){const p=C('c3_5'),d=CE('c3_5')-p;s.lab.style.opacity=P(t,p-.1,.4);s.gl2.style.opacity=P(t,p-.1,.5);
    s.cards.forEach((c,i)=>fin(c,t,p+[0,d*.22,d*.5][i],.5,30));stamp(s.no,t,p+d*.84,-9);}
});
E.add({id:'song',a:C('c3_6')-.1,b:C('c3_8')-.05,chap:CH3,dark:true,
  build(r,s){h('div','bg dark',null,r);
    s.hd=h('div','abs',`<div class="sans" style="font-size:30px;letter-spacing:8px;color:#a99c82">一九一三年三月 · 上海火车站</div><div class="black trad" style="font-size:108px;letter-spacing:10px;color:#e8ddc5;margin-top:8px">宋教仁遇刺</div><div class="sans" style="font-size:30px;color:#cdbf9f;margin-top:8px;letter-spacing:2px">宋教仁：国民党代理理事长，力主政党内阁</div>`,r,{left:'64px',top:'292px'});
    s.frame=h('div','abs',null,r,{left:'0',top:'590px',width:'1080px',height:'440px',overflow:'hidden',borderTop:'3px solid #8d806a',borderBottom:'3px solid #8d806a'});
    s.map=GeoMap(s.frame,'eastasia',{dark:true,id:'c'});s.map.city('北京',{left:true,dy:-30});s.map.city('上海',{dy:-10});s.rt=s.map.route('北京','上海',-.12);
    s.yuan=h('div','abs',`<div class="sans" style="font-size:28px;letter-spacing:5px;color:#e0705f;font-weight:700">章士钊回忆</div><div class="bold" style="font-size:46px;line-height:1.4;color:#e8ddc5;margin-top:6px">袁世凯当着他的面，<br>把嫌疑引向<span style="color:#e0705f">黄兴</span>。</div>`,r,{left:'64px',top:'1060px'});
    s.q=h('div','abs black trad inkf','「潛赴東站　獨馳返滬」',r,{left:'0',top:'1060px',width:'1080px',textAlign:'center',fontSize:'82px',letterSpacing:'6px',color:'#e8ddc5'});
    s.pl=h('div','abs bold','悄悄去了车站，一个人回了上海。',r,{left:'0',top:'1186px',width:'1080px',textAlign:'center',fontSize:'44px',color:'#cdbf9f'});
    s.tx=h('div','abs',`<div class="sans" style="font-size:28px;letter-spacing:5px;color:#e0705f;font-weight:700">1913 年 7 月 · 二次革命</div><div class="bold" style="font-size:46px;line-height:1.4;color:#e8ddc5;margin-top:6px">黄兴起兵讨袁。讨袁通电，<br>据他说：「此赫然吾之手筆也」。</div><div class="sans" style="font-size:28px;color:#a99c82;margin-top:10px">通电＝公开发表的电报声明</div>`,r,{left:'64px',top:'1060px'});
    s.src=srcTag(r,'回忆','章士钊《与黄克强相交始末》《黄兴年谱长编》；<em>据后人引文，离京日期待核</em>',true);
  },
  update(t,lt,s){const a=C('c3_6'),d=CE('c3_6')-a,b=C('c3_7'),e=CE('c3_7')-b;
    fin(s.hd,t,a,.6,24);const M=s.map.M,[bx,by]=M.cities['北京'],[sx,sy]=M.cities['上海'];
    s.map.view((bx+sx)/2+30,(by+sy)/2,540,220,1.08);s.frame.style.opacity=P(t,a+d*.2,.6);
    s.rt.set(P(t,a+d*.78,b+e*.3-(a+d*.78),ease.io));
    finout(s.yuan,t,a+d*.28,a+d*.76,.5,24);finout(s.q,t,a+d*.78,b+e*.36,.5,24);finout(s.pl,t,b-.1,b+e*.36,.5,20);
    fin(s.tx,t,b+e*.38,.6,24);fin(s.src,t,a+1,.6,12);}
});
takeWebScene({id:'take3',a:C('c3_8')-.1,b:CE('c3_8')+.9,chap:CH3,html:'他的笔谁都想要，<span class="red">可往哪边写，他自己定。</span>',fs:46,old:['zsz','ymz','zty','wzh','szs','wrn','wcq'],add:['hx','ysk']});
