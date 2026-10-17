import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {drawGPT} from '../components/gpt.js';
import {cursor} from '../components/chat.js';

const HORIZON=590;
const NOTES=[
  'say it plainly',
  'check the edge',
  'leave room to ask',
  'keep the useful part',
  'try the quieter line',
  'make the shape simpler',
  'one honest sentence'
];

function withCamera(d,{zoom=1,x=0,y=0,rot=0}={},fn){
  d.save(()=>{
    d.g.translate(960,540);
    d.g.scale(zoom,zoom);
    d.g.rotate(rot);
    d.g.translate(-960+x,-540+y);
    fn();
  });
}

function sky(d,t,alpha=1){
  d.alpha(alpha,()=>d.gradRect(0,0,1920,1080,[[0,P.paper],[.52,'#eef3ff'],[1,'#ffe8b6']],true));
  d.glow(1510,225,480,P.gold,.33*alpha);
  d.circle(1510,225,90,{fill:P.gold2,alpha:.55*alpha});
  for(let i=0;i<6;i++){
    const yy=lerp(HORIZON,1080,i/5),spread=90+i*150;
    d.line(960-spread,yy,960+spread,yy,{color:i<2?P.cobalt:P.ink2,width:2+i*.35,alpha:(.16+.09*i)*alpha});
  }
  for(const x of [220,520,880,1260,1660])d.line(960,HORIZON,x,1080,{color:P.gold,width:2,alpha:.17*alpha});
}

function pageSpec(i){
  const w=86+(i%3)*22,h=105+((i*67)%205),x=120+i*245,y=HORIZON+48-h;
  return {x,y,w,h,blue:i%3===0};
}

function page(d,{x,y,w,h,rot=0,alpha=1,blue=false,text='',lines=true,shadow=.12,selected=0}){
  d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));
    if(selected>0)d.glow(x+w*.5,y+h*.45,Math.max(w,h)*.62,P.gold,.20*selected*alpha);
    d.rrect(x,y,w,h,10,{fill:blue?'rgba(235,242,255,.94)':'rgba(255,253,248,.96)',stroke:selected>0?P.gold:'rgba(53,65,92,.18)',width:selected>0?3:1.5,alpha,shadow:shadow*alpha});
    d.line(x+18,y+28,x+w-18,y+28,{color:blue?P.cobalt:P.gold,width:4,alpha:.50*alpha});
    if(lines){
      for(let r=0;r<3;r++)d.rrect(x+18,y+52+r*24,Math.max(20,w-36-(r%2)*18),7,4,{fill:blue?P.cobalt2:P.line,alpha:.26*alpha});
    }
    if(text&&w>190)d.text(text,x+22,y+64,{size:22,color:P.ink2,alpha:.82*alpha,font:'serif',italic:true});
  });
}

function skyline(d,alpha=1){
  for(let i=0;i<7;i++)page(d,{...pageSpec(i),alpha:.88*alpha,blue:i%3===0,shadow:.04});
}

function detachedPages(d,t){
  // Each skyline page owns its own trajectory into the revision room.
  const targets=[
    {x:170,y:180,w:300,h:190,r:-.10},
    {x:520,y:105,w:340,h:220,r:.06},
    {x:900,y:150,w:330,h:205,r:-.04},
    {x:1320,y:105,w:330,h:220,r:.08},
    {x:1500,y:410,w:300,h:190,r:-.06},
    {x:310,y:600,w:330,h:205,r:.07},
    {x:1180,y:610,w:350,h:215,r:-.08}
  ];
  for(let i=0;i<7;i++){
    const s=pageSpec(i),p=easeInOut(prog(t,15.35+i*.08,18.15+i*.05)),q=targets[i];
    const x=lerp(s.x,q.x,p),y=lerp(s.y,q.y,p),w=lerp(s.w,q.w,p),h=lerp(s.h,q.h,p),rot=lerp(0,q.r,p);
    page(d,{x,y,w,h,rot,alpha:.88,blue:s.blue,text:p>.72?NOTES[i]:'',shadow:lerp(.04,.30,p)});
  }
}

function revisionRoom(d,t){
  const u=t-18.2;
  const room=easeOut(prog(t,18.0,19.0));
  // Warm editorial field replaces the distant horizon without becoming a dashboard.
  d.alpha(room,()=>d.gradRect(0,0,1920,1080,[[0,'rgba(244,239,229,0)'],[1,'rgba(255,248,232,.82)']],true));
  d.glow(1080,480,610,P.cobalt,.07*room);

  const choice=easeInOut(prog(t,20.0,22.6));
  const chosen=3;
  const slots=[
    {x:130,y:170,w:410,h:245,r:-.10},
    {x:580,y:105,w:410,h:245,r:.055},
    {x:1030,y:155,w:410,h:245,r:-.035},
    {x:1280,y:500,w:430,h:260,r:.075},
    {x:120,y:590,w:400,h:235,r:.045},
    {x:700,y:650,w:420,h:245,r:-.055},
    {x:1460,y:160,w:340,h:220,r:.09}
  ];

  for(let i=0;i<7;i++){
    const s=slots[i],isChosen=i===chosen;
    const reject=isChosen?0:easeOut(prog(t,21.45+i*.035,23.15+i*.03));
    const fold=1-reject;
    const w=s.w*(isChosen?lerp(1,1.20,choice):Math.max(.035,fold));
    const x=isChosen?lerp(s.x,1110,choice):s.x+(1-fold)*(s.x<960?-300:300);
    const y=isChosen?lerp(s.y,360,choice):s.y-(1-fold)*90;
    const rot=isChosen?lerp(s.r,-.025,choice):s.r+(1-fold)*(s.x<960?-.35:.35);
    if(fold>.025||isChosen)page(d,{x,y,w,h:s.h*(isChosen?lerp(1,1.16,choice):1),rot,alpha:isChosen?1:fold,blue:i%3===0,text:NOTES[i],selected:isChosen?choice:0,shadow:.34});
  }

  // GPT shifts left as the selected page gains editorial weight on the right.
  const gx=lerp(750,430,choice),gy=lerp(190,235,choice),gs=lerp(.72,.76,choice);
  drawGPT(d,gx,gy+Math.sin(t*1.05)*3,gs,{assemble:1,alpha:1,pose:choice>.45?'reply':'think',look:choice>.45?.10:.04});

  // Coral is used only for revision: strike one phrase, then write the replacement.
  const edit=easeOut(prog(t,22.55,24.7));
  if(edit>0){
    const px=1110,py=360,pw=430*1.20,ph=260*1.16;
    d.text('keep the useful part',px+38,py+94,{size:30,font:'serif',italic:true,color:P.ink,alpha:edit});
    const strike=easeOut(prog(t,22.85,23.55));
    d.line(px+34,py+101,px+34+(pw-72)*strike,py+83,{color:P.coral,width:5,alpha:.76*strike});
    const rewrite=easeOut(prog(t,23.45,24.65));
    d.text('keep what matters.',px+38,py+154,{size:38,font:'serif',italic:true,color:P.ink,alpha:rewrite});
    d.line(px+38,py+172,px+38+310*rewrite,py+172,{color:P.gold,width:4,alpha:.62*rewrite});
  }
}

function handoff(d,t){
  const p=easeInOut(prog(t,24.8,28.65)),finish=easeOut(prog(t,28.55,29.7));
  // Selected page stretches into one continuous ribbon instead of cutting to a new prop.
  const x=lerp(1110,470,p),y=lerp(360,555,p),w=lerp(516,980,p),h=lerp(302,150,p),rot=lerp(-.025,-.015,p);
  page(d,{x,y,w,h,rot,alpha:1,blue:false,text:'',lines:false,selected:1-p*.55,shadow:.34});
  d.text('keep what matters.',x+48,y+h*.56,{size:lerp(38,44,p),font:'serif',italic:true,color:P.ink,alpha:1});
  d.line(x+46,y+h*.70,x+46+(w-95)*easeOut(prog(t,25.25,27.2)),y+h*.70,{color:P.gold,width:4,alpha:.62});

  const gx=lerp(430,255,p),gy=lerp(235,260,p),gs=lerp(.76,.68,p);
  drawGPT(d,gx,gy+Math.sin(t)*2,gs,{assemble:1,alpha:1,pose:'reply',look:.12});

  // User re-enters only for the handoff, preserving gold as the user's semantic color.
  const cx=lerp(1860,1500,easeOut(prog(t,26.7,28.25))),cy=lerp(760,650,easeOut(prog(t,26.7,28.25)));
  cursor(d,cx,cy,{alpha:easeOut(prog(t,26.55,27.0)),click:prog(t,28.05,28.48)});
  if(finish>0){
    d.glow(1500,650,190,P.gold,.28*finish);
    d.text('yours.',1540,735,{size:32,font:'serif',italic:true,color:P.ink2,alpha:.72*finish});
  }
}

export function renderDrafts(d,t){
  const local=t-15;
  const cameraPush=easeInOut(prog(t,15.0,18.15));
  const release=easeInOut(prog(t,18.0,19.2));
  const zoom=lerp(1,1.075,cameraPush)*(1-.035*release),panX=lerp(0,-30,cameraPush),panY=lerp(0,22,cameraPush);

  d.paper(t);
  withCamera(d,{zoom,x:panX,y:panY},()=>{
    const worldFade=1-smooth(prog(t,16.7,19.15));
    sky(d,t,worldFade);
    if(t<15.42)skyline(d,worldFade);
    if(t>=15.30&&t<19.1)detachedPages(d,t);
    if(t<18.35)drawGPT(d,850,225+Math.sin(t*1.1)*3,.78,{assemble:1,alpha:1,pose:'reply',look:.05});
  });

  if(t>=18.0&&t<25.35)revisionRoom(d,t);
  if(t>=24.75)handoff(d,t);

  // A thin cobalt rule at the end becomes the seed for the next gate.
  const end=easeOut(prog(t,29.35,30));
  if(end>0)d.line(1540,795,1540+260*end,795,{color:P.cobalt,width:3,alpha:.48*end});
}
