import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV6} from './drafts_v6.js';

const T1=18.30,T2=21.80;
const WRONG='#d94b3d',PAPER='rgba(255,253,248,.985)';
const MAP=[[110,475],[240,390],[365,430],[500,315],[625,355]],BAD=[790,185],GOOD=[805,485];

function base(d,t){
  d.paper(t*.28);
  d.glow(1510,220,680,P.gold,.105);
  d.glow(330,800,720,P.cobalt,.060);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[1,'rgba(23,32,51,.035)']],true);
  d.save(()=>{d.g.translate(-130,850);d.g.rotate(-.045);d.rect(0,0,2180,410,{fill:P.ink,alpha:.052});d.line(170,52,1700,52,{color:P.gold,width:6,alpha:.14});});
}
function pagePose(d,{cx,cy,w=900,h=610,rot=0,scale=1},fn){d.save(()=>{d.g.translate(cx,cy);d.g.rotate(rot);d.g.scale(scale,scale);d.g.translate(-w/2,-h/2);fn(w,h);});}
function paper(d,w,h,{accent=P.gold,alpha=1,fill=PAPER,shadow=.29}={}){
  d.rrect(18,22,w,h,18,{fill:P.ink,alpha:.045*alpha});
  d.rrect(0,0,w,h,18,{fill,stroke:'rgba(53,65,92,.18)',width:1.5,alpha,shadow:shadow*alpha});
  d.line(36,42,w-40,42,{color:accent,width:5,alpha:.48*alpha});
}
function node(d,x,y,{color=P.cobalt,a=1,r=8}={}){d.glow(x,y,78,color,.10*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,25,{fill:null,stroke:color,width:2,alpha:.30*a});}
function route(d,{good=false,a=1,color=P.cobalt,width=5,progress=1,ghost=0}={}){
  const pts=[...MAP,good?GOOD:BAD],c=(pts.length-1)*Math.max(0,Math.min(1,progress));
  for(let i=0;i<pts.length-1;i++){
    const q=Math.max(0,Math.min(1,c-i));if(q<=0)continue;
    const p=pts[i],n=pts[i+1];
    d.line(p[0],p[1],lerp(p[0],n[0],q),lerp(p[1],n[1],q),{color,width,alpha:a*(.80-.055*i)*(1-.55*ghost)});
  }
}
function proof(d,w,h,{mode='wrong',a=1,mark=0,build=1}={}){
  d.text(mode==='wrong'?'DRAFT / 01':'REVISION / 02',42,88,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.42*a});
  d.text(mode==='wrong'?'confident route':'corrected route',42,126,{size:29,font:'serif',italic:true,color:P.ink,alpha:.60*a});
  route(d,{good:false,a:(mode==='wrong'?.62:.12)*a,color:mode==='wrong'?P.gold:P.ink2,width:mode==='wrong'?5:3,progress:build,ghost:mode!=='wrong'});
  if(mode==='correct')route(d,{good:true,a:.72*a,color:P.cobalt,width:6,progress:build});
  node(d,MAP[0][0],MAP[0][1],{color:P.cobalt,a:.90*a,r:7});
  node(d,mode==='wrong'?BAD[0]:GOOD[0],mode==='wrong'?BAD[1]:GOOD[1],{color:P.gold,a:.92*a,r:9});
  if(mark>0){
    d.circle(BAD[0],BAD[1],56,{fill:null,stroke:WRONG,width:5,alpha:.72*mark*a});
    d.line(BAD[0]+38,BAD[1]+42,GOOD[0]-35,GOOD[1]-32,{color:WRONG,width:5,alpha:.66*mark*a});
    d.text('not there',BAD[0]-112,BAD[1]-76,{size:24,font:'serif',italic:true,color:WRONG,alpha:.70*mark*a});
  }
}
function coverImage(g,img,x,y,w,h,{alpha=1,pan=0}={}){
  const dar=w/h,iar=img.naturalWidth/img.naturalHeight;
  let sx=0,sy=0,sw=img.naturalWidth,sh=img.naturalHeight;
  if(iar>dar){sw=sh*dar;sx=(img.naturalWidth-sw)*(.48+pan*.07);}
  else{sh=sw/dar;sy=(img.naturalHeight-sh)*(.46+pan*.05);}
  g.save();g.globalAlpha=alpha;g.filter='saturate(.70) contrast(1.06) brightness(1.03)';g.drawImage(img,sx,sy,sw,sh,x,y,w,h);g.restore();
}
function tornPosePath(g,x,y,w,h,offset=0){
  g.beginPath();
  g.moveTo(x+72+offset,y+8);
  g.bezierCurveTo(x+230+offset,y-15,x+470+offset,y+26,x+w-36+offset,y+118);
  g.bezierCurveTo(x+w+22+offset,y+260,x+w-20+offset,y+510,x+w-104+offset,y+h-26);
  g.bezierCurveTo(x+420+offset,y+h+18,x+214+offset,y+h-4,x+18+offset,y+h-126);
  g.bezierCurveTo(x-42+offset,y+570,x-20+offset,y+250,x+72+offset,y+8);
  g.closePath();
}
function thinkingCutout(d,t,img){
  if(!img)return;
  const enter=easeOut(prog(t,T1+.16,T1+.72));
  const leave=1-smooth(prog(t,T2-.66,T2-.05));
  const a=enter*leave;if(a<=0)return;
  const x=lerp(-510,-80,enter),y=118,w=760,h=860,drift=prog(t,T1,T2);
  const g=d.g;
  // Offset print plates: the pose belongs to the scene, not to a framed photo card.
  d.save(()=>{tornPosePath(g,x-18,y+15,w,h);g.fillStyle=P.cobalt;g.globalAlpha=.105*a;g.fill();});
  d.save(()=>{tornPosePath(g,x+17,y-10,w,h);g.fillStyle=P.gold;g.globalAlpha=.075*a;g.fill();});
  d.save(()=>{
    tornPosePath(g,x,y,w,h);g.clip();
    coverImage(g,img,x-22,y-12,w+90,h+42,{alpha:.94*a,pan:drift});
    const gr=g.createLinearGradient(x,y,x+w,y+h);gr.addColorStop(0,'rgba(243,239,228,.18)');gr.addColorStop(.58,'rgba(49,87,213,.03)');gr.addColorStop(1,'rgba(23,32,51,.16)');g.fillStyle=gr;g.globalAlpha=a;g.fillRect(x,y,w,h);
  });
  // One quiet registration edge, no card chrome.
  d.line(x+w-86,y+120,x+w-126,y+h-90,{color:P.cobalt2,width:3,alpha:.24*a});
}
function foregroundSwipe(d,t){
  const q=prog(t,T1+.28,T1+1.08);if(q<=0||q>=1)return;
  d.save(()=>{d.g.translate(lerp(2060,-620,easeInOut(q)),900);d.g.rotate(-.105);d.rrect(0,0,560,155,14,{fill:P.white,stroke:P.line,width:1.2,alpha:.93,shadow:.34});d.line(34,40,430,40,{color:WRONG,width:7,alpha:.50});});
}
function compareScene(d,t,poses){
  base(d,t);
  thinkingCutout(d,t,poses?.think);

  const split=easeInOut(prog(t,T1+.50,T1+1.42));
  const wrong={cx:lerp(1090,965,split),cy:585,rot:lerp(-.035,-.075,split),scale:lerp(.94,.82,split)};
  const mark=easeOut(prog(t,T1+.42,T1+1.16));
  pagePose(d,wrong,(w,h)=>{paper(d,w,h,{accent:WRONG,shadow:.27});proof(d,w,h,{mode:'wrong',mark});});

  // Corrected route is tracing paper physically pulled from behind the draft.
  const trace=easeOut(prog(t,T1+.78,T1+1.54));
  const corrected={cx:lerp(1040,1425,trace),cy:lerp(590,580,trace),rot:lerp(-.05,.055,trace),scale:lerp(.78,.83,trace)};
  if(trace>0)pagePose(d,corrected,(w,h)=>{
    paper(d,w,h,{accent:P.cobalt,alpha:trace,fill:'rgba(241,246,255,.91)',shadow:.25});
    proof(d,w,h,{mode:'correct',a:trace,build:easeOut(prog(t,T1+1.00,T1+1.92))});
    d.line(110,170,790,170,{color:P.cobalt2,width:2,alpha:.14*trace});
  });

  const caption=easeOut(prog(t,T1+.72,T1+1.42))*(1-smooth(prog(t,T2-.65,T2)));
  d.text('look again.',92,132,{size:38,font:'serif',italic:true,color:P.ink,alpha:.60*caption});
  d.text('COMPARE / KEEP THE EVIDENCE',94,174,{size:19,font:'mono',weight:700,color:P.ink2,alpha:.34*caption});
  foregroundSwipe(d,t);
}
function compareWithHandoff(d,t,model,poses){
  const k=easeInOut(prog(t,T1,T1+.62));
  if(k>=.999)return compareScene(d,t,poses);
  // Hold the last valid frame from shot 1 and reveal the new scene behind a moving proof sheet.
  renderDraftsV6(d,T1-.001,model);
  const edge=lerp(1980,-120,k);
  d.save(()=>{
    const g=d.g;g.beginPath();g.rect(edge,-40,2100-edge,1160);g.clip();compareScene(d,t,poses);
  });
  d.save(()=>{d.g.translate(edge-70,530);d.g.rotate(-.055);d.rrect(-70,-700,150,1400,8,{fill:P.white,stroke:P.line,width:1.4,alpha:.97,shadow:.42});d.line(-25,-610,-25,590,{color:P.gold,width:5,alpha:.30});});
}

export function renderDraftsV9(d,t,model,poses){
  if(t<T1||t>=T2)return renderDraftsV6(d,t,model);
  return compareWithHandoff(d,t,model,poses);
}

export const DRAFTS_V9_CUTS=[15,T1,T2,25.20,30];
