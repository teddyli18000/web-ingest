import {PALETTE as P} from '../engine/palette.js';
import {easeOut,lerp,prog,smooth} from '../engine/timing.js';

export const L={x:210,y:115,w:1500,h:850,r:34,side:260,head:94,compose:116};

export function drawWindow(d,t,{open=1,glass=1,thread=1}={}){
  const k=easeOut(open),{x,y,w,h,r}=L,cx=x+w/2,cy=y+h/2;
  const hh=Math.max(3,h*k),ww=w*Math.min(1,k*1.5);
  d.rrect(cx-ww/2,cy-hh/2,ww,hh,r*k,{fill:`rgba(255,255,255,${.58*glass})`,stroke:P.line,width:2,shadow:k});
  if(k<.72)return;
  const a=smooth((k-.72)/.28);
  d.line(x+L.side,y+18,x+L.side,y+h-18,{color:P.line,width:2,alpha:a*.85});
  d.line(x+L.side,y+L.head,x+w-18,y+L.head,{color:P.line,width:2,alpha:a*.85});
  d.line(x+L.side+34,y+h-L.compose,x+w-34,y+h-L.compose,{color:P.line,width:2,alpha:a*.55});
  d.text('ChatGPT',x+L.side+38,y+61,{size:31,weight:650,color:P.ink,alpha:a});
  d.circle(x+w-66,y+47,17,{fill:P.cobalt,alpha:a});
  // sidebar lines are intentionally abstract: enough to feel like a client, not a product screenshot.
  for(let i=0;i<7;i++){
    const yy=y+82+i*72, active=i===0;
    if(active)d.rrect(x+22,yy-23,L.side-44,48,15,{fill:'rgba(47,102,213,.10)',alpha:a});
    d.rrect(x+45,yy-5,active?125:95+(i%3)*24,10,5,{fill:active?P.cobalt:P.line,alpha:a*(active?.8:.6)});
  }
  if(thread>0){
    const ta=a*thread;d.rrect(x+L.side+62,y+L.head+68,520,84,28,{fill:'rgba(242,184,75,.15)',stroke:'rgba(242,184,75,.35)',alpha:ta});
    d.rrect(x+w-632,y+L.head+196,540,104,30,{fill:'rgba(47,102,213,.09)',stroke:'rgba(47,102,213,.24)',alpha:ta});
  }
  composer(d,1,a);
}

export function composer(d,k=1,alpha=1){
  const {x,y,w,h}=L,xx=x+L.side+62,yy=y+h-L.compose+27,ww=w-L.side-124;
  d.rrect(xx,yy,ww,65,24,{fill:'rgba(255,255,255,.82)',stroke:P.line,width:1.5,alpha,shadow:.22});
  d.circle(xx+31,yy+32,12,{fill:P.gold,alpha:alpha*.8});
  d.rrect(xx+58,yy+25,Math.max(0,(250*k)),13,7,{fill:P.line,alpha:alpha*.65});
  d.circle(xx+ww-34,yy+32,18,{fill:P.cobalt,alpha:alpha*k});
}

export function userBubble(d,t,start,text){
  const a=easeOut(prog(t,start,start+.28)),slide=(1-a)*35;
  if(a<=0)return;
  const x=L.x+L.w-715+slide,y=L.y+L.head+105,w=540,h=82;
  d.rrect(x,y,w,h,26,{fill:'#fff8e8',stroke:'rgba(242,184,75,.55)',alpha:a,shadow:.25});
  const n=Math.floor(text.length*prog(t,start+.18,start+1.1));
  d.text(text.slice(0,n),x+28,y+52,{size:31,color:P.ink,alpha:a});
  if(n<text.length&&Math.floor(t*4)%2===0)d.rect(x+31+d.measure(text.slice(0,n),{size:31}),y+25,3,34,{fill:P.gold,alpha:a});
}

export function assistantBubble(d,t,start,text){
  const a=easeOut(prog(t,start,start+.35));if(a<=0)return;
  const x=L.x+L.side+82,y=L.y+L.head+245,w=660,h=104;
  d.rrect(x,y,w,h,28,{fill:'rgba(234,241,255,.86)',stroke:'rgba(47,102,213,.30)',alpha:a,shadow:.32});
  d.circle(x+31,y+31,13,{fill:P.cobalt,alpha:a});
  const n=Math.floor(text.length*prog(t,start+.2,start+1.3));
  d.text(text.slice(0,n),x+58,y+61,{size:33,color:P.ink,alpha:a,font:'serif',italic:true});
}

export function cursor(d,x,y,{alpha=1,click=0}={}){
  const g=d.g;d.save(()=>{g.translate(x,y);g.rotate(-.18);const p=new Path2D('M0 0 L0 43 L11 32 L20 51 L29 46 L20 28 L37 27 Z');d.path(p,{fill:P.gold,stroke:P.ink2,width:2,alpha});if(click>0)d.circle(4,4,34,{fill:null,stroke:P.gold,width:4,alpha:alpha*(1-click)})})
}

export function buildPieces(d,t,start=1.0){
  const parts=[
    [L.x,L.y,L.w,L.h,'window'],
    [L.x+18,L.y+22,L.side-36,L.h-44,'sidebar'],
    [L.x+L.side+20,L.y+18,L.w-L.side-42,L.head-18,'header'],
    [L.x+L.side+50,L.y+L.head+22,L.w-L.side-100,L.h-L.head-L.compose-42,'thread'],
    [L.x+L.side+60,L.y+L.h-L.compose+24,L.w-L.side-120,68,'composer']
  ];
  parts.forEach(([x,y,w,h,label],i)=>{
    const a=easeOut(prog(t,start+i*.24,start+i*.24+.42));if(a<=0)return;
    const lift=(1-a)*(i%2? -210:260),rot=(1-a)*(i-2)*.025;
    d.save(()=>{d.g.translate(x+w/2,y+h/2+lift);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));d.rrect(x,y,w,h,Math.min(24,h*.18),{fill:i===0?'rgba(255,255,255,.22)':'rgba(255,253,248,.78)',stroke:i===0?P.cobalt2:P.line,width:2,alpha:a,shadow:.15});if(i>0)d.text(label,x+18,y+31,{size:20,font:'mono',color:P.ink2,alpha:a*.7})})
  });
}
