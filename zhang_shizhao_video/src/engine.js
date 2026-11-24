// 极简确定性时间轴引擎：所有画面状态都是时间 t 的纯函数，逐帧截图即可得到一致结果
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const lerp=(a,b,p)=>a+(b-a)*p;
const ease={
  lin:p=>p, out2:p=>1-(1-p)*(1-p), out3:p=>1-Math.pow(1-p,3), out5:p=>1-Math.pow(1-p,5),
  in2:p=>p*p, in3:p=>p*p*p,
  io:p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,
  io2:p=>p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2,
  back:p=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2);},
};
// 进度：t 从 t0 开始，持续 d 秒
const P=(t,t0,d,e=ease.out3)=>e(clamp((t-t0)/d));
// 时间段内为 1 的窗（带淡入淡出）
const W=(t,a,b,fi=.4,fo=.4)=>Math.min(clamp((t-a)/fi),clamp((b-t)/fo));
function h(tag,cls,html,parent,style){const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;if(style)Object.assign(e.style,style);if(parent)parent.appendChild(e);return e;}
function svg(tag,attrs,parent){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e;}
// 设置元素的透明度/位移/缩放/旋转
function A(el,o){
  if(o.o!==undefined){el.style.opacity=o.o;el.style.visibility=o.o<=0.001?'hidden':'visible';}
  const x=o.x||0,y=o.y||0,s=o.s===undefined?1:o.s,r=o.r||0;
  el.style.transform=`translate(${x}px,${y}px) rotate(${r}deg) scale(${s})`;
}
// 常用入场：淡入+上移
function fin(el,t,t0,d=.6,dy=36){const p=P(t,t0,d);A(el,{o:p,y:(1-p)*dy});return p;}
function finout(el,t,a,b,d=.5,dy=30){const p=P(t,a,d),q=P(t,b-.4,.4,ease.in2);A(el,{o:p*(1-q),y:(1-p)*dy});}
// 盖章：从大到小砸下
function stamp(el,t,t0,rot=-4){const p=clamp((t-t0)/.22);const e=ease.in3(p);const s=lerp(2.6,1,e);
  const settle=t>t0+.22?1+0.04*Math.exp(-(t-t0-.22)*18)*Math.cos((t-t0-.22)*40):s;
  A(el,{o:p<=0?0:clamp(p*3),s:p<1?s:settle,r:rot});return p>=1;}
// 画面震动（盖章瞬间）
function shake(t,t0,amp=10){const dt=t-t0;if(dt<0||dt>.45)return [0,0];const k=amp*Math.exp(-dt*9);return [k*Math.sin(dt*70),k*Math.cos(dt*55)];}
// 把字符串拆成逐字 span（用于铅字逐字显现）
function chars(el,str,dots){el.innerHTML='';const out=[];let i=0;for(const ch of str){if(ch==='\n'){h('br',null,null,el);continue;}const s=h('span',dots&&dots.includes(i)?'dot':null,ch,el);out.push(s);i++;}return out;}
function reveal(spans,t,t0,dur){const n=spans.length;for(let i=0;i<n;i++){const st=t0+dur*i/n;const p=clamp((t-st)/.18);spans[i].style.opacity=p;spans[i].style.transform=`scale(${lerp(1.25,1,ease.out3(p))})`;}}
const C=id=>{const v=window.TIM[id];if(!v)throw new Error('no cue '+id);return v[0];};
const CE=id=>window.TIM[id][1];

const E={scenes:[],t:0,
  add(def){this.scenes.push(def);},
  boot(){
    const root=document.getElementById('scenes');
    this.scenes.sort((a,b)=>a.a-b.a);
    this.scenes.forEach((s,i)=>{s.el=h('div','scene',null,root);s.el.style.transformOrigin='540px 800px';s.el.style.zIndex=10+i;s.build(s.el,s);s.el.style.display='none';});
    this.hud=document.getElementById('hud');
    this.hud.innerHTML='<div class="bar"><i></i><span>背水一战 · 章士钊</span></div><div class="chap"></div>';
    this.sub=document.getElementById('subtext');
    this.buildSubs();
    this.duration=window.TIM._end[1];
    document.fonts.ready.then(()=>{this.ready=true;const q=new URLSearchParams(location.search);this.renderAt(parseFloat(q.get('t')||'0'));});
  },
  // 字幕：按标点把每句切成不超过 MAXC 字的行，按字数分配时长
  buildSubs(){
    const MAXC=16;this.subs=[];const PUN=/[，。；：？！、…「」“”《》]/;
    const vis=s=>[...s].filter(c=>!PUN.test(c)).length;
    for(const seg of window.SCRIPT){
      const [a,b]=window.TIM[seg.id];
      const txt=seg.t.replace(/……/g,'…');
      const toks=txt.split(/(?<=[，。；：？！、…])(?![」”])|(?<=[」”])(?=[^，。；：？！、…])/).filter(x=>x);
      let parts=[];let cur='';
      for(let tk of toks){
        while(vis(tk)>MAXC){const n=Math.ceil(vis(tk)/Math.ceil(vis(tk)/MAXC));let k=0,cnt=0;for(const ch of tk){if(!PUN.test(ch))cnt++;k+=ch.length;if(cnt>=n)break;}
          if(cur){parts.push(cur);cur='';}parts.push(tk.slice(0,k));tk=tk.slice(k);}
        if(cur&&vis(cur)+vis(tk)>MAXC){parts.push(cur);cur=tk;}else cur+=tk;
        if(/[。？！]」?$/.test(cur)&&vis(cur)>=7){parts.push(cur);cur='';}
      }
      if(cur)parts.push(cur);
      if(seg.sub)parts=seg.sub.slice();else
      for(let i=parts.length-1;i>0;i--){if(vis(parts[i])<=3&&vis(parts[i-1])+vis(parts[i])<=MAXC+1){parts[i-1]+=parts[i];parts.splice(i,1);}}
      const tot=parts.reduce((s,p)=>s+vis(p)+1.2,0);let t=a;
      let inq=false;
      for(const p of parts){const d=(b-a)*(vis(p)+1.2)/tot;
        const show=p.replace(/^[，。；：、]+/,'').replace(/[，。；、]+$/,'');
        const isq=inq||p.includes('「');if(p.includes('「'))inq=true;if(p.includes('」'))inq=false;
        this.subs.push({a:t,b:t+d,txt:show,k:isq?'q':'n',ch:seg.ch});t+=d;}
    }
  },
  renderAt(t){
    this.t=t;let top=null;
    for(const s of this.scenes){
      const fi=s.fi===undefined?.5:s.fi, fo=s.fo===undefined?0:s.fo;
      const vis=t>=s.a-0.001&&t<s.b+(s.hold===undefined?.6:s.hold);
      if(!vis){if(s.on){s.el.style.display='none';s.on=false;}continue;}
      if(!s.on){s.el.style.display='block';s.on=true;}
      let o=fi>0?clamp((t-s.a)/fi):1; if(fo>0)o=Math.min(o,clamp((s.b-t)/fo));
      s.el.style.opacity=o;
      if(!s.nokb){const kp=clamp((t-s.a)/Math.max(4,s.b-s.a));s.el.style.transform=`scale(${1+0.018*kp})`;}
      s.update(t,t-s.a,s);
      top=s;
    }
    // 顶栏明暗 + 章节名
    if(top){this.hud.className=top.dark?'ondark':'onlight';this.hud.style.opacity=top.nohud?0:1;
      this.hud.querySelector('.chap').textContent=top.chap||'';}
    // 字幕
    let cur=null;for(const s of this.subs){if(t>=s.a&&t<s.b){cur=s;break;}}
    if(cur){if(this.sub.textContent!==cur.txt)this.sub.textContent=cur.txt;this.sub.className=cur.k==='q'?'q':'';}
    else if(this.sub.textContent)this.sub.textContent='';
    if(top&&top.nosub)this.sub.textContent='';
    return true;
  }
};
window.renderAt=t=>E.renderAt(t);
