import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {cursor} from '../components/chat.js';
import {renderOpeningV5} from './opening_v5.js';

const BPM=116,OFF=.28,PB=60/BPM;
const B=n=>OFF+n*PB;
const C2=B(13),C3=B(20),END=15;
const P1={x:-170,y:30,w:1080,h:1000};
const WORLD_DST={x:735,y:65,w:1080,h:995};
const PROMPT={x:390,y:390,w:1290,h:280};

function base(d,t,{dark=.12,blue=.08,warm=.08}={}){
  d.paper(t*.32);
  d.glow(420,720,700,P.cobalt,blue);
  d.glow(1510,230,520,P.gold,warm);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[.55,`rgba(23,32,51,${dark*.32})`],[1,`rgba(23,32,51,${dark})`]],true);
}
function inkShelf(d,a=1){d.save(()=>{d.g.translate(-100,835);d.g.rotate(-.032);d.rect(0,0,820,300,{fill:P.ink,alpha:.095*a});d.line(80,62,670,62,{color:P.cobalt,width:7,alpha:.20*a});});}
function art(d,model,dst,{crop='full',alpha=1,register=0}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha});
  else model.draw(d.g,dst,{crop,alpha});
}
function typing(t){
  const a='make it impressive.',b='make it worth watching.',q=(t-C2)/PB;let s='',del=false;
  if(q<1.65)s=a.slice(0,Math.floor(prog(q,0,1.48)*a.length));
  else if(q<2.25)s=a;
  else if(q<3.25){s=a.slice(0,Math.ceil((1-prog(q,2.25,3.25))*a.length));del=true;}
  else if(q<3.72)s='';
  else s=b.slice(0,Math.floor(prog(q,3.72,6.35)*b.length));
  return{s,del,done:s===b};
}
function promptBox(d,t,typed,fold=0){
  const k=easeInOut(fold),x=lerp(PROMPT.x,500,k),y=lerp(PROMPT.y,510,k),w=lerp(PROMPT.w,1080,k),h=lerp(PROMPT.h,160,k);
  const shadow=easeOut(prog(t,C2,C2+.22));
  if(shadow>0)d.rrect(x+16,y+22,w,h,38,{fill:P.ink,alpha:.05*shadow});
  d.rrect(x,y,w,h,38,{fill:'rgba(255,253,248,.985)',stroke:'rgba(53,65,92,.18)',width:2,shadow:.55,alpha:1-.32*k});
  d.circle(x+60,y+58,16,{fill:P.gold,alpha:.92*(1-.25*k)});
  if(k<.45)d.text('you',x+92,y+67,{size:24,weight:700,color:P.ink2,alpha:.58*(1-k)});
  d.text(typed.s,x+58,y+lerp(168,98,k),{size:lerp(50,40,k),color:P.ink,weight:450,alpha:1-.18*k});
  const tw=d.measure(typed.s,{size:lerp(50,40,k)});
  if(Math.floor(t*3.2)%2===0&&k<.42)d.rect(x+62+tw,y+118,4,62,{fill:typed.del?P.coral:P.cobalt,alpha:.82});
  d.circle(x+w-76,y+h-64,30,{fill:typed.done?P.cobalt:P.line,alpha:.90*(1-.25*k)});
  if(typed.done&&k<.68){d.line(x+w-87,y+h-64,x+w-66,y+h-64,{color:P.white,width:4,alpha:1-k});d.line(x+w-67,y+h-64,x+w-76,y+h-73,{color:P.white,width:4,alpha:1-k});}
  return{x,y,w,h};
}

// One absolute flood function is used on both sides of C3.
function floodState(t){
  const k=easeInOut(prog(t,C3-.55,C3+.65));
  return{k,top:lerp(1140,-40,k)};
}
function flood(d,t){
  const f=floodState(t);
  if(f.k<=0)return f;
  d.rect(-30,f.top,1980,1180,{fill:P.ink,alpha:.995*f.k});
  d.line(0,f.top+36,1920,f.top+36,{color:P.cobalt2,width:3,alpha:.18*f.k});
  return f;
}
function sendState(t){return easeOut(prog(t,C3-.58,C3+.08));}
function stripGeom(i,t){
  const send=sendState(t),q=easeOut(prog(send,i*.045,.45+i*.04));
  const sx=620+i*98,sy=568+(i%3)*18,ex=500+i*138,ey=640+(i%2?55:-55);
  return{x:lerp(sx,ex,q),y:lerp(sy,ey,q),rot:lerp(0,(i-4)*.025,q),q};
}
function strip(d,i,t,alpha=1){
  const s=stripGeom(i,t);if(s.q<=0||alpha<=0)return;
  d.save(()=>{d.g.translate(s.x,s.y);d.g.rotate(s.rot);d.rrect(-86,-23,172,46,11,{fill:i%3===0?P.gold2:P.white,stroke:P.line,width:1.2,shadow:.18,alpha:s.q*alpha});});
}

function shotPrompt(d,t,model){
  const typed=typing(t),send=sendState(t);
  const intro=easeInOut(prog(t,C2,C2+.50));
  base(d,t,{dark:lerp(.14,.12,intro),blue:lerp(.12,.08,intro),warm:lerp(.12,.08,intro)});
  inkShelf(d,lerp(.9,.55,intro));
  // Exact C2 handoff: same P1 bust crop and registration as v5 context's final frame.
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,540,1080);d.g.clip();art(d,model,P1,{crop:'bust',alpha:.90+.10*(1-intro),register:lerp(7,5,intro)});});
  d.rect(0,0,540,1080,{fill:P.cobalt,alpha:.028*intro});
  const box=promptBox(d,t,typed,send);
  const key=Math.floor((t-C2)*12);
  for(let i=0;i<11;i++){
    const age=((key-i)+100)%11/11,a=.22*(1-age)*(1-send);
    d.rrect(box.x+105+(i*97)%930,box.y+box.h-22+age*68,25+(i%3)*15,4,2,{fill:typed.del?P.coral:P.gold,alpha:a});
  }
  const cx=lerp(1820,1588,easeInOut(prog(t,C2+.08,C2+.9))),cy=lerp(790,606,easeInOut(prog(t,C2+.08,C2+.9)));
  cursor(d,cx,cy,{alpha:(1-send)*easeOut(prog(t,C2+.05,C2+.35)),click:prog(t,C3-.31,C3-.05)});
  flood(d,t);
  for(let i=0;i<9;i++)strip(d,i,t,1);
}

function buildingPath(g,type,w,h){
  g.beginPath();
  if(type===0){g.roundRect(-w/2,-h,w,h,7);}
  else if(type===1){g.moveTo(-w/2,0);g.lineTo(-w/2,-h*.76);g.lineTo(0,-h);g.lineTo(w/2,-h*.76);g.lineTo(w/2,0);g.closePath();}
  else if(type===2){g.moveTo(-w/2,0);g.lineTo(-w/2,-h);g.lineTo(w*.18,-h);g.lineTo(w/2,-h*.72);g.lineTo(w/2,0);g.closePath();}
  else if(type===3){g.moveTo(-w/2,0);g.lineTo(-w/2,-h*.84);g.quadraticCurveTo(0,-h*1.05,w/2,-h*.84);g.lineTo(w/2,0);g.closePath();}
  else {g.moveTo(-w/2,0);g.lineTo(-w/2,-h*.55);g.lineTo(-w*.25,-h*.55);g.lineTo(-w*.25,-h*.72);g.lineTo(0,-h*.72);g.lineTo(0,-h*.88);g.lineTo(w*.26,-h*.88);g.lineTo(w*.26,-h);g.lineTo(w/2,-h);g.lineTo(w/2,0);g.closePath();}
}
function paperBuilding(d,i,t){
  const grow=easeInOut(prog(t,C3+.04+i*.04,C3+.84+i*.04));if(grow<=0)return 0;
  const start=stripGeom(i,t),x=lerp(start.x,180+i*188,grow),baseY=lerp(start.y,654,grow),w=lerp(172,106+(i%3)*28,grow),h=lerp(46,150+(i%4)*62,grow);
  d.save(()=>{
    const g=d.g;g.translate(x,baseY);g.rotate(lerp(start.rot,0,grow));
    g.save();g.translate(12,14);buildingPath(g,i%5,w,h*grow);g.fillStyle='#0b1322';g.globalAlpha=.24*grow;g.fill();g.restore();
    buildingPath(g,i%5,w,h*grow);g.fillStyle=i%3===0?'#f2d77d':'#ece6d9';g.globalAlpha=.97*grow;g.fill();g.strokeStyle='rgba(126,165,245,.28)';g.lineWidth=1.4;g.stroke();
    const yTop=-h*grow;
    g.globalAlpha=.55*grow;g.strokeStyle=i%3===0?P.gold:P.cobalt2;g.lineWidth=5;g.beginPath();g.moveTo(-w*.32,yTop+25);g.lineTo(w*.32,yTop+25);g.stroke();
    g.globalAlpha=.22*grow;g.strokeStyle=P.ink2;g.lineWidth=6;for(let j=0;j<4;j++){const yy=yTop+54+j*34;if(yy<-12){g.beginPath();g.moveTo(-w*.28,yy);g.lineTo(w*(.24-(j%2)*.05),yy);g.stroke();}}
    if(i%5===3&&h*grow>90){g.fillStyle=P.ink;g.globalAlpha=.72*grow;g.beginPath();g.arc(0,-24,Math.min(w*.2,22),Math.PI,0);g.lineTo(Math.min(w*.2,22),0);g.lineTo(-Math.min(w*.2,22),0);g.closePath();g.fill();}
  });
  return grow;
}

function shotWorld(d,t,model){
  base(d,t,{dark:.12,blue:.08,warm:.08});
  const f=flood(d,t);
  if(f.k>0){d.glow(1450,250,760,P.gold,.16*f.k);d.glow(520,720,760,P.cobalt,.18*f.k);}
  // Strips remain until the corresponding paper building has visibly taken over.
  for(let i=0;i<9;i++){const grow=easeInOut(prog(t,C3+.04+i*.04,C3+.84+i*.04));strip(d,i,t,1-grow);paperBuilding(d,i,t);}
  const horizon=easeOut(prog(t,C3+.18,C3+.80));
  d.line(0,654,1920,654,{color:P.gold2,width:3,alpha:.30*horizon*f.k});
  for(let i=0;i<6;i++){const q=easeOut(prog(t,C3+.30+i*.055,C3+.86+i*.055));d.line(960,654,lerp(960,100+i*355,q),1080,{color:i%2?P.gold:P.cobalt2,width:2.3,alpha:.18*q*f.k});}

  // Exact C3 handoff, then one continuous source-crop pull-back from bust to full.
  const move=easeInOut(prog(t,C3,C3+1.28)),pull=easeInOut(prog(t,C3+.20,C3+1.15)),clip=easeOut(prog(t,C3,C3+.72));
  const dst={x:lerp(P1.x,WORLD_DST.x,move),y:lerp(P1.y,WORLD_DST.y,move),w:lerp(P1.w,WORLD_DST.w,move),h:lerp(P1.h,WORLD_DST.h,move)};
  const crop=model.morphCrop('bust','full',pull);
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,lerp(540,1920,clip),1080);d.g.clip();art(d,model,dst,{crop,alpha:.98,register:lerp(5,7,move)});});

  const user=easeOut(prog(t,C3+.95,C3+1.42));
  if(user>0){d.glow(430,824,135,P.gold,.30*user);d.circle(430,824,11,{fill:P.gold,alpha:user});d.circle(430,824,35,{fill:null,stroke:P.gold2,width:2,alpha:.42*user});}
  const bridge=easeOut(prog(t,C3+1.15,C3+2.15));
  if(bridge>0)for(let i=0;i<7;i++){
    const q=easeOut(prog(bridge,i*.08,.42+i*.08)),x=lerp(920,455,i/6),y=lerp(760,820,i/6)-Math.sin(i/6*Math.PI)*65;
    d.save(()=>{d.g.translate(x,y);d.g.rotate(-.10+i*.025);d.rrect(-54*q,-17,108*q,34,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.90*q});});
  }
  const title=easeOut(prog(t,C3+1.32,C3+2.16));
  if(title>0){d.text('MAKE IT',112,152,{size:34,font:'mono',weight:700,color:P.cobalt2,alpha:.72*title});d.text('WORTH WATCHING.',110,224,{size:74,font:'serif',weight:700,color:P.white,alpha:.94*title});d.line(114,252,710,252,{color:P.gold,width:6,alpha:.64*title});}
  for(let i=0;i<3;i++){
    const q=prog(t,C3+.48+i*.18,END-.28+i*.06);if(q<=0||q>=1)continue;
    d.save(()=>{d.g.translate(lerp(-380,2100,easeInOut(q)),900-i*175);d.g.rotate(-.15+i*.08);d.rrect(0,0,380,150,12,{fill:P.white,stroke:P.line,width:1.2,alpha:.90,shadow:.35});d.line(34,42,292,42,{color:i===1?P.gold:P.cobalt,width:7,alpha:.55});});
  }
}

export function renderOpeningV6(d,t,model){
  if(t<C2)return renderOpeningV5(d,t,model);
  if(t<C3)return shotPrompt(d,t,model);
  return shotWorld(d,t,model);
}
export const OPENING_V6_CUTS=[0,B(6),C2,C3,END];
