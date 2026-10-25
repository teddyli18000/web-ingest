import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV10} from './drafts_v10.js';

const T0=30,T1=33.45,T2=36.90,T3=40.80,END=45;
const INK='#172033',PAPER='#f7f2e8',PAPER2='#ebe4d6';

function poly(d,pts,{fill=PAPER,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(18,28,44,${.13*shadow})`;g.shadowBlur=34*shadow;g.shadowOffsetY=18*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function curve(d,pts,{color=P.cobalt,width=5,alpha=1}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],cx=(p[0]+n[0])/2;g.quadraticCurveTo(p[0],p[1],cx,(p[1]+n[1])/2);}const z=pts[pts.length-1];g.lineTo(z[0],z[1]);g.stroke();});
}
function paperField(d,t,{dark=.0}={}){d.paper(t*.22);d.glow(350,800,780,P.cobalt,.055);d.glow(1510,240,720,P.gold,.12);if(dark)d.gradRect(0,0,1920,1080,[[0,`rgba(23,32,51,${dark})`],[.45,'rgba(23,32,51,.02)'],[1,`rgba(23,32,51,${dark*.72})`]],false);}
function userMark(d,x,y,a=1){d.glow(x,y,150,P.gold,.20*a);d.circle(x,y,11,{fill:P.gold,alpha:a});d.circle(x,y,36,{fill:null,stroke:P.gold2,width:2,alpha:.42*a});}
function gptMark(d,x,y,a=1){d.glow(x,y,120,P.cobalt,.14*a);d.circle(x,y,9,{fill:P.cobalt,alpha:a});d.circle(x,y,29,{fill:null,stroke:P.cobalt2,width:2,alpha:.34*a});}
function art(d,model,dst,{crop='full',alpha=1,register=0,cover=false,rot=0}={}){if(register)model.register(d.g,dst,{crop,spread:register,alpha,rot});else model.draw(d.g,dst,{crop,alpha,cover,rot});}

const MAP=[[170,895],[430,720],[720,795],[985,565],[1280,655],[1640,400]];
const GOLD=[[240,470],[520,540],[805,390],[1110,455],[1465,285]];
function mapQuad(){return [[85,170],[1740,95],[1880,870],[205,1015]];}
function mapSurface(d,t,{a=1,grid=1,route=1,gold=1,labels=1}={}){
  const q=mapQuad();poly(d,q,{fill:PAPER,stroke:'rgba(53,65,92,.18)',width:2,alpha:a,shadow:.48});
  if(grid){
    for(let i=1;i<9;i++){const u=i/9,ax=lerp(q[0][0],q[3][0],u),ay=lerp(q[0][1],q[3][1],u),bx=lerp(q[1][0],q[2][0],u),by=lerp(q[1][1],q[2][1],u);d.line(ax,ay,bx,by,{color:P.ink2,width:1.2,alpha:.075*a*grid});}
    for(let i=1;i<11;i++){const u=i/11,ax=lerp(q[0][0],q[1][0],u),ay=lerp(q[0][1],q[1][1],u),bx=lerp(q[3][0],q[2][0],u),by=lerp(q[3][1],q[2][1],u);d.line(ax,ay,bx,by,{color:P.cobalt,width:1.1,alpha:.052*a*grid});}
  }
  if(route){curve(d,MAP,{color:P.cobalt,width:7,alpha:.55*a*route});for(const [x,y] of MAP)d.circle(x,y,7,{fill:P.cobalt,alpha:.62*a*route});}
  if(gold){curve(d,GOLD,{color:P.gold,width:6,alpha:.46*a*gold});for(const [x,y] of GOLD)d.circle(x,y,6,{fill:P.gold,alpha:.58*a*gold});}
  if(labels){d.text('SHARED MAP / 01',140,235,{size:21,font:'mono',weight:700,color:P.ink2,alpha:.34*a*labels});d.text('route after revision',140,274,{size:34,font:'serif',italic:true,color:P.ink,alpha:.50*a*labels});}
}
function entrySheet(d,t){
  const q=easeInOut(prog(t,T0,T0+1.12));if(q<=0)return;
  const g=d.g,x=lerp(-1180,0,q),y=lerp(1160,0,q),rot=lerp(-.20,0,q),s=lerp(1.18,1,q);
  d.save(()=>{g.translate(960,540);g.rotate(rot);g.scale(s,s);g.translate(-960+x,-540+y);mapSurface(d,t,{a:1,grid:q,route:q,gold:.12*q,labels:.55*q});});
}
function entryRibbons(d,t){
  const q=easeOut(prog(t,T0+.45,T1-.18));if(q<=0)return;
  // Perspective paper ties that grow out of the same blue route used by the handoff.
  for(let i=0;i<10;i++){
    const u=i/9,k=easeOut(prog(q,i*.045,.46+i*.045));if(k<=0)continue;
    const x=lerp(300,1680,u),y=lerp(820,335,u)-Math.sin(u*Math.PI)*115;
    const w=lerp(150,64,u),h=lerp(46,24,u);
    d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.16,.08,u));d.rrect(-w*k/2,-h/2,w*k,h,6,{fill:i%3===0?P.gold2:P.white,stroke:P.line,width:1,alpha:.94*k,shadow:.16});});
  }
}
function shotEnter(d,t,model,poses){
  // Exact first frame inheritance from the accepted hand close-up.
  renderDraftsV10(d,29.999,model,poses);
  entrySheet(d,t);entryRibbons(d,t);
  const cap=easeOut(prog(t,T0+.72,T0+1.48))*(1-smooth(prog(t,T1-.72,T1-.12)));
  d.text('follow the correction.',118,144,{size:44,font:'serif',italic:true,color:P.ink,alpha:.54*cap});
  d.text('THE LINE LEAVES THE ANSWER',120,190,{size:19,font:'mono',weight:700,color:P.ink2,alpha:.30*cap});
}
function foldPanel(d,side,k,i=0){
  const q=mapQuad(),gold=i%2===1,fill=gold?'#f2e2a8':'#edf1fa';
  let pts;
  if(side==='left')pts=[[85,170],[205,1015],[lerp(205,-280,k),lerp(1015,875,k)],[lerp(85,-350,k),lerp(170,280,k)]];
  else if(side==='right')pts=[[1740,95],[1880,870],[lerp(1880,2200,k),lerp(870,750,k)],[lerp(1740,2160,k),lerp(95,225,k)]];
  else if(side==='top')pts=[[85,170],[1740,95],[lerp(1740,1600,k),lerp(95,-300,k)],[lerp(85,220,k),lerp(170,-260,k)]];
  else pts=[[205,1015],[1880,870],[lerp(1880,1730,k),lerp(870,1250,k)],[lerp(205,350,k),lerp(1015,1290,k)]];
  poly(d,pts,{fill,stroke:'rgba(53,65,92,.16)',width:1.5,alpha:.96,shadow:.23});
  const c=gold?P.gold:P.cobalt;const a=.18+.18*k;
  if(side==='left'||side==='right'){const x=side==='left'?lerp(155,-70,k):lerp(1810,2040,k);d.line(x,300,x,760,{color:c,width:7,alpha:a});}
  else{const y=side==='top'?lerp(140,-95,k):lerp(945,1130,k);d.line(430,y,1450,y,{color:c,width:7,alpha:a});}
}
function shotUnfold(d,t){
  paperField(d,t,{dark:.055});
  mapSurface(d,t,{a:1,grid:1,route:1,gold:1,labels:1});
  const sides=['left','right','top','bottom'];
  sides.forEach((s,i)=>foldPanel(d,s,easeInOut(prog(t,T1+.08+i*.18,T1+.90+i*.18)),i));
  const user=easeOut(prog(t,T1+.35,T1+1.10));userMark(d,240,470,user);
  const gp=easeOut(prog(t,T1+.68,T1+1.34));gptMark(d,1640,400,gp);
  // A translucent tracing page crosses near-lens: third depth plane, not random particles.
  const fg=prog(t,T1+.58,T2-.30);if(fg>0&&fg<1)d.save(()=>{d.g.translate(lerp(1980,-560,easeInOut(fg)),780);d.g.rotate(-.095);d.rrect(0,0,650,240,17,{fill:'rgba(241,246,255,.92)',stroke:P.line,width:1.2,alpha:.94,shadow:.35});d.line(42,54,520,54,{color:P.cobalt,width:8,alpha:.48});d.text('overlay / shared',46,104,{size:24,font:'mono',color:P.ink2,alpha:.36});});
  const cap=easeOut(prog(t,T1+.82,T1+1.52));d.text('two marks. one surface.',1280,970,{size:34,font:'serif',italic:true,align:'center',color:P.ink,alpha:.48*cap});
}
function riser(d,x,y,w,h,k,{gold=false,lean=0}={}){
  const H=h*k,top=y-H,c=gold?P.gold:P.cobalt;
  poly(d,[[x,y],[x+w,y],[x+w+lean,top],[x+lean,top]],{fill:gold?'#efe3af':'#e9edf7',stroke:'rgba(53,65,92,.17)',width:1.2,alpha:.98,shadow:.18});
  poly(d,[[x+w,y],[x+w+lean,top],[x+w+lean+18,top+14],[x+w+18,y+16]],{fill:INK,alpha:.075*k});
  d.line(x+lean+18,top+28,x+lean+w-16,top+28,{color:c,width:5,alpha:.42*k});
  for(let i=0;i<3;i++)d.line(x+lean+22,top+58+i*27,x+lean+w*(.62-i*.08),top+58+i*27,{color:P.ink2,width:5,alpha:.12*k});
}
function bridge(d,t){
  const k=easeOut(prog(t,T2+.65,T3-.35));if(k<=0)return;
  const from=[500,700],to=[1490,410],N=13;
  for(let i=0;i<N;i++){
    const u=i/(N-1),q=easeOut(prog(k,i*.045,.44+i*.045));if(q<=0)continue;
    const x=lerp(from[0],to[0],u),y=lerp(from[1],to[1],u)-Math.sin(u*Math.PI)*155;
    const sc=lerp(1.28,.72,u);d.save(()=>{d.g.translate(x,y);d.g.rotate(-.28+u*.42);d.rrect(-62*sc*q,-20*sc,124*sc*q,40*sc,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.97*q,shadow:.22});});
  }
  curve(d,[[500,700],[720,525],[990,475],[1240,400],[1490,410]],{color:P.cobalt,width:5,alpha:.25*k});
}
function shotBuild(d,t){
  paperField(d,t,{dark:.075});mapSurface(d,t,{a:1,grid:.75,route:.42,gold:.42,labels:.35});
  const bases=[[370,780,170,210,false,-20],[590,680,190,300,true,10],[850,715,155,250,false,-8],[1080,590,205,340,false,16],[1375,520,165,270,true,-12]];
  bases.forEach((v,i)=>riser(d,v[0],v[1],v[2],v[3],easeOut(prog(t,T2+.10+i*.16,T2+.92+i*.16)),{gold:v[4],lean:v[5]}));
  bridge(d,t);
  userMark(d,430,720,easeOut(prog(t,T2+.38,T2+.95)));gptMark(d,1535,410,easeOut(prog(t,T2+.62,T2+1.12)));
  // Drafting ruler sweeps foreground and motivates the next camera change.
  const r=prog(t,T2+1.15,T3+.18);if(r>0&&r<1)d.save(()=>{d.g.translate(lerp(-600,2050,easeInOut(r)),950);d.g.rotate(-.115);d.rrect(0,0,820,118,10,{fill:'#fffdf8',stroke:P.line,width:1.2,alpha:.96,shadow:.35});for(let i=0;i<15;i++)d.line(42+i*48,18,42+i*48,18+(i%5===0?42:24),{color:P.ink2,width:2,alpha:.24});});
  const cap=easeOut(prog(t,T2+.95,T2+1.58));d.text('the correction becomes structure.',105,145,{size:42,font:'serif',italic:true,color:P.white,alpha:.72*cap});
}
function finalFlap(d,t){
  const q=easeInOut(prog(t,END-.72,END));if(q<=0)return;
  const y=lerp(1170,220,q),h=980;
  poly(d,[[-80,y],[2010,y-115],[2010,y+h],[-80,y+h+70]],{fill:'#fffdf8',stroke:'rgba(53,65,92,.16)',width:2,alpha:.995,shadow:.45});
  d.line(120,y+105,1640,y+18,{color:P.cobalt,width:7,alpha:.30});d.text('NEXT PROOF',132,y+185,{size:24,font:'mono',weight:700,color:P.ink2,alpha:.30});
}
function shotTogether(d,t,model){
  paperField(d,t,{dark:.10});
  // Slight pull-back: completed map becomes a stage rather than another flat card.
  d.save(()=>{d.g.translate(960,540);const z=lerp(1.04,.88,easeInOut(prog(t,T3,T3+1.05)));d.g.scale(z,z);d.g.translate(-960,-540);mapSurface(d,t,{a:1,grid:.55,route:.30,gold:.30,labels:0});const bases=[[370,780,170,210,false,-20],[590,680,190,300,true,10],[850,715,155,250,false,-8],[1080,590,205,340,false,16],[1375,520,165,270,true,-12]];bases.forEach(v=>riser(d,v[0],v[1],v[2],v[3],1,{gold:v[4],lean:v[5]}));bridge(d,T3-.001);});
  // Character is revealed by the map edge, not faded in.
  const reveal=easeInOut(prog(t,T3+.28,T3+1.10));
  d.save(()=>{const g=d.g;g.beginPath();g.rect(lerp(1920,1110,reveal),0,900,1080);g.clip();art(d,model,{x:1080,y:5,w:900,h:1040},{crop:'full',alpha:1,register:5});});
  const user=easeOut(prog(t,T3+.45,T3+1.05)),gp=easeOut(prog(t,T3+.65,T3+1.22));userMark(d,400,755,user);gptMark(d,1450,410,gp);
  const join=easeOut(prog(t,T3+.82,T3+2.02));paperBridgeMini(d,[445,735],[1395,425],join);
  const end=easeOut(prog(t,T3+1.45,T3+2.25));d.text('SHARED CONSTRUCTION / 01',92,975,{size:20,font:'mono',weight:700,color:P.white,alpha:.30*end});
  finalFlap(d,t);
}
function paperBridgeMini(d,a,b,k){
  for(let i=0;i<10;i++){const u=i/9,q=easeOut(prog(k,i*.055,.38+i*.055));if(q<=0)continue;const x=lerp(a[0],b[0],u),y=lerp(a[1],b[1],u)-Math.sin(u*Math.PI)*145;d.save(()=>{d.g.translate(x,y);d.g.rotate(-.20+u*.30);d.rrect(-50*q,-15,100*q,30,4,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.95*q,shadow:.12});});}
}

export function renderConstructV1(d,t,model,poses){
  if(t<T1)return shotEnter(d,t,model,poses);
  if(t<T2)return shotUnfold(d,t);
  if(t<T3)return shotBuild(d,t);
  return shotTogether(d,t,model);
}

export const CONSTRUCT_V1_CUTS=[T0,T1,T2,T3,END];
