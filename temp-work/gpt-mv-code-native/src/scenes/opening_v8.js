import {renderOpeningV7} from './opening_v7.js';
import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';
import {cursor} from '../components/chat.js';

const BPM=116,OFF=.28,PB=60/BPM;
const B=n=>OFF+n*PB;
const C1=B(6),C2=B(13),C3=B(20),END=15;
const P1={x:-170,y:30,w:1080,h:1000};
const DOCK={x:390,y:390,w:1290,h:280};
const PROOF={x:610,y:330,w:1100,h:330};

function base(d,t,{dark=.12,blue=.08,warm=.08}={}){
  d.paper(t*.32);
  d.glow(420,720,700,P.cobalt,blue);
  d.glow(1510,230,520,P.gold,warm);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[.55,`rgba(23,32,51,${dark*.32})`],[1,`rgba(23,32,51,${dark})`]],true);
}
function inkShelf(d,a=1){d.save(()=>{d.g.translate(-100,835);d.g.rotate(-.032);d.rect(0,0,820,300,{fill:P.ink,alpha:.095*a});d.line(80,62,670,62,{color:P.cobalt,width:7,alpha:.20*a});});}
function art(d,model,dst,{crop='full',alpha=1,register=0,clip=null}={}){
  d.save(()=>{
    if(clip){d.g.beginPath();d.g.rect(clip.x,clip.y,clip.w,clip.h);d.g.clip();}
    if(register>0)model.register(d.g,dst,{crop,spread:register,alpha});
    else model.draw(d.g,dst,{crop,alpha});
  });
}
function mixRect(a,b,k){return{x:lerp(a.x,b.x,k),y:lerp(a.y,b.y,k),w:lerp(a.w,b.w,k),h:lerp(a.h,b.h,k)};}

function openingHand(d,t,model){
  const enter=easeOut(prog(t,.10,.42)),leave=1-easeInOut(prog(t,.82,1.42)),a=enter*leave;
  if(a<=0)return;
  // A photographic-scale gesture is the first subject. The same master later pulls back
  // to bust/full views, so this is not a separate illustration or a decorative insert.
  d.save(()=>{d.g.beginPath();d.g.rect(830,0,1090,1080);d.g.clip();
    model.plate(d.g,{x:820,y:-80,w:1120,h:1190},{crop:'hand',color:P.ink,alpha:.12*a,rot:-.025});
    model.draw(d.g,{x:800,y:-100,w:1120,h:1190},{crop:'hand',alpha:.96*a,rot:-.025});
  });
  d.line(115,235,690,235,{color:P.cobalt,width:5,alpha:.38*a});
  d.text('first: reach the page.',116,205,{size:29,font:'serif',italic:true,color:P.ink2,alpha:.48*a});
}

function typing(t){
  const a='make it impressive.',b='make it worth watching.';
  // A short physical unfold happens before typing begins; this gives the C2 handoff room to breathe.
  const q=(t-(C2+.20))/PB;let s='',del=false;
  if(q<0)return{s,del,done:false};
  if(q<1.55)s=a.slice(0,Math.floor(prog(q,0,1.38)*a.length));
  else if(q<2.12)s=a;
  else if(q<3.10){s=a.slice(0,Math.ceil((1-prog(q,2.12,3.10))*a.length));del=true;}
  else if(q<3.48)s='';
  else s=b.slice(0,Math.floor(prog(q,3.48,5.82)*b.length));
  return{s,del,done:s===b};
}

function floodState(t){const k=easeInOut(prog(t,C3-.55,C3+.65));return{k,top:lerp(1140,-40,k)};}
function flood(d,t){const f=floodState(t);if(f.k<=0)return;d.rect(-30,f.top,1980,1180,{fill:P.ink,alpha:.995*f.k});d.line(0,f.top+36,1920,f.top+36,{color:P.cobalt2,width:3,alpha:.18*f.k});}
function sendState(t){return easeOut(prog(t,C3-.58,C3+.08));}

function proofSheet(d,t,typed,send){
  const unfold=easeInOut(prog(t,C2,C2+.48)),r=mixRect(DOCK,PROOF,unfold);
  const survive=1-easeInOut(prog(send,.22,.92));
  if(survive<=0)return r;
  const radius=lerp(38,8,unfold),shadow=lerp(.55,.30,unfold);
  d.save(()=>{
    d.g.translate(r.x+r.w/2,r.y+r.h/2);d.g.rotate(lerp(0,-.012,unfold));d.g.translate(-(r.x+r.w/2),-(r.y+r.h/2));
    d.rrect(r.x+14,r.y+18,r.w,r.h,radius,{fill:P.ink,alpha:.05*survive});
    d.rrect(r.x,r.y,r.w,r.h,radius,{fill:'rgba(255,253,248,.985)',stroke:'rgba(53,65,92,.20)',width:1.8,shadow,alpha:survive});
    // Folded proof corner replaces the app-like send-card silhouette.
    const fold=lerp(0,42,unfold);if(fold>1){d.save(()=>{d.g.beginPath();d.g.moveTo(r.x+r.w-fold,r.y);d.g.lineTo(r.x+r.w,r.y+fold);d.g.lineTo(r.x+r.w,r.y);d.g.closePath();d.g.fillStyle=P.gold2;d.g.globalAlpha=.52*survive;d.g.fill();});}
    d.circle(r.x+44,r.y+42,10,{fill:P.gold,alpha:.84*survive});
    d.text('PROOF / YOU',r.x+70,r.y+49,{size:19,font:'mono',weight:700,color:P.ink2,alpha:.42*unfold*survive});
    d.line(r.x+38,r.y+76,r.x+r.w-40,r.y+76,{color:P.line,width:1.4,alpha:.32*survive});
    d.text(typed.s,r.x+48,r.y+lerp(170,190,unfold),{size:lerp(50,56,unfold),font:'serif',color:P.ink,weight:500,alpha:.96*survive});
    const size=lerp(50,56,unfold),tw=d.measure(typed.s,{size,font:'serif'});
    if(Math.floor(t*3.2)%2===0&&send<.2)d.rect(r.x+52+tw,r.y+lerp(121,137,unfold),4,64,{fill:typed.del?P.coral:P.cobalt,alpha:.82*survive});
    if(unfold>.55){d.text(typed.del?'REVISE':'DRAFT',r.x+r.w-54,r.y+r.h-34,{size:18,font:'mono',weight:700,align:'right',color:typed.del?P.coral:P.ink2,alpha:.42*survive});}
  });
  return r;
}

function rejectedProof(d,t){
  const q=(t-(C2+.20))/PB,del=prog(q,2.10,3.12);if(del<=0||del>=1)return;
  const k=easeOut(del);
  // The bad phrase is not merely backspaced: its proof marks are physically removed.
  for(let i=0;i<5;i++){
    const x=lerp(960+i*70,1840+i*34,k),y=lerp(535+i*9,260+i*82,k);
    d.save(()=>{d.g.translate(x,y);d.g.rotate(-.22+i*.09+k*.20);d.rrect(-64,-5,128,10,5,{fill:P.coral,alpha:.55*(1-k*.42),shadow:.10});});
  }
}

function finalTypingMarks(d,t){
  const q=(t-(C2+.20))/PB,make=easeOut(prog(q,3.48,5.3));if(make<=0)return;
  for(let i=0;i<6;i++){const a=easeOut(prog(make,i*.09,.42+i*.09));d.circle(720+i*122,712,5,{fill:i%2?P.gold:P.cobalt,alpha:.28*a});}
}

function strips(d,t,send){
  if(send<=0)return;
  for(let i=0;i<9;i++){
    const k=easeOut(prog(send,i*.045,.45+i*.04));
    const sx=740+i*92,sy=555+(i%3)*20,ex=500+i*138,ey=640+(i%2?55:-55);
    d.save(()=>{d.g.translate(lerp(sx,ex,k),lerp(sy,ey,k));d.g.rotate(lerp(-.012,(i-4)*.025,k));d.rrect(-86,-23,172,46,11,{fill:i%3===0?P.gold2:P.white,stroke:P.line,width:1.2,shadow:.18,alpha:k});});
  }
}

function shotPrompt(d,t,model){
  const typed=typing(t),send=sendState(t),unfold=easeInOut(prog(t,C2,C2+.48));
  base(d,t,{dark:lerp(.14,.10,unfold),blue:lerp(.12,.075,unfold),warm:lerp(.12,.09,unfold)});
  inkShelf(d,lerp(.90,.58,unfold));

  // Paper first, character second: the proof physically sits behind her shoulder and never hides its own text.
  proofSheet(d,t,typed,send);
  rejectedProof(d,t);finalTypingMarks(d,t);
  art(d,model,P1,{crop:'bust',alpha:.98,register:lerp(7,4,unfold),clip:{x:0,y:0,w:515,h:1080}});
  d.line(518,184,518,900,{color:P.cobalt,width:3,alpha:.13*unfold});

  const cx=lerp(1820,1600,easeInOut(prog(t,C2+.08,C2+.86))),cy=lerp(790,590,easeInOut(prog(t,C2+.08,C2+.86)));
  cursor(d,cx,cy,{alpha:(1-send)*easeOut(prog(t,C2+.05,C2+.35)),click:prog(t,C3-.31,C3-.05)});

  flood(d,t);
  strips(d,t,send);
  // Character remains above the rising dark sheet until the exact cut; v6 continues the same P1 crop at C3.
  if(send>.16)art(d,model,P1,{crop:'bust',alpha:.98,register:4,clip:{x:0,y:0,w:515,h:1080}});
}

export function renderOpeningV8(d,t,model){
  if(t<C2){renderOpeningV7(d,t,model);if(t<C1)openingHand(d,t,model);return;}
  if(t<C3)return shotPrompt(d,t,model);
  return renderOpeningV7(d,t,model);
}

export const OPENING_V8_CUTS=[0,C1,C2,C3,END];
