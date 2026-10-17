import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {assistantBubble,cursor,drawWindow,L,userBubble} from '../components/chat.js';
import {drawGPT} from '../components/gpt.js';

const userText='make something only code can make.';
const replyText='Then watch the interface become a world.';

function paperWorld(d,t,k){
  const horizon=lerp(835,590,easeInOut(k));
  // background / atmosphere
  d.gradRect(0,0,1920,1080,[[0,P.paper],[.52,'#eef3ff'],[1,'#ffe8b6']],true);
  d.glow(1510,225,480,P.gold,.33*k);
  d.circle(1510,225,90,{fill:P.gold2,alpha:.55*k});
  // middle layer: city / pages built from the same rectangular grammar as the app.
  for(let i=0;i<13;i++){
    const x=90+i*152,base=horizon+((i*37)%78),hh=90+((i*91)%240)*k;
    const w=82+((i*17)%48);
    d.rrect(x,base-hh,w,hh,8,{fill:i%3===0?'rgba(47,102,213,.16)':'rgba(255,253,248,.72)',stroke:'rgba(53,65,92,.16)',alpha:.85*k});
    for(let r=0;r<3;r++)d.rect(x+16,base-hh+24+r*34,w-32,8,{fill:i%3===0?P.cobalt2:P.line,alpha:.20*k});
  }
  // foreground paper rails: UI separators have become landscape perspective lines.
  for(let i=0;i<6;i++){
    const yy=lerp(horizon,1080,i/5),spread=90+i*150;
    d.line(960-spread,yy,960+spread,yy,{color:i<2?P.cobalt:P.ink2,width:2+i*.35,alpha:(.18+.10*i)*k});
  }
  for(const x of [220,520,880,1260,1660]) d.line(960,horizon,x,1080,{color:P.gold,width:2,alpha:.18*k});
  // foreground scraps move independently, so the shot is not one flat illustration.
  const scraps=[[-80,760,370,210,-.08],[1520,720,430,240,.07],[280,920,500,200,.03]];
  scraps.forEach(([x,y,w,h,r],i)=>d.save(()=>{d.g.translate(x+w/2,y+h/2);d.g.rotate(r+Math.sin(t*.45+i)*.01);d.g.translate(-(x+w/2),-(y+h/2));d.rrect(x,y,w,h,18,{fill:i===1?'rgba(47,102,213,.10)':'rgba(255,253,248,.84)',stroke:'rgba(53,65,92,.15)',alpha:k,shadow:.25*k});d.line(x+28,y+48,x+w-40,y+48,{color:i===1?P.cobalt:P.gold,width:5,alpha:.46*k})}));
}

export function renderReply(d,t){
  d.paper(t);
  d.glow(1320,340,520,P.gold,.14);
  drawWindow(d,t,{open:1,glass:.66,thread:.18});
  d.clipRect(L.x+L.side+18,L.y+L.head+8,L.w-L.side-36,L.h-L.head-L.compose-26,18,()=>{
    drawGPT(d,1025,140+Math.sin(t*1.2)*4,.69,{assemble:1,alpha:1,pose:t>10.25?'reply':'listen',look:-.08});
  });

  // The user's cursor is a true actor: it enters, clicks the composer, then yields the frame.
  const m=prog(t,7.0,8.25),cx=lerp(130,1535,easeInOut(m)),cy=lerp(870,887,easeInOut(m));
  cursor(d,cx,cy,{alpha:easeOut(prog(t,6.85,7.2))*(1-prog(t,9.7,10.05)),click:prog(t,8.20,8.55)});
  userBubble(d,t,8.0,userText);
  if(t>10.05)assistantBubble(d,t,10.05,replyText);

  // The reply does not remain a bubble. The interface geometry expands into the scene itself.
  const world=prog(t,11.25,14.30);
  if(world>0){
    const k=easeInOut(world),g=d.g;
    // peel the client open in three paper shutters
    d.alpha(k,()=>paperWorld(d,t,k));
    const shutter=1-k;
    if(shutter>.001){
      d.rrect(0,0,1920,245*shutter,0,{fill:P.paper,alpha:.95});
      d.rrect(0,1080-220*shutter,1920,220*shutter,0,{fill:P.paper2,alpha:.92});
      d.line(0,245*shutter,1920,245*shutter,{color:P.cobalt,width:4,alpha:.6*shutter});
    }
    // character moves from 'inside an app' to 'standing in the constructed world'.
    const px=lerp(1160,880,k),py=lerp(150,225,k),sc=lerp(.68,.78,k);
    drawGPT(d,px,py,sc,{assemble:1,alpha:k,pose:'reply',look:.05});
    const type=easeOut(prog(t,12.15,13.0));
    d.text('the window was only the beginning.',960,164,{size:52,font:'serif',italic:true,align:'center',color:P.ink,alpha:type*k});
  }

  // final hold keeps motion alive through light and paper drift, not a frozen title card.
  const hold=prog(t,14.25,15.0);
  if(hold>0)d.glow(1510,225,560,P.gold,.12+.16*hold);
}
