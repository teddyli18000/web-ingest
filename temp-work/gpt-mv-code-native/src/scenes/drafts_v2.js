import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderOpeningV8} from './opening_v8.js';

const T0=15,T1=18.3,T2=21.6,T3=25.2,END=30;
const MAP={x:650,y:126,w:1120,h:760};

function art(d,model,dst,{crop='full',alpha=1,register=0,flip=false,rot=0,cover=false}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha,flip,rot});
  else model.draw(d.g,dst,{crop,alpha,flip,rot,cover});
}
function warmBase(d,t,{blue=.055,gold=.10}={}){
  d.paper(t*.29);
  d.glow(1520,240,620,P.gold,gold);
  d.glow(390,760,650,P.cobalt,blue);
  d.gradRect(0,780,1920,300,[[0,'rgba(23,32,51,0)'],[1,'rgba(23,32,51,.055)']],true);
}
function proof(d,x,y,w,h,{rot=0,alpha=1,shadow=.26,blue=false}={}){
  d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));
    d.rrect(x+16,y+20,w,h,18,{fill:P.ink,alpha:.045*alpha});
    d.rrect(x,y,w,h,18,{fill:blue?'rgba(239,244,255,.965)':'rgba(255,253,248,.975)',stroke:'rgba(53,65,92,.18)',width:1.6,alpha,shadow:shadow*alpha});
    d.line(x+30,y+38,x+w-34,y+38,{color:blue?P.cobalt:P.gold,width:5,alpha:.48*alpha});
  });
}
function cropMarks(d,x,y,w,h,a=.34){
  const m=13,l=28,c=P.ink2;
  for(const [px,py,sx,sy] of [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){
    d.line(px-sx*m,py,px+sx*l,py,{color:c,width:1.7,alpha:a});
    d.line(px,py-sy*m,px,py+sy*l,{color:c,width:1.7,alpha:a});
  }
}
function point(d,x,y,{color=P.gold,a=1,r=10,halo=34}={}){
  d.glow(x,y,halo*3,color,.15*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,halo,{fill:null,stroke:color,width:2,alpha:.36*a});
}
function paperBridge(d,a,{wrong=1,ghost=0}={}){
  const start={x:775,y:715},bad={x:1430,y:330},good={x:1560,y:715};
  const target={x:lerp(good.x,bad.x,wrong),y:lerp(good.y,bad.y,wrong)};
  for(let i=0;i<8;i++){
    const q=easeOut(prog(a,i*.065,.48+i*.065));if(q<=0)continue;
    const u=i/7,x=lerp(start.x,target.x,u),y=lerp(start.y,target.y,u)-Math.sin(u*Math.PI)*56;
    d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.14,.08,u));d.rrect(-55*q,-18,110*q,36,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1.2,alpha:(.92-.54*ghost)*q,shadow:.12*(1-ghost)});});
  }
  return {start,bad,good};
}
function routeInk(d,{ox=0,oy=0,a=1,color=P.cobalt,wrong=.35,width=5}={}){
  const pts=[[780,705],[925,612],[1060,655],[1190,535],[1320,585],[lerp(1560,1430,wrong),lerp(715,330,wrong)]];
  for(let i=0;i<pts.length-1;i++){
    const p=pts[i],q=pts[i+1];d.line(p[0]+ox,p[1]+oy,q[0]+ox,q[1]+oy,{color,width,alpha:a*(.72-.055*i)});
  }
}
function foregroundSweep(d,t){
  for(let i=0;i<2;i++){
    const q=prog(t,T1+.35+i*.30,T2-.25+i*.18);if(q<=0||q>=1)continue;
    d.save(()=>{d.g.translate(lerp(2040,-620,easeInOut(q)),885-i*190);d.g.rotate(-.13+i*.07);d.rrect(0,0,520,180,14,{fill:P.white,stroke:P.line,width:1.3,alpha:.92,shadow:.32});d.line(34,45,405,45,{color:i?P.cobalt:P.gold,width:7,alpha:.50});});
  }
}

function shotWipe(d,t,model){
  // Freeze the exact last opening composition under a moving foreground sheet.
  renderOpeningV8(d,14.999,model);
  const q=easeInOut(prog(t,T0,T0+1.22));
  if(q>0){
    d.save(()=>{
      const x=lerp(-520,-160,q),y=lerp(820,-170,q),w=2380,h=1420;
      d.g.translate(x+w/2,y+h/2);d.g.rotate(lerp(-.16,-.035,q));d.g.translate(-(x+w/2),-(y+h/2));
      d.rrect(x,y,w,h,34,{fill:P.white,stroke:'rgba(53,65,92,.15)',width:2,shadow:.55});
      d.line(x+120,y+105,x+w-180,y+105,{color:P.gold,width:8,alpha:.48});
      for(let r=0;r<4;r++)d.rrect(x+140,y+220+r*92,lerp(680,1320,r/3),14,7,{fill:P.line,alpha:.16});
    });
  }
  const reveal=smooth(prog(q,.58,1));
  if(reveal>0){
    d.alpha(reveal,()=>{warmBase(d,t,{blue:.04,gold:.12});proof(d,MAP.x,MAP.y,MAP.w,MAP.h,{shadow:.28});cropMarks(d,MAP.x,MAP.y,MAP.w,MAP.h,.26);});
    // Same source artwork, now a close editorial crop rather than a mascot swap.
    d.save(()=>{d.g.beginPath();d.g.rect(0,0,650,1080);d.g.clip();art(d,model,{x:-330,y:95,w:1040,h:970},{crop:'bust',alpha:reveal,register:5});});
    d.text('revision / 01',MAP.x+48,MAP.y+94,{size:24,font:'mono',weight:700,color:P.ink2,alpha:.48*reveal});
  }
  const build=easeOut(prog(t,T0+1.05,T1));
  if(build>0){
    point(d,775,715,{color:P.cobalt,a:build,r:9,halo:27});
    const g=paperBridge(d,build,{wrong:1});
    point(d,g.bad.x,g.bad.y,{color:P.gold,a:build,r:10,halo:31});
    d.text('first reading',1280,276,{size:28,font:'serif',italic:true,color:P.ink2,alpha:.47*build});
  }
}

function shotMisread(d,t,model){
  const u=prog(t,T1,T2);warmBase(d,t,{blue:.055,gold:.11});proof(d,MAP.x,MAP.y,MAP.w,MAP.h,{shadow:.30});cropMarks(d,MAP.x,MAP.y,MAP.w,MAP.h,.30);
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,640,1080);d.g.clip();art(d,model,{x:-350,y:55,w:1080,h:1010},{crop:'bust',register:5});});
  d.text('revision / 01',MAP.x+48,MAP.y+94,{size:24,font:'mono',weight:700,color:P.ink2,alpha:.48});
  const g=paperBridge(d,1,{wrong:1});point(d,g.start.x,g.start.y,{color:P.cobalt,a:1,r:9,halo:26});point(d,g.bad.x,g.bad.y,{color:P.gold,a:1,r:10,halo:31});
  const notice=easeOut(prog(t,T1+.65,T1+1.45));
  if(notice>0){
    // User correction is one concrete mark, not a red-alert lighting state.
    point(d,g.good.x,g.good.y,{color:P.coral,a:notice,r:9,halo:30});
    const ring=easeOut(prog(t,T1+.78,T1+1.38));d.circle(g.bad.x,g.bad.y,68,{fill:null,stroke:P.coral,width:5,alpha:.62*ring});
    const arrow=easeOut(prog(t,T1+1.05,T1+1.90));d.line(g.bad.x+52,g.bad.y+52,lerp(g.bad.x+52,g.good.x-28,arrow),lerp(g.bad.y+52,g.good.y-28,arrow),{color:P.coral,width:5,alpha:.72*arrow});
  }
  const understand=easeOut(prog(t,T1+1.65,T2-.15));
  if(understand>0){
    d.text('not there.',1285,255,{size:31,font:'serif',italic:true,color:P.coral,alpha:.67*understand});
    // A hand detail enters on top of the proof: human scale and clear depth plane.
    d.save(()=>{d.g.beginPath();d.g.rect(1050,470,870,610);d.g.clip();art(d,model,{x:930,y:390,w:950,h:700},{crop:'hand',alpha:.90*understand,register:4});});
  }
  foregroundSweep(d,t);
}

function traceLayer(d,i,t,align){
  const offsets=[[-70,35,-.055],[35,-48,.042],[88,48,-.025]],o=offsets[i],x=470+lerp(o[0],0,align),y=160+lerp(o[1],0,align),rot=lerp(o[2],0,align),w=1150,h=720;
  d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));
    d.rrect(x,y,w,h,16,{fill:i===1?'rgba(238,244,255,.72)':'rgba(255,253,248,.72)',stroke:i===0?P.coral:i===1?P.cobalt:P.gold,width:2,alpha:.70,shadow:.16});
    const wrong=i===0?.92:i===1?.48:.18;routeInk(d,{ox:x-470,oy:y-160,a:.52,color:i===0?P.coral:i===1?P.cobalt:P.gold,wrong,width:i===2?6:4});
    d.line(x+40,y+54,x+330,y+54,{color:i===0?P.coral:i===1?P.cobalt:P.gold,width:6,alpha:.50});
  });
  cropMarks(d,x,y,w,h,.18);
}
function shotTrace(d,t,model){
  const u=prog(t,T2,T3),align=easeInOut(prog(t,T2+.65,T3-.52));warmBase(d,t,{blue:.075,gold:.08});
  d.text('keep the evidence.',105,142,{size:43,font:'serif',italic:true,color:P.ink,alpha:.72});
  d.text('three passes · one correction',108,184,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.42});
  for(let i=0;i<3;i++)traceLayer(d,i,t,align);
  // The correction point stays fixed while the layers move around it.
  point(d,1560,715,{color:lerpColor(P.coral,P.gold,align),a:.95,r:9,halo:32});
  const hand=easeOut(prog(t,T2+.25,T2+1.05));if(hand>0){d.save(()=>{d.g.beginPath();d.g.rect(0,390,620,690);d.g.clip();art(d,model,{x:-300,y:350,w:1040,h:770},{crop:'hand',alpha:.94*hand,register:4});});}
  const reg=easeOut(prog(t,T3-.95,T3-.18));if(reg>0){for(let i=0;i<4;i++)d.circle(470+i*380,925,lerp(20,5,reg),{fill:null,stroke:i%2?P.gold:P.cobalt,width:2,alpha:.42*(1-reg)});}
}
function lerpColor(a,b,k){
  const parse=s=>s.match(/[0-9a-f]{2}/ig).map(v=>parseInt(v,16)),aa=parse(a),bb=parse(b),c=aa.map((v,i)=>Math.round(lerp(v,bb[i],k)).toString(16).padStart(2,'0'));return `#${c.join('')}`;
}

function shotFinal(d,t,model){
  const u=prog(t,T3,END),settle=easeOut(prog(t,T3,T3+.90));warmBase(d,t,{blue:.045,gold:.16});
  // One clean page owns the middle distance; old route remains as a graphite ghost.
  const px=265,py=170,pw=1120,ph=720;proof(d,px,py,pw,ph,{rot:lerp(-.018,0,settle),shadow:.30});cropMarks(d,px,py,pw,ph,.24);
  routeInk(d,{ox:px-470,oy:py-160,a:.12,color:P.ink2,wrong:.92,width:3});
  const clean=easeOut(prog(t,T3+.28,T3+1.48));routeInk(d,{ox:px-470,oy:py-160,a:.70*clean,color:P.cobalt,wrong:0,width:6});
  point(d,575,725,{color:P.cobalt,a:clean,r:9,halo:28});point(d,1355,725,{color:P.gold,a:clean,r:10,halo:32});
  d.text('revision / final',px+44,py+76,{size:22,font:'mono',weight:700,color:P.ink2,alpha:.42});
  const words=easeOut(prog(t,T3+1.05,T3+2.05));d.text('keep what matters.',px+70,py+170,{size:54,font:'serif',italic:true,color:P.ink,alpha:.80*words});
  d.line(px+72,py+196,px+72+470*words,py+196,{color:P.gold,width:5,alpha:.54*words});

  // Character is in front of the page but behind the near-lens paper: stable three-plane depth.
  const enter=easeOut(prog(t,T3+.20,T3+1.12));art(d,model,{x:1120+18*(1-enter),y:95,w:820,h:920},{crop:'full',alpha:enter,register:6});
  const user=easeOut(prog(t,T3+1.25,T3+1.95));if(user>0)point(d,975,770,{color:P.gold,a:user,r:9,halo:30});
  const link=easeOut(prog(t,T3+1.48,T3+2.55));if(link>0){for(let i=0;i<5;i++){const q=easeOut(prog(link,i*.09,.45+i*.09)),x=lerp(1260,995,i/4),y=lerp(680,770,i/4)-Math.sin(i/4*Math.PI)*35;d.save(()=>{d.g.translate(x,y);d.g.rotate(-.08+i*.025);d.rrect(-42*q,-13,84*q,26,4,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.88*q});});}}

  for(let i=0;i<2;i++){const q=prog(t,T3+.55+i*.28,END-.20+i*.08);if(q>0&&q<1)d.save(()=>{d.g.translate(lerp(-520,2050,easeInOut(q)),905-i*165);d.g.rotate(-.14+i*.08);d.rrect(0,0,430,155,12,{fill:P.white,stroke:P.line,width:1.2,alpha:.90,shadow:.32});d.line(32,40,330,40,{color:i?P.cobalt:P.gold,width:6,alpha:.52});});}
  const quiet=easeOut(prog(t,28.75,29.70));d.text('still revisable.',150,998,{size:26,font:'serif',italic:true,color:P.ink2,alpha:.48*quiet});
}

export function renderDraftsV2(d,t,model){
  if(t<T1)return shotWipe(d,t,model);
  if(t<T2)return shotMisread(d,t,model);
  if(t<T3)return shotTrace(d,t,model);
  return shotFinal(d,t,model);
}

export const DRAFTS_V2_CUTS=[T0,T1,T2,T3,END];
