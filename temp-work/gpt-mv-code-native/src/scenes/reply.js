import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {assistantBubble,cursor,drawWindow,L,userBubble} from '../components/chat.js';
import {drawGPT} from '../components/gpt.js';

const userText='make something only code can make.';
const replyText='Then watch the interface become a world.';

function paperWorld(d,t,k){
  const horizon=lerp(835,590,easeInOut(k));
  // Atmosphere is code-built and fades in beneath the transforming client grammar.
  d.alpha(k,()=>d.gradRect(0,0,1920,1080,[[0,P.paper],[.52,'#eef3ff'],[1,'#ffe8b6']],true));
  d.glow(1510,225,480,P.gold,.33*k);
  d.circle(1510,225,90,{fill:P.gold2,alpha:.55*k});

  // Perspective paper rails are the destination of the composer/header geometry.
  for(let i=0;i<6;i++){
    const yy=lerp(horizon,1080,i/5),spread=90+i*150;
    d.line(960-spread,yy,960+spread,yy,{color:i<2?P.cobalt:P.ink2,width:2+i*.35,alpha:(.16+.09*i)*k});
  }
  for(const x of [220,520,880,1260,1660])d.line(960,horizon,x,1080,{color:P.gold,width:2,alpha:.17*k});

  // Foreground sheets move independently, so the new space has actual depth.
  const scraps=[[-80,760,370,210,-.08],[1520,720,430,240,.07],[280,920,500,200,.03]];
  scraps.forEach(([x,y,w,h,r],i)=>d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(r+Math.sin(t*.45+i)*.01);d.g.translate(-(x+w/2),-(y+h/2));
    d.rrect(x,y,w,h,18,{fill:i===1?'rgba(47,102,213,.10)':'rgba(255,253,248,.84)',stroke:'rgba(53,65,92,.15)',alpha:k,shadow:.25*k});
    d.line(x+28,y+48,x+w-40,y+48,{color:i===1?P.cobalt:P.gold,width:5,alpha:.46*k});
  }));
  return horizon;
}

function morphClientIntoWorld(d,k,horizon){
  const q=easeInOut(k),reveal=easeOut(prog(k,.04,.34));
  const mixLine=(a,b,color,width=2,alpha=.55)=>d.line(
    lerp(a[0],b[0],q),lerp(a[1],b[1],q),lerp(a[2],b[2],q),lerp(a[3],b[3],q),
    {color,width,alpha:alpha*reveal}
  );

  // Header rule literally becomes the horizon.
  mixLine(
    [L.x+L.side,L.y+L.head,L.x+L.w-18,L.y+L.head],
    [110,horizon,1810,horizon],P.cobalt,3,.72
  );
  // Sidebar divider and composer edges become perspective rails.
  mixLine(
    [L.x+L.side,L.y+18,L.x+L.side,L.y+L.h-18],
    [960,horizon,250,1080],P.ink2,2.5,.44
  );
  const compX=L.x+L.side+62,compY=L.y+L.h-L.compose+27,compW=L.w-L.side-124;
  mixLine([compX,compY,compX+compW,compY],[960,horizon,1690,1080],P.gold,3,.52);
  mixLine([compX,compY+65,compX+compW,compY+65],[960,horizon,470,1080],P.cobalt2,2.5,.40);

  // Every sidebar conversation mark becomes one building/page in the skyline.
  for(let i=0;i<7;i++){
    const active=i===0;
    const sx=L.x+45,sy=L.y+82+i*72-5,sw=active?125:95+(i%3)*24,sh=10;
    const tw=86+(i%3)*22,th=105+((i*67)%205),tx=120+i*245,ty=horizon+48-th;
    const x=lerp(sx,tx,q),y=lerp(sy,ty,q),w=lerp(sw,tw,q),h=lerp(sh,th,q);
    const blue=i%3===0;
    d.rrect(x,y,w,h,lerp(5,8,q),{
      fill:blue?'rgba(47,102,213,.16)':'rgba(255,253,248,.78)',
      stroke:'rgba(53,65,92,.16)',alpha:(.52+.34*q)*reveal,shadow:.08*q
    });
    // The single sidebar stroke splits into page text as height appears.
    if(q>.36){
      const ta=smooth(prog(q,.36,.72));
      for(let r=0;r<3;r++)d.rect(x+15,y+23+r*31,w-30,7,{fill:blue?P.cobalt2:P.line,alpha:.19*ta});
    }
  }

  // A few registration circles detach from the app and become depth markers.
  for(let i=0;i<5;i++){
    const sx=L.x+L.w-66,sy=L.y+47;
    const tx=330+i*320,ty=horizon+120+(i%2)*115;
    d.circle(lerp(sx,tx,q),lerp(sy,ty,q),lerp(17,5,q),{fill:i%2?P.gold:P.cobalt,alpha:.30*reveal*(1-.35*q)});
  }
}

export function renderReply(d,t){
  const worldRaw=prog(t,11.25,14.30),k=easeInOut(worldRaw);
  const uiAlpha=1-smooth(prog(t,11.30,12.35));
  const messageAlpha=1-smooth(prog(t,11.18,12.00));
  const oldCharacter=1-smooth(prog(t,11.28,12.08));

  d.paper(t);
  d.glow(1320,340,520,P.gold,.14*uiAlpha);
  drawWindow(d,t,{open:1,glass:.66,thread:.18,alpha:uiAlpha});
  if(oldCharacter>0){
    d.clipRect(L.x+L.side+18,L.y+L.head+8,L.w-L.side-36,L.h-L.head-L.compose-26,18,()=>{
      drawGPT(d,1025,140+Math.sin(t*1.2)*4,.69,{assemble:1,alpha:oldCharacter,pose:t>10.25?'reply':'listen',look:-.08});
    });
  }

  // The user's cursor is an actor, not decoration.
  const m=prog(t,7.0,8.25),cx=lerp(130,1535,easeInOut(m)),cy=lerp(870,887,easeInOut(m));
  cursor(d,cx,cy,{alpha:easeOut(prog(t,6.85,7.2))*(1-prog(t,9.7,10.05))*messageAlpha,click:prog(t,8.20,8.55)});
  userBubble(d,t,8.0,userText,messageAlpha);
  if(t>10.05)assistantBubble(d,t,10.05,replyText,messageAlpha);

  if(worldRaw>0){
    const horizon=paperWorld(d,t,k);
    morphClientIntoWorld(d,k,horizon);

    // Two paper shutters use the former app boundaries, then leave the frame.
    const shutter=1-easeOut(prog(worldRaw,.04,.72));
    if(shutter>.001){
      d.rrect(0,0,1920,210*shutter,0,{fill:P.paper,alpha:.91});
      d.rrect(0,1080-185*shutter,1920,185*shutter,0,{fill:P.paper2,alpha:.88});
      d.line(0,210*shutter,1920,210*shutter,{color:P.cobalt,width:3,alpha:.42*shutter});
    }

    // New-world character enters only after the old in-window plate is gone: no accidental double exposure.
    const charIn=easeOut(prog(worldRaw,.40,.72));
    const px=lerp(1100,850,easeInOut(prog(worldRaw,.40,1))),py=lerp(185,225,easeInOut(prog(worldRaw,.40,1))),sc=lerp(.70,.78,easeInOut(prog(worldRaw,.40,1)));
    if(charIn>0)drawGPT(d,px,py,sc,{assemble:1,alpha:charIn,pose:'reply',look:.05});

    // Type grows out of the horizon instead of behaving like a subtitle plate.
    const type=easeOut(prog(t,12.55,13.25));
    if(type>0){
      d.line(625,170,1295,170,{color:P.gold,width:2,alpha:.20*type});
      d.text('the window was only the beginning.',960,150,{size:50,font:'serif',italic:true,align:'center',color:P.ink,alpha:type});
    }
  }

  const hold=prog(t,14.25,15.0);
  if(hold>0)d.glow(1510,225,560,P.gold,.12+.16*hold);
}
