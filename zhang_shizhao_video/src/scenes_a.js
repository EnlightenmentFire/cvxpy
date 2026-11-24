// 场景（一）：冷启动、章节卡、苏报案引文卡、关系网、地图、两个桃子、日历
// ── 冷启动：平政院裁决书 ────────────────────────────────
E.add({id:'verdict',nokb:true,a:0,b:C('c0_3')-.05,dark:true,chap:'1926 · 北京',fi:.8,
  build(r,s){
    h('div','bg dark',null,r);
    s.cam=h('div','abs',null,r,{left:0,top:0,width:'1080px',height:'1920px',transformOrigin:'540px 780px'});
    const doc=s.doc=h('div','abs',null,s.cam,{left:'150px',top:'326px',width:'780px',height:'910px',backgroundImage:'url(../assets/paper_old.jpg)',backgroundSize:'1080px 1920px',backgroundPosition:'-120px -300px',boxShadow:'0 30px 80px rgba(0,0,0,.65), 0 0 0 1px rgba(0,0,0,.4)',transform:'rotate(-1.1deg)'});
    // 朱丝栏
    const PT=79.1,GX=34,GY=36;
    const grid=h('div','abs cols',null,doc,{left:GX+'px',top:GY+'px',width:'712px',height:'838px',border:'3px solid rgba(165,40,29,.6)'});grid.style.setProperty('--pitch',PT+'px');
    const col=(i,txt,fs,top,cls,style)=>{const e=h('div','abs v trad '+(cls||'bold'),txt,doc,Object.assign({right:(GX+i*PT+(PT-fs)/2)+'px',top:(GY+top)+'px',fontSize:fs+'px',lineHeight:'1',letterSpacing:'.14em',color:'#1b1814',whiteSpace:'nowrap'},style||{}));e.classList.add('inkf');return e;};
    s.cols=[
      col(0,'平政院裁決書',58,40,'black',{letterSpacing:'.3em'}),
      col(1,'原告　周樹人',38,40,'bold'),
      col(1,'教育部僉事',26,400,'semi',{color:'#3a332b'}),
      col(2,'被告　教育部',38,40,'bold'),
      col(3,'主文',32,40,'black',{color:'#a5281d',letterSpacing:'.6em'}),
    ];
    s.main=col(4,'教育部之處分取消之',58,150,'black',{letterSpacing:'.2em'});
    s.cols.push(col(5,'理由',32,40,'black',{color:'#a5281d',letterSpacing:'.6em'}));
    s.cols.push(col(6,'被告遽行呈請免職確與',34,120,'semi'));
    s.cols.push(col(7,'現行法令規定程序不符',34,120,'semi'));
    s.date=col(8,'中華民國十五年三月',27,500,'semi',{letterSpacing:'.12em'});
    // 主文高亮
    s.hl=h('div','abs',null,doc,{right:(GX+4*PT+1)+'px',top:(GY+130)+'px',width:(PT-2)+'px',height:'668px',background:'rgba(165,40,29,.13)',borderLeft:'5px solid #a5281d',borderRight:'5px solid #a5281d',transformOrigin:'50% 0'});
    s.seal=seal(doc,'平政院印',24,588,178,{bw:9});
    s.note=srcTag(r,'出处','平政院裁决书（1926年3月）主文与理由原文；<em>画面为据文字重排，非原件影像</em>',true);
    s.where=h('div','abs sans','一九二六年三月 · 北京',r,{left:'0',top:'1232px',width:'1080px',textAlign:'center',fontSize:'30px',letterSpacing:'12px',color:'#a99c82',display:'none'});
  },
  update(t,lt,s){
    const q=C('c0_2');
    const push=P(t,0,s.b,ease.io2);
    const [sx,sy]=shake(t,q+.75,12);
    s.cam.style.transform=`translate(${sx}px,${sy+lerp(8,-6,push)}px) scale(${lerp(.985,1.045,push)})`;
    s.cols.forEach((c,i)=>{c.style.opacity=P(t,.3+i*.12,.7);});
    s.date.style.opacity=P(t,1.6,.7);
    s.main.style.opacity=lerp(.0,1,P(t,1.0,.8));
    const hp=P(t,q-.15,.5,ease.out3);s.hl.style.transform=`scaleY(${hp})`;s.hl.style.opacity=hp;
    stamp(s.seal,t,q+.55,-7);
    fin(s.note,t,q+1.2,.6,14);
  }
});

// ── 章节卡 ───────────────────────────────────────────────
[['c1','壹','一張人情網','1903 · 上海 · 蘇報案'],['c2','貳','不是誰的人','1905–1909 · 東京 · 倫敦'],['c3','叁','一支筆','1912–1913 · 北京 · 上海'],
 ['c4','肆','有容','1914 · 東京 ·《甲寅》'],['c5','伍','兩個桃子','1923 · 文言與白話'],['c6','陸','老虎總長','1925–1926 · 北京']].forEach(([c,n,tt,sb])=>{
  const first=C(c+'_1');chapterCard(first-2.75,first-.12,n,tt,sb);
});

// ── 引文卡：阳怒而阴佐之 ────────────────────────────────
E.add({id:'q_yangnu',a:C('c1_4')-.1,b:C('c1_6')-.05,chap:'壹 · 一张人情网',
  build(r,s){
    h('div','bg light',null,r);
    s.tag=personTag(r,'俞明震','江苏候补道 · 苏报案查办官<br>南京陆师学堂总办（校长）',64,300,'shi');
    s.who=h('div','abs sans','章士钊回忆',r,{right:'64px',top:'318px',fontSize:'30px',letterSpacing:'8px',color:'#6b6052',fontWeight:'500'});
    s.q=vQuote(r,['顧余為革命故','不得不與','俞先生翻異','……','乃先生','陽怒而陰佐之'],1000,492,84,{pitch:124,offs:[0,0,0,210,0,0],dots:[null,null,[3,4],null,null,[0,1,3,4]]});
    s.q.spans.forEach(x=>x.classList.add('inkf'));
    s.gloss=h('div','abs sans','翻異＝翻脸',r,{left:'120px',top:'600px',fontSize:'30px',color:'#a5281d',fontWeight:'700',letterSpacing:'4px',writingMode:'vertical-rl',borderRight:'3px solid #a5281d',paddingRight:'12px'});
    s.plain=plainBox(r,'我为革命跟老师翻了脸；<br>老师<mark>表面发火</mark>，<mark>暗地里却在帮我</mark>。',64,1060,960,47);
    s.src=srcTag(r,'回忆','章士钊《苏报案始末记叙》，事后多年所写；<em>据后人引文，页码待核</em>');
  },
  update(t,lt,s){
    const a=C('c1_4'),b=CE('c1_4'),p0=C('c1_5');
    fin(s.tag,t,a-.05,.5,20);s.who.style.opacity=P(t,a+.2,.5);
    reveal(s.q.spans,t,a+1.35,(b-a)-1.6);
    s.gloss.style.opacity=P(t,a+3.2,.5);
    fin(s.plain,t,p0-.1,.6,30);
    fin(s.src,t,a+1,.6,12);
  }
});

// ── 地图：上海—东京—伦敦 ────────────────────────────────
E.add({id:'map_tokyo',nokb:true,a:C('c2_1')-.1,b:C('c2_2')-.05,chap:'贰 · 不是谁的人',
  build(r,s){h('div','bg old',null,r);
    s.frame=h('div','abs',null,r,{left:'0',top:'330px',width:'1080px',height:'700px',overflow:'hidden',borderTop:'4px solid #1b1814',borderBottom:'4px solid #1b1814'});
    s.map=GeoMap(s.frame,'eurasia');
    s.map.city('上海',{left:true,sub:'1903',dy:-4});s.map.city('东京',{sub:'1905',dy:-64});s.map.city('伦敦',{sub:'1909'});
    s.r1=s.map.route('上海','东京',-.25);s.r2=s.map.route('东京','伦敦',.12);
    s.ttl=h('div','abs black trad','一九〇五　東京',r,{left:'64px',top:'1060px',fontSize:'84px',letterSpacing:'8px',display:'none'});
    s.def=h('div','abs',`<span class="sans" style="font-size:26px;font-weight:700;letter-spacing:6px;color:#e8ddc5;background:#2c4563;padding:3px 12px 4px 16px">名词</span>
      <div class="black" style="font-size:60px;margin-top:14px;letter-spacing:6px">同盟会</div>
      <div class="sans" style="font-size:36px;line-height:1.5;margin-top:6px;color:#3a332b;font-weight:500">孙中山领导的革命组织，<br>1905 年 8 月在东京成立。</div>`,r,{left:'64px',top:'1060px'});
    s.note=h('div','abs bold','章士钊人在东京，<span class="red">偏不入会。</span>',r,{left:'64px',top:'1060px',fontSize:'60px',lineHeight:'1.3'});
  },
  update(t,lt,s){const a=s.a;const z=P(t,a,3.5,ease.io);
    // 从欧亚全景推到东亚
    const M=s.map.M,[tx,ty]=M.cities['东京'],[sx,sy]=M.cities['上海'];
    const k=lerp(.72,1.9,z);const fx=lerp(M.w*.5,(tx+sx)/2-10,z),fy=lerp(M.h*.5,(ty+sy)/2,z);
    s.map.view(fx,fy,540,350,k);
    s.map.cities['上海'].style.opacity=P(t,a+.3,.4);s.r1.set(P(t,a+1.6,1.4,ease.io));
    s.map.cities['东京'].style.opacity=P(t,a+2.6,.4);
    s.map.cities['伦敦'].style.opacity=0;s.r2.set(0);
    const d=CE('c2_1')-C('c2_1');finout(s.def,t,a+d*.2,a+d*.66,.6,24);fin(s.note,t,a+d*.68,.6,24);
  }
});

// ── 两个桃子：拓片风线描 ────────────────────────────────
function warriorSVG(g,x,y,sc,pose,flip){
  const G=svg('g',{transform:`translate(${x},${y}) scale(${flip?-sc:sc},${sc})`},g);
  const F='#e6dcc3',D='#1d1a17';
  // 下裳
  svg('path',{d:'M-32,-165 Q-44,-70 -78,0 L80,0 Q42,-70 30,-165 Z',fill:F},G);
  // 上身
  svg('path',{d:'M-36,-232 Q0,-250 36,-232 L32,-160 L-34,-160 Z',fill:F},G);
  // 头、冠
  svg('circle',{cx:2,cy:-268,r:22,fill:F},G);
  svg('path',{d:'M-14,-288 L18,-288 L12,-306 L-8,-306 Z',fill:F},G);
  svg('path',{d:'M4,-306 Q-4,-336 -22,-350',stroke:F,'stroke-width':5,fill:'none','stroke-linecap':'round'},G);
  svg('path',{d:'M10,-306 Q10,-338 -2,-356',stroke:F,'stroke-width':5,fill:'none','stroke-linecap':'round'},G);
  if(pose===0){ // 举剑
    svg('path',{d:'M30,-228 Q70,-262 96,-300 L112,-286 Q104,-226 52,-186 Z',fill:F},G);
    svg('path',{d:'M100,-296 L156,-392',stroke:F,'stroke-width':7,'stroke-linecap':'round'},G);
    svg('path',{d:'M90,-286 L114,-306',stroke:F,'stroke-width':6,'stroke-linecap':'round'},G);
    svg('path',{d:'M-34,-226 Q-70,-210 -92,-168 L-74,-150 Q-46,-170 -30,-186 Z',fill:F},G);
  }else if(pose===1){ // 伸手取桃
    svg('path',{d:'M30,-228 Q84,-236 128,-222 L128,-200 Q84,-176 40,-186 Z',fill:F},G);
    svg('path',{d:'M-34,-226 Q-64,-200 -70,-150 L-50,-142 Q-40,-170 -30,-186 Z',fill:F},G);
    svg('path',{d:'M-52,-150 L-108,-64',stroke:F,'stroke-width':7,'stroke-linecap':'round'},G);
  }else{ // 按剑而立
    svg('path',{d:'M30,-228 Q62,-214 70,-168 L50,-158 Q40,-176 30,-186 Z',fill:F},G);
    svg('path',{d:'M-34,-226 Q-76,-236 -104,-262 L-112,-240 Q-86,-196 -34,-186 Z',fill:F},G);
    svg('path',{d:'M56,-160 L118,-70',stroke:F,'stroke-width':7,'stroke-linecap':'round'},G);
    svg('path',{d:'M46,-150 L70,-166',stroke:F,'stroke-width':6,'stroke-linecap':'round'},G);
  }
  // 阴刻衣纹
  for(const d of ['M-34,-160 L32,-160','M-6,-158 Q-14,-70 -30,-2','M12,-158 Q22,-70 44,-2','M-22,-246 L20,-170','M24,-246 L-18,-170'])svg('path',{d,stroke:D,'stroke-width':3.2,fill:'none'},G);
  return G;
}
E.add({id:'peaches',a:C('c5_2')-.1,b:C('c5_5')-.05,chap:'伍 · 两个桃子',
  build(r,s){h('div','bg light',null,r);
    s.who=h('div','abs sans','章士钊《评新文化运动》· 1923',r,{left:'64px',top:'300px',fontSize:'30px',letterSpacing:'5px',color:'#6b6052',fontWeight:'500'});
    // 拓片
    const slab=s.slab=h('div','abs',null,r,{left:'64px',top:'372px',width:'952px',height:'520px',background:'#1d1a17',boxShadow:'0 10px 30px rgba(27,24,20,.35)'});
    const sv=svg('svg',{width:952,height:520,viewBox:'0 0 952 520',style:'filter:url(#rough2)'},slab);
    // 上缘菱形纹
    for(let i=0;i<24;i++)svg('path',{d:`M${22+i*38},18 l19,16 l-19,16 l-19,-16 Z`,fill:'none',stroke:'#e6dcc3','stroke-width':3},sv);
    svg('rect',{x:14,y:12,width:924,height:496,fill:'none',stroke:'#e6dcc3','stroke-width':4},sv);
    svg('line',{x1:14,y1:58,x2:938,y2:58,stroke:'#e6dcc3','stroke-width':3},sv);
    svg('line',{x1:14,y1:470,x2:938,y2:470,stroke:'#e6dcc3','stroke-width':3},sv);
    s.w=[warriorSVG(sv,150,470,1.0,2,false),warriorSVG(sv,340,470,1.02,0,false),warriorSVG(sv,520,470,1.0,1,false)];
    // 高足盘与二桃
    const dish=s.dish=svg('g',{transform:'translate(700,470)'},sv);const F='#e6dcc3';
    svg('path',{d:'M-62,-150 Q0,-104 62,-150 L62,-158 L-62,-158 Z',fill:F},dish);svg('rect',{x:-8,y:-118,width:16,height:86,fill:F},dish);svg('path',{d:'M-44,0 L44,0 L22,-34 L-22,-34 Z',fill:F},dish);
    s.p=[-28,28].map(dx=>svg('path',{transform:`translate(${dx},-186)`,d:'M0,-34 C10,-20 30,-14 26,8 C22,28 -22,28 -26,8 C-30,-14 -10,-20 0,-34Z',fill:F},dish));
    // 晏子（矮小、拱手）
    const yz=s.yz=svg('g',{transform:'translate(850,470) scale(-.78,.78)'},sv);
    svg('path',{d:'M-30,-165 Q-40,-70 -66,0 L70,0 Q40,-70 30,-165 Z',fill:F},yz);svg('path',{d:'M-36,-232 Q0,-250 36,-232 L32,-160 L-34,-160 Z',fill:F},yz);
    svg('circle',{cx:2,cy:-268,r:22,fill:F},yz);svg('path',{d:'M-16,-286 L20,-286 L20,-312 L-16,-300 Z',fill:F},yz);
    svg('path',{d:'M30,-226 Q76,-214 92,-190 L84,-164 Q52,-160 28,-180 Z',fill:F},yz);
    h('div','abs',null,slab,{left:0,top:0,width:'952px',height:'520px',backgroundImage:'url(../assets/rub_specks.png)',opacity:.9});
    s.nm=[['古冶子',150],['田開疆',340],['公孫接',520],['晏子',850]].map(([n,x])=>h('div','abs sans',n,slab,{left:(x-60)+'px',top:'474px',width:'120px',textAlign:'center',fontSize:'23px',letterSpacing:'3px',color:'#e6dcc3',fontWeight:'500'}));
    s.cap=h('div','abs sans','二桃杀三士 · 仿汉画像石拓片风格自绘',r,{right:'64px',top:'902px',fontSize:'24px',letterSpacing:'2px',color:'#6b6052'});
    // 五个字
    s.five=h('div','abs black trad',null,r,{left:'64px',top:'950px',fontSize:'124px',letterSpacing:'18px',whiteSpace:'nowrap'});
    s.fs=chars(s.five,'二桃殺三士');s.fs.forEach(x=>x.classList.add('inkf'));
    s.arrow=h('div','abs sans','换成白话 ↓',r,{left:'68px',top:'1112px',fontSize:'30px',letterSpacing:'6px',color:'#a5281d',fontWeight:'700'});
    s.bai=h('div','abs black','两个桃子杀了三个<span style="position:relative;display:inline-block" id="dsr">读书人<i style="position:absolute;left:-4px;right:-4px;top:54%;height:7px;background:#a5281d;transform-origin:0 50%"></i><b style="position:absolute;left:8px;top:-62px;font-size:56px;color:#a5281d;font-family:var(--serif);white-space:nowrap;transform:rotate(-5deg)">勇士！</b></span>',r,{left:'64px',top:'1160px',fontSize:'70px',letterSpacing:'2px',whiteSpace:'nowrap'});
    s.strike=s.bai.querySelector('i');s.fix=s.bai.querySelector('b');
    s.src=srcTag(r,'原文','章士钊《评新文化运动》，1923年8月上海《新闻报》；典出《晏子春秋·内篇谏下》');
  },
  update(t,lt,s){const a=C('c5_2'),b=CE('c5_2'),c=C('c5_3'),d=C('c5_4'),e=s.b;
    const z=P(t,a,e-a,ease.io2);s.slab.style.transform=`scale(${lerp(1.0,1.035,z)})`;
    s.w.forEach((w,i)=>w.style.opacity=P(t,a+.2+i*.25,.6));s.dish.style.opacity=P(t,a+.1,.6);s.yz.style.opacity=P(t,d+1.2,.6);
    reveal(s.fs,t,a+.2,1.3);
    const bq=a+(b-a)*.58;s.arrow.style.opacity=P(t,bq-.4,.4);
    fin(s.bai,t,bq,.6,24);
    s.strike.style.transform='scaleX(0)';s.fix.style.opacity=0;
    fin(s.src,t,a+.8,.6,12);s.cap.style.opacity=P(t,a+.8,.6);s.nm.forEach((n,i)=>n.style.opacity=P(t,d+1.0+i*.25,.4));
  }
});

// ── 日历：八月十二日 vs 八月十三日 ─────────────────────
function calPage(root,x,y,day,wk,head,body,hot){
  const e=h('div','abs',null,root,{left:x+'px',top:y+'px',width:'440px',height:'640px',background:'#efe6cf',boxShadow:'0 14px 0 -6px #d8ccb0,0 26px 0 -12px #cbbd9e,0 30px 40px rgba(27,24,20,.35)',border:'3px solid #1b1814',transformOrigin:'50% 0'});
  e.innerHTML=`<div style="background:${hot?'#a5281d':'#1b1814'};color:#efe6cf;height:92px;display:flex;align-items:center;justify-content:space-between;padding:0 24px" class="trad bold"><span style="font-size:30px;letter-spacing:3px">中華民國十四年</span><span style="font-size:40px;letter-spacing:4px">八月</span></div>
   <div class="black" style="font-size:300px;line-height:310px;text-align:center;letter-spacing:-6px;color:${hot?'#a5281d':'#1b1814'};font-family:var(--serif)">${day}</div>
   <div class="sans" style="text-align:center;font-size:30px;letter-spacing:10px;color:#3a332b;font-weight:500;margin-top:-6px">1925 · ${wk}</div>
   <div style="margin:22px 26px 0;border-top:3px solid #1b1814;padding-top:16px"><div class="sans" style="font-size:25px;letter-spacing:5px;color:#a5281d;font-weight:700">${head}</div><div class="bold" style="font-size:38px;line-height:1.35;margin-top:6px">${body}</div></div>`;
  return e;
}
E.add({id:'calendar',a:C('c6_8')-.1,b:C('c6_10')-.05,chap:'陆 · 老虎总长',
  build(r,s){h('div','bg light',null,r);
    s.ttl=h('div','abs black','他抓住一个日期',r,{left:'64px',top:'296px',fontSize:'60px',letterSpacing:'6px'});
    s.c12=calPage(r,64,420,'12','星期三','教育部 · 呈请免职','罪名：倡设校务维持会，<span class="red">充任委员</span>',false);
    s.c13=calPage(r,576,420,'13','星期四','女师大 · 校务维持会','这一天，才公举周树人<span class="red">为委员</span>',true);
    const sv=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0;pointer-events:none'},r);
    s.arc=svg('path',{d:'M796,1098 C760,1215 330,1215 290,1104',fill:'none',stroke:'#a5281d','stroke-width':8,'stroke-linecap':'round'},sv);
    s.arcLen=s.arc.getTotalLength();s.arc.setAttribute('stroke-dasharray',s.arcLen);
    s.head=svg('path',{d:'M268,1128 L290,1100 L316,1124',fill:'none',stroke:'#a5281d','stroke-width':8,'stroke-linecap':'round','stroke-linejoin':'round'},sv);
    s.q=h('div','abs black','先有罪名，后有其事？',r,{left:'0',top:'1196px',width:'1080px',textAlign:'center',fontSize:'58px',letterSpacing:'6px',color:'#a5281d'});
    s.src=srcTag(r,'原文','鲁迅互辩书，引自鲁迅《从胡须说到牙齿》（1925年10月）');
  },
  update(t,lt,s){const a=C('c6_8'),p=C('c6_9');
    fin(s.ttl,t,a-.05,.5,20);
    const p12=P(t,a+.2,.6,ease.out3);A(s.c12,{o:p12,y:(1-p12)*40,r:-1.5});
    // 13 日翻页落下
    const f=P(t,a+4.6,.7,ease.out3);s.c13.style.opacity=clamp(f*3);s.c13.style.transform=`perspective(1400px) rotateX(${lerp(-88,0,f)}deg) rotate(1.5deg)`;
    const ar=P(t,p+.4,.9,ease.io);s.arc.setAttribute('stroke-dashoffset',s.arcLen*(1-ar));s.head.style.opacity=ar>=1?1:0;
    const q=P(t,p+1.2,.4,ease.back);A(s.q,{o:clamp(q*2),s:lerp(1.3,1,q)});
    fin(s.src,t,a+.8,.6,12);
  }
});
