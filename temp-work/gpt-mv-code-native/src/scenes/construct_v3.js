import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV10} from './drafts_v10.js';

const T0=30,T1=33.05,T2=36.10,T3=40.55,END=45;
const SKY='#151c2c',SKY2='#27324a',FLOOR='#d9d0c0',FLOOR2='#ece4d5',INK='#172033',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f',RED='#d94b3d';

function poly(d,pts,{fill=FLOOR2,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(3,8,18,${.30*shadow})`;g.shadowBlur=34*shadow;g.shadowOffsetY=18*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function strokeCurve(d,pts,{color=BLUE,width=6,alpha=1}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],mx=(p[0]+n[0])/2,my=(p[1]+n[1])/2;g.quadraticCurveTo(p[0],p[1],mx,my);}const z=pts[pts.length-1];g.lineTo(z[0],z[1]);g.stroke();});
}
function mark(d,x,y,color,a=1,r=10){d.glow(x,y,120,color,.18*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,r*3,{fill:null,stroke:color,width:2,alpha:.34*a});}
function art(d,model,dst,{crop='hand',alpha=1,register=0,cover=false,rot=0}={}){if(register)model.register(d.g,dst,{crop,spread:register,alpha,rot});else model.draw(d.g,dst,{crop,alpha,cover,rot});}

function stage(d,t,{horizon=302}={}){
  d.rect(0,0,1920,1080,{fill:SKY});
  d.glow(260,210,630,BLUE,.16);d.glow(1590,235,650,GOLD,.105);
  d.gradRect(0,0,1920,horizon+60,[[0,'rgba(8,12,24,.08)'],[1,'rgba(8,12,24,.52)']],true);
  poly(d,[[0,horizon],[1920,horizon],[1920,1080],[0,1080]],{fill:FLOOR});
  // The map is the floor itself: no border, no floating sheet.
  const vp=[960,horizon-14];
  for(let i=0;i<=12;i++){
    const x=lerp(-260,2180,i/12);d.line(vp[0],vp[1],x,1080,{color:i%2?INK:BLUE,width:i%2?1.2:1.4,alpha:i%2?.075:.055});
  }
  for(let i=1;i<=9;i++){
    const u=i/10,y=lerp(horizon+18,1080,Math.pow(u,1.75));d.line(0,y,1920,y,{color:INK,width:1.25,alpha:.075*(1-u*.35)});
  }
  // Fold seams and subtle paper grain make this a physical floor, not a UI plane.
  d.line(0,665,1920,535,{color:INK,width:2,alpha:.10});
  d.line(560,horizon,840,1080,{color:INK,width:2,alpha:.08});
  d.line(1370,horizon,1190,1080,{color:GOLD,width:2,alpha:.07});
  d.save(()=>{const g=d.g;g.globalAlpha=.045;g.fillStyle=INK;for(let i=0;i<130;i++){const x=(i*167.3+t*11)%1920,y=horizon+((i*97.9+t*5)%(1080-horizon));g.fillRect(x,y,1+(i%5===0),1);}});
}

const BLUE_ROUTE=[[170,1030],[455,870],[760,765],[1050,670],[1320,555],[1660,430]];
const GOLD_ROUTE=[[1760,1015],[1510,870],[1240,785],[1035,705],[835,605],[655,510]];
function routes(d,{blue=1,gold=1,join=0}={}){
  strokeCurve(d,BLUE_ROUTE,{color:BLUE,width:8,alpha:.66*blue});
  strokeCurve(d,GOLD_ROUTE,{color:GOLD,width:7,alpha:.58*gold});
  BLUE_ROUTE.forEach((p,i)=>d.circle(p[0],p[1],i===0?9:6,{fill:BLUE,alpha:.72*blue}));
  GOLD_ROUTE.forEach((p,i)=>d.circle(p[0],p[1],i===0?9:6,{fill:GOLD,alpha:.68*gold}));
  if(join>0){d.glow(1035,705,190,BLUE,.14*join);d.glow(1035,705,150,GOLD,.12*join);d.circle(1035,705,16,{fill:FLOOR2,stroke:BLUE,width:4,alpha:join});d.circle(1035,705,8,{fill:GOLD,alpha:join});}
}

function foldedArch(d,cx,base,w,h,k,{accent=BLUE,depth=34,front=FLOOR2,side='#b9b2a7'}={}){
  if(k<=0)return;const H=h*k,top=base-H,g=d.g;
  // Side face first: this is an object in space, not a card.
  poly(d,[[cx+w/2,base],[cx+w/2+depth,base-18],[cx+w/2+depth,top-18],[cx+w/2,top]],{fill:side,stroke:'rgba(23,32,51,.20)',width:1.2,shadow:.18});
  d.save(()=>{
    const path=new Path2D();
    path.moveTo(cx-w/2,base);path.lineTo(cx-w*.45,top+H*.22);path.quadraticCurveTo(cx,top-H*.035,cx+w*.45,top+H*.22);path.lineTo(cx+w/2,base);path.closePath();
    const hole=new Path2D();const hw=w*.21;hole.moveTo(cx-hw,base);hole.lineTo(cx-hw,top+H*.58);hole.quadraticCurveTo(cx,top+H*.33,cx+hw,top+H*.58);hole.lineTo(cx+hw,base);hole.closePath();
    path.addPath(hole);g.globalAlpha=.995;g.fillStyle=front;g.fill(path,'evenodd');g.strokeStyle='rgba(23,32,51,.22)';g.lineWidth=1.5;g.stroke(path);
  });
  d.line(cx-w*.29,top+H*.30,cx+w*.29,top+H*.30,{color:accent,width:6,alpha:.52});
  d.line(cx-w*.34,base-22,cx+w*.36,base-22,{color:INK,width:2,alpha:.13});
}
function foldedSteps(d,x,base,w,h,k,{accent=GOLD,depth=28}={}){
  if(k<=0)return;const tiers=4;
  for(let i=0;i<tiers;i++){
    const u=i/(tiers-1),kk=easeOut(prog(k,u*.10,.64+u*.10));if(kk<=0)continue;
    const tw=w*(1-u*.13),th=h/tiers,ty=base-i*th*kk,tx=x+i*w*.08;
    poly(d,[[tx,ty],[tx+tw,ty],[tx+tw+depth,ty-14],[tx+depth,ty-14]],{fill:i%2?FLOOR2:'#e7decf',stroke:'rgba(23,32,51,.18)',alpha:.99,shadow:.14});
    poly(d,[[tx,ty],[tx+tw,ty],[tx+tw,ty-th*kk],[tx,ty-th*kk]],{fill:'#d1c8b8',stroke:'rgba(23,32,51,.16)',alpha:.99});
    d.line(tx+18,ty-th*kk+18,tx+tw*.78,ty-th*kk+18,{color:accent,width:4,alpha:.34});
  }
}
function foldedCanopy(d,cx,base,w,h,k,{accent=BLUE}={}){
  if(k<=0)return;const H=h*k,top=base-H;
  // Legs.
  poly(d,[[cx-w*.38,base],[cx-w*.30,base],[cx-w*.22,top+H*.26],[cx-w*.30,top+H*.26]],{fill:'#c8c0b2',stroke:'rgba(23,32,51,.18)',alpha:.98});
  poly(d,[[cx+w*.24,base],[cx+w*.32,base],[cx+w*.25,top+H*.26],[cx+w*.17,top+H*.26]],{fill:'#c8c0b2',stroke:'rgba(23,32,51,.18)',alpha:.98});
  // Folded roof with a visible underside.
  poly(d,[[cx-w*.52,top+H*.29],[cx,top],[cx+w*.52,top+H*.29],[cx,top+H*.42]],{fill:FLOOR2,stroke:'rgba(23,32,51,.21)',width:1.4,shadow:.22});
  poly(d,[[cx-w*.52,top+H*.29],[cx,top+H*.42],[cx,top+H*.50],[cx-w*.49,top+H*.37]],{fill:'#b8b1a5',stroke:'rgba(23,32,51,.14)',alpha:.95});
  d.line(cx-w*.32,top+H*.25,cx+w*.32,top+H*.25,{color:accent,width:5,alpha:.46});
}
function foldedBeacon(d,cx,base,w,h,k,{accent=GOLD}={}){
  if(k<=0)return;const H=h*k,top=base-H;
  poly(d,[[cx-w/2,base],[cx+w/2,base],[cx+w*.32,top],[cx-w*.32,top]],{fill:'#e2d9c9',stroke:'rgba(23,32,51,.20)',shadow:.16});
  poly(d,[[cx+w/2,base],[cx+w/2+26,base-14],[cx+w*.32+24,top-14],[cx+w*.32,top]],{fill:'#bdb5a8',stroke:'rgba(23,32,51,.15)'});
  poly(d,[[cx-w*.32,top],[cx+w*.32,top],[cx+w*.32+24,top-14],[cx-w*.32+22,top-14]],{fill:'#f1eadf',stroke:'rgba(23,32,51,.13)'});
  d.line(cx-w*.20,top+44,cx+w*.18,top+44,{color:accent,width:5,alpha:.48});
}

function bridgePath(u){
  const a=[385,895],b=[1535,585],x=lerp(a[0],b[0],u),y=lerp(a[1],b[1],u)-Math.sin(u*Math.PI)*145;return [x,y];
}
function bridge(d,k,{gap=false,final=0,foreground=false}={}){
  if(k<=0)return;const N=19;
  for(let i=0;i<N;i++){
    const u=i/(N-1);if(gap&&u>.45&&u<.57)continue;const q=easeOut(prog(k,i*.035,.45+i*.035));if(q<=0)continue;const p=bridgePath(u),n=bridgePath(Math.min(1,u+.025)),ang=Math.atan2(n[1]-p[1],n[0]-p[0]),sc=lerp(1.28,.70,u),w=136*sc*q,h=44*sc;
    d.save(()=>{d.g.translate(p[0],p[1]);d.g.rotate(ang);d.rrect(-w/2,-h/2,w,h,5,{fill:i%3===0?GOLD2:FLOOR2,stroke:'rgba(23,32,51,.22)',width:1.1,shadow:.26});d.line(-w*.30,0,w*.30,0,{color:i%3===0?GOLD:BLUE,width:3,alpha:.22});});
  }
  // Paper cable/crease, not a neon rail.
  const pts=[];for(let i=0;i<=16;i++)pts.push(bridgePath(i/16));strokeCurve(d,pts,{color:BLUE,width:5,alpha:.28*k});
  if(final>0){
    const p=bridgePath(.51),n=bridgePath(.535),ang=Math.atan2(n[1]-p[1],n[0]-p[0]);
    d.save(()=>{d.g.translate(p[0],p[1]);d.g.rotate(ang+lerp(-.75,0,easeOut(final)));d.rrect(-72*final,-27,144*final,54,6,{fill:'#fff8e4',stroke:BLUE,width:2,alpha:final,shadow:.38});d.line(-48*final,0,48*final,0,{color:GOLD,width:6,alpha:.65*final});});
  }
  if(foreground){
    // A cropped near plank crosses the lower frame to sell camera depth.
    const p=bridgePath(.06);d.save(()=>{d.g.translate(p[0]-170,p[1]+135);d.g.rotate(-.18);d.rrect(-250,-48,500,96,8,{fill:'#cfc6b7',stroke:'rgba(23,32,51,.18)',alpha:.98,shadow:.45});d.line(-190,0,190,0,{color:BLUE,width:5,alpha:.18});});
  }
}

function world(d,t,{structures=0,bridgeK=0,gap=false,final=0,hand=0}={}){
  const push=easeInOut(prog(t,T1,T2+.15));
  const horizon=lerp(330,258,push);stage(d,t,{horizon});
  d.save(()=>{
    const g=d.g;const s=lerp(.95,1.08,push),tx=lerp(35,-95,push),ty=lerp(20,6,push);g.translate(960+tx,540+ty);g.scale(s,s);g.translate(-960,-540);
    routes(d,{blue:1,gold:easeOut(prog(t,T1+.55,T2+.2)),join:easeOut(prog(t,T2-.20,T2+.65))});
    foldedBeacon(d,1510,575,125,240,easeOut(prog(structures,.02,.42)),{accent:GOLD});
    foldedCanopy(d,1205,704,320,360,easeOut(prog(structures,.12,.58)),{accent:BLUE});
    foldedSteps(d,610,845,330,390,easeOut(prog(structures,.22,.72)),{accent:GOLD});
    foldedArch(d,315,930,470,610,easeOut(prog(structures,.32,.82)),{accent:BLUE,depth:46,front:'#e7dfd2',side:'#aaa397'});
    foldedArch(d,945,770,300,390,easeOut(prog(structures,.42,.92)),{accent:GOLD,depth:34,front:'#ded6c9',side:'#afa89d'});
    // Hand enters before the foreground bridge and nearest architecture, so it lives inside the space.
    if(hand>0){
      const x=lerp(2050,1135,easeOut(hand)),y=lerp(390,255,easeOut(hand));art(d,arguments[0]._gptModel,{x,y,w:980,h:790},{crop:'hand',alpha:1,register:0,rot:-.028});
    }
    bridge(d,bridgeK,{gap,final,foreground:structures>.72});
    // Front-right fold partially occludes the arm and bridge.
    if(structures>.58)foldedSteps(d,1540,1050,430,520,easeOut(prog(structures,.58,1)),{accent:BLUE,depth:34});
  });
}

function entry(d,t,model,poses){
  // Underlay already contains the new low-angle space.
  d._gptModel=model;world(d,t,{structures:0,bridgeK:0});
  const k=easeInOut(prog(t,T0+.25,T1-.15));
  // Hold the previous final frame above a physical fold edge, then peel it upward.
  if(k<1){
    const edge=lerp(1180,-140,k);d.save(()=>{const g=d.g;g.beginPath();g.rect(0,0,1920,Math.max(0,edge));g.clip();renderDraftsV10(d,29.999,model,poses);});
    d.save(()=>{const g=d.g;g.translate(960,edge+12);g.rotate(-.018);poly(d,[[-1050,-18],[1050,-18],[1090,46],[-1090,52]],{fill:FLOOR2,stroke:'rgba(23,32,51,.20)',width:1.2,shadow:.48});d.line(-820,6,780,6,{color:BLUE,width:7,alpha:.36});d.line(-250,28,460,28,{color:GOLD,width:4,alpha:.24});});
  }
  // The blue correction line visibly continues across the fold into the floor.
  const pull=easeOut(prog(t,T0+.12,T0+1.12));strokeCurve(d,[[765,725],[650,760],[520,825],[385,900]],{color:BLUE,width:8,alpha:.52*pull});
}
function dive(d,t,model){d._gptModel=model;const s=easeOut(prog(t,T1+.22,T2+.05));world(d,t,{structures:s*.20,bridgeK:0});
  const seam=easeOut(prog(t,T1+.38,T1+1.15));if(seam>0){mark(d,170,1030,BLUE,seam,9);mark(d,1760,1015,GOLD,seam,9);}
}
function build(d,t,model){d._gptModel=model;const s=easeOut(prog(t,T2+.05,T3-.38)),bk=easeOut(prog(t,T2+.95,T3-.18));world(d,t,{structures:s,bridgeK:bk,gap:true});
  const trace=easeOut(prog(t,T2+.55,T2+1.42));if(trace>0){d.text('from plan to place',116,158,{size:24,font:'mono',weight:700,color:'#dfe6f5',alpha:.34*trace});d.text('make it hold.',114,207,{size:42,font:'serif',italic:true,color:'#f2eadf',alpha:.58*trace});}
}
function join(d,t,model){d._gptModel=model;const h=easeOut(prog(t,T3+.18,T3+1.22)),f=easeOut(prog(t,T3+.78,T3+2.05));world(d,t,{structures:1,bridgeK:1,gap:true,final:f,hand:h});
  // The user stays abstract: one gold tab and a physical thread from the opposite edge.
  const user=easeOut(prog(t,T3+.28,T3+1.18));if(user>0){strokeCurve(d,[[35,915],[245,845],[470,805],[745,760],[930,718]],{color:GOLD,width:7,alpha:.55*user});mark(d,72,908,GOLD,user,10);}
  const lock=easeOut(prog(t,T3+1.58,T3+2.55));if(lock>0){mark(d,1035,705,GOLD,.65*lock,8);mark(d,1035,705,BLUE,.55*lock,5);}
  const cap=easeOut(prog(t,T3+2.05,T3+2.95));d.text('keep building from here.',116,156,{size:38,font:'serif',italic:true,color:'#f4eee3',alpha:.58*cap});
}

export function renderConstructV3(d,t,model,poses){
  if(t<T1)return entry(d,t,model,poses);
  if(t<T2)return dive(d,t,model);
  if(t<T3)return build(d,t,model);
  return join(d,t,model);
}

export const CONSTRUCT_V3_CUTS=[30,T1,T2,T3,45];
