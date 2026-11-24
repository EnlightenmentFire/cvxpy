// 可复用组件：出处标签、人物名牌、关系网、地图、章节卡、引文卡
const REL={ // 关系线配色
  shi:{c:'#a67c2e',n:'师生'}, yin:{c:'#a5281d',n:'姻亲'}, zhi:{c:'#2c4563',n:'同志'}, di:{c:'#1b1814',n:'对手'}, guan:{c:'#77705f',n:'上下级'}
};
function srcTag(root,kind,html,dark,top){
  const e=h('div','src'+(dark?' dk':''),`<b>${kind}</b><span>${html}</span>`,root);
  if(top!==undefined)e.style.top=top+'px';return e;
}
function personTag(root,name,role,x,y,rel,light){
  const e=h('div','tag'+(light?' lt':''),`<div class="barv" style="background:${rel?REL[rel].c:'#a5281d'}"></div><div class="tx"><div class="nm">${name}</div><div class="rl">${role}</div></div>`,root);
  e.style.left=x+'px';e.style.top=y+'px';return e;
}
function seal(root,text,x,y,size,opt={}){
  // text: 2 或 4 个字，按传统自右向左、自上而下排
  const e=h('div','seal'+(opt.fill?' fill':'')+(opt.dark?' ondark':''),null,root);
  const n=[...text];const cols=n.length<=2?1:2;const fs=opt.fs||Math.floor(size/(cols===1?(n.length===1?1.25:2.25):2.25));
  e.style.cssText+=`left:${x}px;top:${y}px;width:${size}px;height:${opt.h||size}px;font-size:${fs}px;line-height:1.05;`;
  if(n.length===4)e.innerHTML=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 ${fs*0.08}px;direction:rtl"><span>${n[0]}</span><span>${n[2]}</span><span>${n[1]}</span><span>${n[3]}</span></div>`;
  else e.innerHTML=`<div style="writing-mode:vertical-rl">${text}</div>`;
  if(opt.bw)e.style.borderWidth=opt.bw+'px';
  return e;
}

// ── 关系网 ───────────────────────────────────────────────
const WEB_NODES={
  zsz:{n:'章士釗',r:'',x:540,y:800,center:true},
  ymz:{n:'俞明震',r:'陆师学堂校长·查办官',x:210,y:470},
  zty:{n:'章太炎',r:'结拜兄长·入狱三年',x:560,y:420},
  wzh:{n:'吴稚晖',r:'爱国学社同人',x:890,y:500},
  szs:{n:'孙中山',r:'同盟会总理',x:900,y:735},
  hx:{n:'黄兴',r:'同盟会领袖·湖南同乡',x:880,y:960},
  wrn:{n:'吴弱男',r:'妻·同盟会女会员',x:190,y:735},
  wcq:{n:'吴长庆',r:'淮军将领·弱男祖父',x:190,y:985},
  ysk:{n:'袁世凯',r:'大总统·吴长庆旧部',x:330,y:1190},
  dqr:{n:'段祺瑞',r:'临时执政',x:640,y:1200},
  lx:{n:'鲁迅',r:'教育部佥事·周树人',x:900,y:1170},
};
const WEB_EDGES=[
  ['zsz','ymz','shi','师生'],['zsz','zty','zhi','结拜'],['zsz','wzh','zhi','同人'],['ymz','wzh','guan','放走',true,.26],
  ['zsz','szs','zhi','不入会'],['zsz','wrn','yin','夫妻'],['wrn','wcq','yin','祖孙'],
  ['zsz','hx','zhi','秘书长'],['wcq','ysk','guan','旧部'],['zsz','ysk','di','拉拢→决裂'],
  ['zsz','dqr','guan','总长'],['zsz','lx','di','免职→被告'],
];
function Web(root,opt={}){
  const g=h('div','abs',null,root,{left:'0',top:'0',width:'1080px',height:'1920px'});
  const s=svg('svg',{width:1080,height:1920,style:'position:absolute;left:0;top:0'},g);
  const nodes={},edges=[];
  for(const [a,b,rel,lab,dash,lf] of WEB_EDGES){
    const A_=WEB_NODES[a],B_=WEB_NODES[b];
    const len=Math.hypot(B_.x-A_.x,B_.y-A_.y);
    const ln=svg('line',{x1:A_.x,y1:A_.y,x2:B_.x,y2:B_.y,stroke:REL[rel].c,'stroke-width':rel==='guan'?4:6,'stroke-linecap':'round','stroke-dasharray':len,'stroke-dashoffset':len},s);
    if(dash)ln.setAttribute('stroke-dasharray','2 14');
    const f=lf||(A_.center?.6:.5);const mx=lerp(A_.x,B_.x,f),my=lerp(A_.y,B_.y,f);
    const lb=h('div','abs sans',lab,g,{left:mx+'px',top:my+'px',transform:'translate(-50%,-50%)',fontSize:'23px',fontWeight:'700',letterSpacing:'2px',color:'#efe6cf',background:REL[rel].c,padding:'1px 9px 3px',whiteSpace:'nowrap'});
    edges.push({a,b,ln,lb,len,dash});
  }
  for(const k in WEB_NODES){const n=WEB_NODES[k];
    const e=h('div','abs',null,g,{left:n.x+'px',top:n.y+'px'});
    if(n.center){
      e.innerHTML=`<div style="transform:translate(-50%,-50%);background:#a5281d;color:#f0e5cc;padding:10px 26px 14px;font-family:var(--serift);font-weight:900;font-size:66px;letter-spacing:8px;white-space:nowrap;box-shadow:0 0 0 5px #e8ddc5,0 0 0 9px #a5281d">${n.n}</div>`;
    }else{
      e.innerHTML=`<div style="transform:translate(-50%,-50%);text-align:center;white-space:nowrap"><div style="display:inline-block;background:#ece2ca;border:3px solid #1b1814;padding:3px 18px 7px;font-weight:900;font-size:44px;letter-spacing:5px;box-shadow:5px 5px 0 rgba(27,24,20,.18)">${n.n}</div><div class="sans" style="font-size:22px;letter-spacing:1px;color:#3a332b;margin-top:6px;font-weight:500"><span style="background:#e4d9c0;padding:1px 6px 2px">${n.r}</span></div></div>`;
    }
    nodes[k]=e;
  }
  // 图例
  const lg=h('div','abs sans',null,g,{left:'64px',top:(opt.legendY||1306)+'px',width:'952px',display:'flex',justifyContent:'space-between',fontSize:'25px',letterSpacing:'2px',color:'#3a332b',fontWeight:'500'});
  for(const k of ['shi','yin','zhi','di','guan'])h('div',null,`<i style="display:inline-block;width:44px;height:7px;background:${REL[k].c};vertical-align:middle;margin-right:10px"></i>${REL[k].n}`,lg);
  return {g,nodes,edges,lg,
    // times: {nodeKey: 出现时间}，未列出的不显示
    update(t,times){
      for(const k in nodes){const t0=times[k];const p=t0===undefined?0:P(t,t0,.5,ease.back);
        nodes[k].style.opacity=clamp(p*1.6);nodes[k].style.visibility=p<=0?'hidden':'visible';nodes[k].style.transform=`scale(${lerp(.7,1,p)})`;}
      for(const e of edges){const ta=times[e.a],tb=times[e.b];if(ta===undefined||tb===undefined){e.ln.style.opacity=0;e.lb.style.opacity=0;continue;}
        const t0=Math.max(ta,tb)-.1;const p=P(t,t0,.7,ease.io);e.ln.style.opacity=p>0?1:0;
        if(!e.dash)e.ln.setAttribute('stroke-dashoffset',e.len*(1-p));else e.ln.style.opacity=p;
        e.lb.style.opacity=P(t,t0+.45,.35);}
    }};
}

// ── 地图 ─────────────────────────────────────────────────
function GeoMap(root,which,opt={}){
  const M=window.MAPDATA[which];
  const wrap=h('div','abs',null,root,{left:'0',top:'0',width:M.w+'px',height:M.h+'px',transformOrigin:'0 0'});
  const s=svg('svg',{width:M.w,height:M.h,viewBox:`0 0 ${M.w} ${M.h}`},wrap);
  // 海：细横线
  const pat=svg('pattern',{id:'sea_'+which+(opt.id||''),width:14,height:14,patternUnits:'userSpaceOnUse'},svg('defs',{},s));
  svg('line',{x1:0,y1:7,x2:14,y2:7,stroke:opt.dark?'rgba(205,191,159,.10)':'rgba(27,24,20,.10)','stroke-width':1.2},pat);
  svg('rect',{x:0,y:0,width:M.w,height:M.h,fill:`url(#sea_${which}${opt.id||''})`},s);
  svg('path',{d:M.d,fill:opt.dark?'#3b342b':'#cdbd97',stroke:opt.dark?'#8d806a':'#4a4136','stroke-width':1.3,'stroke-linejoin':'round'},s);
  const routes=svg('g',{},s);const marks=h('div','abs',null,wrap,{left:0,top:0});
  const api={wrap,M,cities:{},routes:[],
    city(name,opt2={}){const [x,y]=M.cities[name];
      const e=h('div','abs',`<div style="position:absolute;left:-13px;top:-13px;width:26px;height:26px;border-radius:50%;background:#a5281d;box-shadow:0 0 0 5px rgba(165,40,29,.25)"></div>
        <div class="black" style="position:absolute;${opt2.left?'right:26px;text-align:right':'left:26px'};top:${opt2.dy||-34}px;font-size:${opt2.fs||46}px;letter-spacing:4px;white-space:nowrap;color:${opt.dark?'#e8ddc5':'#1b1814'};text-shadow:0 0 6px ${opt.dark?'#15120f':'#e8ddc5'},0 0 6px ${opt.dark?'#15120f':'#e8ddc5'}">${name}${opt2.sub?`<span class="sans" style="font-size:${(opt2.fs||46)*.52}px;font-weight:500;letter-spacing:1px;margin-left:10px;color:${opt.dark?'#cdbf9f':'#3a332b'}">${opt2.sub}</span>`:''}</div>`,marks,{left:x+'px',top:y+'px'});
      api.cities[name]=e;return e;},
    route(from,to,bend=.18){const [x1,y1]=M.cities[from],[x2,y2]=M.cities[to];
      const mx=(x1+x2)/2,my=(y1+y2)/2,dx=x2-x1,dy=y2-y1;const cx=mx-dy*bend,cy=my+dx*bend;
      const p=svg('path',{d:`M${x1},${y1} Q${cx},${cy} ${x2},${y2}`,fill:'none',stroke:'#a5281d','stroke-width':opt.rw||5,'stroke-linecap':'round'},routes);
      const len=p.getTotalLength();p.setAttribute('stroke-dasharray',len);p.setAttribute('stroke-dashoffset',len);
      const r={p,len,set(pr){p.setAttribute('stroke-dashoffset',len*(1-pr));}};api.routes.push(r);return r;},
    // 把地图上的点 (mx,my) 放到舞台 (sx,sy)，缩放 k
    view(mx,my,sx,sy,k){wrap.style.transform=`translate(${sx-mx*k}px,${sy-my*k}px) scale(${k})`;
      for(const n in api.cities)api.cities[n].style.transform=`scale(${1/k})`;}
  };
  return api;
}

// ── 章节卡 ───────────────────────────────────────────────
function chapterCard(a,b,num,title,sub,chap){
  E.add({id:'chap_'+num,a,b,dark:true,nosub:true,chap:'',fi:.45,fo:.35,
    build(r,s){h('div','bg dark',null,r);
      s.box=h('div','abs',null,r,{left:'0',top:'560px',width:'1080px',textAlign:'center'});
      s.num=seal(r,num,460,520,160,{fill:true,fs:112});
      s.rule1=h('div','rule',null,r,{left:'240px',top:'760px',width:'600px',color:'#a67c2e'});
      s.tt=h('div','abs black trad',title,r,{left:'0',top:'800px',width:'1080px',textAlign:'center',fontSize:'118px',letterSpacing:'16px',color:'#e8ddc5',textIndent:'16px'});
      s.sb=h('div','abs sans',sub,r,{left:'0',top:'990px',width:'1080px',textAlign:'center',fontSize:'34px',letterSpacing:'10px',color:'#a99c82',fontWeight:'400'});
      s.rule2=h('div','rule',null,r,{left:'240px',top:'1080px',width:'600px',color:'#a67c2e'});
    },
    update(t,lt,s){stamp(s.num,lt,.15,-3);
      const p=P(lt,.35,.7);s.rule1.style.transform=`scaleX(${p})`;s.rule2.style.transform=`scaleX(${p})`;
      fin(s.tt,lt,.45,.7,30);fin(s.sb,lt,.8,.6,20);}
  });
}

// ── 引文卡（竖排繁体原文 + 横排白话）────────────────────
// cols: 每列一个字符串（自右向左）；返回逐字 span 数组
function vQuote(root,cols,x,y,fs,opt={}){
  const wrap=h('div','abs',null,root,{left:x+'px',top:y+'px'});
  const spans=[];const pitch=opt.pitch||fs*1.42;
  cols.forEach((c,i)=>{const col=h('div','quote',null,wrap,{right:(i*pitch)+'px',top:(opt.offs&&opt.offs[i]||0)+'px',fontSize:fs+'px',lineHeight:'1.12',color:opt.color||''});
    const d=opt.dots&&opt.dots[i];spans.push(...chars(col,c,d));});
  wrap.style.width='0px';
  return {wrap,spans};
}
function plainBox(root,html,x,y,w,fs,lab){
  return h('div','plain',`<div class="lab">${lab||'大白话'}</div><div>${html}</div>`,root,{left:x+'px',top:y+'px',width:w+'px',fontSize:fs+'px'});
}
