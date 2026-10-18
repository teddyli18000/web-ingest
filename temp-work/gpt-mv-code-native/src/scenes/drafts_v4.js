import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderOpeningV8} from './opening_v8.js';

const T0=15, T1=18.30, T2=21.80, T3=25.20, END=30;

const WRONG='#d94b3d';
const PAPER='rgba(255,253,248,.985)';

function art(d,model,dst,{crop='full',alpha=1,register=0,flip=false,rot=0,cover=false}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha,flip,rot});
  else model.draw(d.g,dst,{crop,alpha,flip,rot,cover});
}
function base(d,t,{blue=.055,gold=.10,dark=.035}={}){
  d.paper(t*.28);
  d.glow(1500,220,680,P.gold,gold);
  d.glow(330,800,720,P.cobalt,blue);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[1,`rgba(23,32,51,${dark})`]],true);
}
function desk(d,a=1){
  d.save(()=>{
    d.g.translate(-130,850);d.g.rotate(-.045);
    d.rect(0,0,2180,410,{fill:P.ink,alpha:.058*a});
    d.line(170,52,1700,52,{color:P.gold,width:6,alpha:.15*a});
  });
}
function pagePose(d,{cx,cy,w=900,h=610,rot=0,scale=1},fn){
  d.save(()=>{
    d.g.translate(cx,cy);d.g.rotate(rot);d.g.scale(scale,scale);d.g.translate(-w/2,-h/2);fn(w,h);
  });
}
function paper(d,w,h,{accent=P.gold,alpha=1,shadow=.30,fill=PAPER}={}){
  d.rrect(18,22,w,h,18,{fill:P.ink,alpha:.045*alpha});
  d.rrect(0,0,w,h,18,{fill,stroke:'rgba(53,65,92,.18)',width:1.5,alpha,shadow:shadow*alpha});
  d.line(36,42,w-40,42,{color:accent,width:5,alpha:.48*alpha});
}
function cropMarks(d,w,h,a=.18){
  const m=12,l=25;
  for(const [x,y,sx,sy] of [[0,0,1,1],[w,0,-1,1],[0,h,1,-1],[w,h,-1,-1]]){
    d.line(x-sx*m,y,x+sx*l,y,{color:P.ink2,width:1.5,alpha:a});
    d.line(x,y-sy*m,x,y+sy*l,{color:P.ink2,width:1.5,alpha:a});
  }
}
function node(d,x,y,{color=P.cobalt,a=1,r=8}={}){
  d.glow(x,y,78,color,.10*a);
  d.circle(x,y,r,{fill:color,alpha:a});
  d.circle(x,y,25,{fill:null,stroke:color,width:2,alpha:.30*a});
}
const MAP=[[110,475],[240,390],[365,430],[500,315],[625,355]], BAD=[790,185], GOOD=[805,485];
function path(d,{good=false,a=1,color=P.cobalt,width=5,progress=1,ghost=0}={}){
  const pts=[...MAP,good?GOOD:BAD], c=(pts.length-1)*Math.max(0,Math.min(1,progress));
  for(let i=0;i<pts.length-1;i++){
    const q=Math.max(0,Math.min(1,c-i)); if(q<=0)continue;
    const p=pts[i],n=pts[i+1];
    d.line(p[0],p[1],lerp(p[0],n[0],q),lerp(p[1],n[1],q),{color,width,alpha:a*(.80-.055*i)*(1-.55*ghost)});
  }
}
function proofContent(d,w,h,{mode='wrong',a=1,mark=0,build=1}={}){
  d.text(mode==='wrong'?'DRAFT / 01':'REVISION / FINAL',42,88,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.42*a});
  d.text(mode==='wrong'?'confident route':'corrected route',42,126,{size:29,font:'serif',italic:true,color:P.ink,alpha:.60*a});
  path(d,{good:false,a:(mode==='wrong'?.62:.12)*a,color:mode==='wrong'?P.gold:P.ink2,width:mode==='wrong'?5:3,progress:build,ghost:mode!=='wrong'});
  if(mode==='correct')path(d,{good:true,a:.72*a,color:P.cobalt,width:6,progress:build});
  node(d,MAP[0][0],MAP[0][1],{color:P.cobalt,a:.90*a,r:7});
  node(d,mode==='wrong'?BAD[0]:GOOD[0],mode==='wrong'?BAD[1]:GOOD[1],{color:mode==='wrong'?P.gold:P.gold,a:.92*a,r:9});
  if(mark>0){
    d.circle(BAD[0],BAD[1],56,{fill:null,stroke:WRONG,width:5,alpha:.72*mark*a});
    d.line(BAD[0]+38,BAD[1]+42,GOOD[0]-35,GOOD[1]-32,{color:WRONG,width:5,alpha:.66*mark*a});
    d.text('not there',BAD[0]-112,BAD[1]-76,{size:24,font:'serif',italic:true,color:WRONG,alpha:.70*mark*a});
  }
  cropMarks(d,w,h,.16*a);
}
function foregroundSheet(d,q,{y=860,rot=-.12,accent=P.gold,w=590,h=190}={}){
  if(q<=0||q>=1)return;
  d.save(()=>{
    d.g.translate(lerp(2040,-680,easeInOut(q)),y);d.g.rotate(rot);
    d.rrect(0,0,w,h,14,{fill:P.white,stroke:P.line,width:1.3,alpha:.95,shadow:.38});
    d.line(36,45,w-88,45,{color:accent,width:7,alpha:.55});
  });
}
function userMark(d,x,y,a=1){
  d.glow(x,y,150,P.gold,.22*a);d.circle(x,y,10,{fill:P.gold,alpha:a});d.circle(x,y,34,{fill:null,stroke:P.gold2,width:2,alpha:.42*a});
}

// 15–18.3: the final-world paper flies straight at camera; GPT catches the bad proof.
function shotCatch(d,t,model){
  renderOpeningV8(d,14.999,model);
  const cover=easeInOut(prog(t,T0,T0+.72));
  if(cover>0){
    d.save(()=>{
      const x=lerp(2100,-120,cover), y=lerp(920,-90,cover), w=2180,h=1320;
      d.g.translate(x+w/2,y+h/2);d.g.rotate(lerp(-.18,-.035,cover));d.g.translate(-(x+w/2),-(y+h/2));
      d.rrect(x,y,w,h,38,{fill:PAPER,stroke:'rgba(53,65,92,.16)',width:2,shadow:.60});
      d.line(x+150,y+118,x+w-210,y+118,{color:P.gold,width:8,alpha:.48});
    });
  }
  const room=smooth(prog(t,T0+.42,T0+1.10)); if(room<=0)return;
  d.alpha(room,()=>{base(d,t,{blue:.045,gold:.13});desk(d,1);});

  const board=easeOut(prog(t,T0+.66,T0+1.62));
  pagePose(d,{cx:lerp(1460,1115,board),cy:lerp(780,570,board),rot:lerp(.13,-.045,board),scale:lerp(1.36,1.00,board)},(w,h)=>{
    paper(d,w,h,{accent:P.gold,alpha:board,shadow:.35});proofContent(d,w,h,{mode:'wrong',a:board,build:easeOut(prog(t,T0+.92,T0+1.90))});
  });

  // The hand is the hero of the shot: same approved art, extreme crop.
  const handIn=easeOut(prog(t,T0+.42,T0+1.05)),handOut=1-smooth(prog(t,T0+2.45,T1-.08));
  const ha=handIn*handOut;
  if(ha>0){
    d.save(()=>{d.g.beginPath();d.g.rect(980,500,940,580);d.g.clip();art(d,model,{x:980,y:410,w:1040,h:760},{crop:'hand',alpha:.98*ha,register:3,cover:true,rot:-.025});});
  }
  d.text('something is off.',112,164,{size:43,font:'serif',italic:true,color:P.ink,alpha:.62*easeOut(prog(t,T0+1.30,T0+2.15))});
  foregroundSheet(d,prog(t,T0+.20,T0+1.14),{y:875,accent:P.cobalt,rot:-.14,w:520,h:165});
}

// 18.3–21.8: face close-up watches two physical versions separate and align.
function shotCompare(d,t,model){
  base(d,t,{blue:.058,gold:.105});desk(d,.82);
  const intro=easeInOut(prog(t,T1,T1+.58));
  // Face occupies a real camera plane, not a small sticker.
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,690,1080);d.g.clip();art(d,model,{x:-250,y:-30,w:1040,h:840},{crop:'close',alpha:.98,register:4,cover:true});});
  d.rect(0,0,690,1080,{fill:P.cobalt,alpha:.025});

  const wrong={cx:lerp(1115,1060,intro),cy:lerp(570,585,intro),rot:lerp(-.045,-.075,intro),scale:lerp(1.00,.82,intro)};
  const split=easeInOut(prog(t,T1+.48,T1+1.38));
  pagePose(d,{...wrong,cx:lerp(wrong.cx,965,split)},(w,h)=>{paper(d,w,h,{accent:P.coral??WRONG,shadow:.27});proofContent(d,w,h,{mode:'wrong',mark:easeOut(prog(t,T1+.45,T1+1.18))});});
  const rightA=easeOut(prog(t,T1+.62,T1+1.42));
  pagePose(d,{cx:lerp(1240,1425,split),cy:580,rot:lerp(-.02,.055,split),scale:lerp(.72,.83,split)},(w,h)=>{
    paper(d,w,h,{accent:P.cobalt,alpha:rightA,fill:'rgba(241,246,255,.94)',shadow:.26});proofContent(d,w,h,{mode:'correct',a:rightA,build:easeOut(prog(t,T1+.90,T1+1.95))});
  });

  // A hand enters between the versions and physically points from wrong to corrected.
  const hand=easeOut(prog(t,T1+1.00,T1+1.75))*(1-smooth(prog(t,T2-.70,T2-.05)));
  if(hand>0)d.save(()=>{d.g.beginPath();d.g.rect(1010,640,910,440);d.g.clip();art(d,model,{x:950,y:480,w:1050,h:720},{crop:'hand',alpha:.90*hand,register:2,cover:true,rot:-.035});});
  d.text('compare, don’t conceal.',84,966,{size:28,font:'mono',weight:700,color:P.ink2,alpha:.42*easeOut(prog(t,T1+.70,T1+1.35))});
  foregroundSheet(d,prog(t,T1+.18,T1+1.12),{y:905,accent:WRONG,rot:-.10,w:470,h:150});
}

function tearRibbon(d,t,a=1){
  const peel=easeInOut(prog(t,T2+.22,T2+1.68));
  for(let i=0;i<11;i++){
    const q=easeOut(prog(peel,i*.045,.36+i*.045)); if(q<=0)continue;
    const u=i/10, sx=850+u*170, sy=410-u*145, ex=1550+u*190, ey=250+Math.sin(u*Math.PI)*110;
    const x=lerp(sx,ex,q),y=lerp(sy,ey,q);
    d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.48,.22,u)+q*.28);d.rrect(-46,-10,92,20,4,{fill:WRONG,alpha:.78*q*a,shadow:.12});});
  }
}

// 21.8–25.2: the wrong sheet peels away; the corrected sheet is the object that remains.
function shotPeel(d,t,model){
  base(d,t,{blue:.072,gold:.075});desk(d,.64);
  const peel=easeInOut(prog(t,T2+.18,T2+1.62));
  const settle=easeInOut(prog(t,T2+1.28,T3-.12));

  pagePose(d,{cx:lerp(965,1260,peel),cy:lerp(585,260,peel),rot:lerp(-.075,-.22,peel),scale:lerp(.82,.58,peel)},(w,h)=>{
    paper(d,w,h,{accent:WRONG,alpha:1-.68*peel,shadow:.25});proofContent(d,w,h,{mode:'wrong',a:1-.35*peel,mark:1});
  });
  pagePose(d,{cx:lerp(1425,1030,settle),cy:lerp(580,555,settle),rot:lerp(.055,-.018,settle),scale:lerp(.83,.99,settle)},(w,h)=>{
    paper(d,w,h,{accent:P.cobalt,fill:'rgba(247,249,255,.975)',shadow:.31});proofContent(d,w,h,{mode:'correct',build:1});
  });
  tearRibbon(d,t,1);

  // Pull back: character re-enters as a whole body only after the decision is made.
  const char=easeOut(prog(t,T2+1.15,T2+2.25));
  if(char>0)art(d,model,{x:1320,y:80,w:720,h:880},{crop:'full',alpha:.96*char,register:5});
  const hand=easeOut(prog(t,T2+.26,T2+1.00))*(1-smooth(prog(t,T2+1.38,T2+2.00)));
  if(hand>0)d.save(()=>{d.g.beginPath();d.g.rect(1260,0,660,520);d.g.clip();art(d,model,{x:1220,y:-100,w:860,h:650},{crop:'hand',alpha:.88*hand,cover:true,flip:true,rot:.08});});
  d.text('keep the evidence.',92,142,{size:42,font:'serif',italic:true,color:P.ink,alpha:.66*easeOut(prog(t,T2+.95,T2+1.70))});
  d.text('remove the mistake.',94,184,{size:20,font:'mono',weight:700,color:WRONG,alpha:.42*easeOut(prog(t,T2+1.08,T2+1.88))});
}

// 25.2–30: one clean page is physically returned to the user mark.
function shotReturn(d,t,model){
  base(d,t,{blue:.045,gold:.15});desk(d,.50);
  const intro=easeInOut(prog(t,T3,T3+.55));
  const breathe=Math.sin((t-T3)*1.15)*4;
  art(d,model,{x:1220,y:80+breathe,w:760,h:900},{crop:'full',alpha:1,register:5});

  const give=easeInOut(prog(t,T3+.72,T3+2.72));
  const pose={cx:lerp(1030,690,give),cy:lerp(555,610,give),rot:lerp(-.018,-.055,give),scale:lerp(.99,.78,give)};
  pagePose(d,pose,(w,h)=>{
    paper(d,w,h,{accent:P.gold,fill:PAPER,shadow:.32});proofContent(d,w,h,{mode:'correct',build:1});
    const title=easeOut(prog(t,T3+.18,T3+1.00));
    d.text('keep what matters.',46,142,{size:34,font:'serif',italic:true,color:P.ink,alpha:.70*title});
  });

  const user=easeOut(prog(t,T3+.65,T3+1.28));userMark(d,250,790,user);
  // Seven physical tabs form a handoff bridge from the page edge to the user mark.
  const bridge=easeOut(prog(t,T3+1.20,T3+2.95));
  if(bridge>0)for(let i=0;i<7;i++){
    const q=easeOut(prog(bridge,i*.075,.42+i*.075)),u=i/6;
    const x=lerp(690,285,u), y=lerp(735,790,u)-Math.sin(u*Math.PI)*58;
    d.save(()=>{d.g.translate(x,y);d.g.rotate(-.10+i*.025);d.rrect(-52*q,-16,104*q,32,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.92*q,shadow:.12});});
  }
  const hand=easeOut(prog(t,T3+.92,T3+1.70));
  if(hand>0)d.save(()=>{d.g.beginPath();d.g.rect(850,585,1070,495);d.g.clip();art(d,model,{x:900,y:430,w:1080,h:780},{crop:'hand',alpha:.76*hand,register:2,cover:true,rot:-.025});});

  const end=easeOut(prog(t,T3+2.20,END-.35));
  d.text('REVISION / COMPLETE',90,980,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.32*end});
  foregroundSheet(d,prog(t,T3+.30,T3+1.40),{y:925,accent:P.gold,rot:-.12,w:520,h:160});
}

export function renderDraftsV4(d,t,model){
  if(t<T1)return shotCatch(d,t,model);
  if(t<T2)return shotCompare(d,t,model);
  if(t<T3)return shotPeel(d,t,model);
  return shotReturn(d,t,model);
}

export const DRAFTS_V4_CUTS=[T0,T1,T2,T3,END];
