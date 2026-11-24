// ---- reusable graphics ----
function nameTag(s,name,role,x,y,tin,tout){const e=s.add('div',`left:${x}px;top:${y}px`,'tag',`<div class="n">${name}</div><div class="r">${role}</div>`);s.io(e,tin,tout,{y:0,x:-30});return e}
function defCard(s,term,text,x,y,w,tin,tout){const e=s.add('div',`left:${x}px;top:${y}px;width:${w}px`,'def',`<b>${term}</b><br>${text}`);s.io(e,tin,tout,{y:0,x:-24});return e}
// line map (Natural Earth, public domain). view(cx,cy,k): centre in map units, k px per unit
function MapView(s,x,y,w,h,o={}){
  const sv=svg(w,h,`left:${x}px;top:${y}px;overflow:hidden;-webkit-mask-image:linear-gradient(transparent,#000 14%,#000 86%,transparent)`);
  sv.innerHTML=`<g class="mv"><path d="${MAP.land}" fill="${o.fill||'rgba(143,191,227,.07)'}" stroke="${o.stroke||'#8fbfe3'}" stroke-width="${o.sw||1.6}" vector-effect="non-scaling-stroke" stroke-linejoin="round"/><path d="${MAP.yangtze}" fill="none" stroke="${o.stroke||'#8fbfe3'}" stroke-width="${(o.sw||1.6)*.8}" opacity=".7" vector-effect="non-scaling-stroke"/></g>`;
  s.add(sv);const g=sv.querySelector('.mv');const m={sv,w,h,cx:0,cy:0,k:1,marks:[],
    view(cx,cy,k){m.cx=cx;m.cy=cy;m.k=k;g.setAttribute('transform',`translate(${w/2},${h/2}) scale(${k}) translate(${-cx},${-cy})`);for(const f of m.marks)f()},
    px(p){const q=typeof p==='string'?MAP.places[p]:p;return[w/2+(q[0]-m.cx)*m.k,h/2+(q[1]-m.cy)*m.k]},
    // marker: dot + label; side: 'r','l','t','b'
    mark(place,label,tin,tout,q={}){const col=q.col||'#ff7a1a';const d=el('div','abs',`left:${x}px;top:${y}px;width:0;height:0`);
      const side=q.side||'r';const lp={r:'left:20px;top:-24px',l:'right:20px;top:-24px',t:'left:-100px;width:200px;text-align:center;bottom:22px',b:'left:-100px;width:200px;text-align:center;top:20px'}[side];
      d.innerHTML=`<div class="abs" style="left:-9px;top:-9px;width:18px;height:18px;border-radius:50%;background:${col};box-shadow:0 0 0 5px ${col}33"></div><div class="abs pulse" style="left:-9px;top:-9px;width:18px;height:18px;border-radius:50%;border:2px solid ${col}"></div><div class="abs serif" style="${lp};white-space:nowrap;font-size:${q.fs||38}px;line-height:1.2;color:${q.tc||'#f1ede4'};text-shadow:0 2px 10px #0009">${label}${q.sub?`<div class="mono" style="font-size:22px;color:${q.sc||'#9fb4c6'};letter-spacing:.06em;font-weight:500">${q.sub}</div>`:''}</div>`;
      s.add(d);const pu=d.querySelector('.pulse');s.io(d,tin,tout,{y:0});const up=()=>{const p=m.px(place);d.style.left=(x+p[0])+'px';d.style.top=(y+p[1])+'px'};m.marks.push(up);up();
      s.on(t=>{const u=((t-tin)%1.8)/1.8;pu.style.transform=`scale(${1+u*2.2})`;pu.style.opacity=(t<tin?0:1-u)});return d},
    // dashed route between two places, drawn on from tin over dur
    route(a,b,tin,dur,q={}){const pth=document.createElementNS(NS,'path');pth.setAttribute('fill','none');pth.setAttribute('stroke',q.col||'#ff7a1a');pth.setAttribute('stroke-width',q.sw||3);pth.setAttribute('stroke-linecap','round');sv.appendChild(pth);
      const upd=()=>{const A=m.px(a),B=m.px(b);const mx=(A[0]+B[0])/2,my=(A[1]+B[1])/2-(q.arc??.18)*Math.hypot(B[0]-A[0],B[1]-A[1]);pth.setAttribute('d',`M${A[0]},${A[1]} Q${mx},${my} ${B[0]},${B[1]}`);pth._len=pth.getTotalLength()};
      m.marks.push(upd);upd();s.on(t=>{const L=pth._len||1;const p=E.io(P(t,tin,tin+dur));pth.style.strokeDasharray=`${L*p} ${L}`;pth.style.opacity=(q.tout?1-P(t,q.tout,q.tout+.4):1)*(p>0?1:0)});return pth}};
  return m}
// blast furnace line drawing, local coords: ground centre (0,0), up = -y, roughly x∈[-470,470], y∈[-670,0]
function furnaceParts(){
  const stove=x=>`M${x-32},0 L${x-32},-330 A32,36 0 0 1 ${x+32},-330 L${x+32},0 M${x-32},-110 L${x+32},-110 M${x-32},-220 L${x+32},-220 M${x-32},-330 L${x+32},-330`;
  const brace=(y0,y1)=>`M-128,${y0} L128,${y1} M128,${y0} L-128,${y1}`;
  return {
   ground:'M-520,0 L520,0',
   shell:'M-78,0 L-78,-70 L-100,-130 L-100,-175 L-58,-400 L-58,-440 L-30,-475 L-30,-500 L30,-500 L30,-475 L58,-440 L58,-400 L100,-175 L100,-130 L78,-70 L78,0',
   bands:'M-78,-70 L78,-70 M-100,-130 L100,-130 M-100,-175 L100,-175 M-86,-250 L86,-250 M-72,-325 L72,-325 M-58,-400 L58,-400 M-58,-440 L58,-440',
   bustle:'M-128,-152 A128,17 0 0 0 128,-152 M-128,-152 A128,17 0 0 1 128,-152 M-96,-140 L-84,-112 M-48,-136 L-42,-108 M0,-135 L0,-106 M48,-136 L42,-108 M96,-140 L84,-112',
   uptake:'M-22,-500 L-50,-592 L0,-642 L50,-592 L22,-500 M0,-642 L0,-672 M-10,-672 L10,-672',
   downcomer:'M22,-622 L236,-372 M46,-598 L262,-350',
   dust:'M222,-360 L300,-360 L300,-232 L261,-168 L222,-232 Z M222,-232 L300,-232 M261,-168 L261,-120 M232,-120 L290,-120 M236,-216 L236,0 M286,-216 L286,0',
   stoves:stove(-215)+' '+stove(-295)+' '+stove(-375),
   main:'M-183,-150 L-128,-150 M-183,-166 L-128,-166 M-407,-60 L-183,-60 M-407,-76 L-183,-76',
   chimney:'M-462,0 L-456,-600 L-436,-600 L-430,0 M-458,-420 L-434,-420',
   frame:'M-128,-70 L-128,-520 M128,-70 L128,-520 M-128,-520 L128,-520 M-128,-400 L128,-400 M-128,-290 L128,-290 M-128,-180 L128,-180 '+brace(-180,-290)+' '+brace(-290,-400)+' '+brace(-400,-520),
   skip:'M452,0 L60,-512 M478,0 L78,-492 M330,-160 L330,0 M356,-160 L356,0 M214,-312 L214,0 M240,-312 L240,0 M330,-80 L356,-80 M214,-150 L240,-150 M214,-230 L240,-230',
   house:'M-190,-70 L-160,-70 M160,-70 L190,-70 M-190,-70 L-190,0 M190,-70 L190,0 M-190,-70 L190,-70'}}
// add furnace to an svg <g>; returns map of path elements
function addFurnace(s,g,o={}){const parts=furnaceParts(),out={};const order=o.order||['ground','house','shell','bands','frame','bustle','uptake','downcomer','dust','stoves','main','chimney','skip'];
  order.forEach((k,i)=>{const p=document.createElementNS(NS,'path');p.setAttribute('d',parts[k]);p.setAttribute('class','ln');if(o.stroke)p.style.stroke=o.stroke;if(o.sw)p.style.strokeWidth=o.sw;
    if(k==='frame'||k==='bands')p.style.opacity=o.dim??.5;g.appendChild(p);out[k]=p;if(o.tin!=null)s.draw(p,o.tin+i*(o.stagger??.16),o.dur??1.1)});return out}
// crowd of tiny figures on canvas
function drawFigure(c,x,y,px,py){const r=px*.23;c.beginPath();c.arc(x+px/2,y+r+py*.06,r,0,6.2832);c.fill();const bw=px*.62,bh=py*.46;c.fillRect(x+(px-bw)/2,y+r*2+py*.1,bw,bh)}
// simple silhouettes (head+shoulders) for audiences
function drawHead(c,x,y,sz){c.beginPath();c.arc(x,y,sz*.34,0,6.2832);c.fill();c.beginPath();c.ellipse(x,y+sz*.86,sz*.62,sz*.5,0,Math.PI,0);c.fill()}
function canvas(s,w=W,h=H,style=''){const c=el('canvas','abs',`left:0;top:0;${style}`);c.width=w;c.height=h;s.add(c);return c}
// hen + egg icons (svg strings, 200x200 box)
const ICON={
 egg:c=>`<ellipse cx="100" cy="108" rx="54" ry="70" fill="none" stroke="${c}" stroke-width="7"/><path d="M70,86 Q78,60 100,52" fill="none" stroke="${c}" stroke-width="5" stroke-linecap="round" opacity=".6"/>`,
 hen:c=>`<g fill="none" stroke="${c}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"><path d="M38,96 Q30,52 62,40 Q60,22 76,24 Q82,10 94,22 Q108,16 108,34 Q122,46 118,70 Q150,78 168,56 Q186,40 180,76 Q192,84 176,100 Q170,150 112,152 Q52,152 38,96 Z"/><path d="M38,74 L16,82 L38,90"/><circle cx="66" cy="62" r="5" fill="${c}"/><path d="M92,152 L88,184 M88,184 L72,190 M88,184 L100,192 M124,152 L128,184 M128,184 L114,192 M128,184 L142,190"/><path d="M92,100 Q120,92 140,108 Q120,128 96,120"/></g>`}
