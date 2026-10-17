import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth,beatPulse} from '../engine/timing.js';
import {cursor} from '../components/chat.js';

const BPM=116,OFF=.28,PB=60/BPM;
const B=n=>OFF+n*PB;
const C1=B(6),C2=B(13),C3=B(20),END=15;

function base(d,t,{blue=.12,warm=.10,dark=.15}={}){
  d.paper(t*.35);
  d.glow(390,700,700,P.cobalt,blue);
  d.glow(1530,240,520,P.gold,warm);
  d.gradRect(0,720,1920,360,[[0,'rgba(23,32,51,0)'],[.48,`rgba(23,32,51,${dark*.28})`],[1,`rgba(23,32,51,${dark})`]],true);
}
function camera(d,{zoom=1,x=0,y=0,rot=0}={},fn){d.save(()=>{const g=d.g;g.translate(960,540);g.scale(zoom,zoom);g.rotate(rot);g.translate(-960+x,-540+y);fn();});}
function card(d,{x,y,w=280,h=160,rot=0,accent=P.cobalt,label='',alpha=1,ink=.06}={}){
  d.save(()=>{const g=d.g;g.translate(x+w/2,y+h/2);g.rotate(rot);g.translate(-(x+w/2),-(y+h/2));
    d.rrect(x+12,y+18,w,h,18,{fill:P.ink,alpha:ink*alpha});
    d.rrect(x,y,w,h,18,{fill:'rgba(255,253,248,.96)',stroke:'rgba(53,65,92,.20)',width:1.5,alpha,shadow:.20});
    d.line(x+22,y+30,x+w-22,y+30,{color:accent,width:5,alpha:.62*alpha});
    if(label)d.text(label,x+22,y+70,{size:22,font:'mono',color:P.ink2,weight:600,alpha:.72*alpha});
    for(let i=0;i<3;i++)d.rrect(x+22,y+96+i*22,Math.max(34,w-48-(i%2)*38),7,4,{fill:P.line,alpha:.32*alpha});
  });
}
function inkForeground(d,t,a=1){
  const k=.5+.5*Math.sin(t*.55);
  d.save(()=>{d.g.translate(-60,820);d.g.rotate(-.035);d.rect(0,0,780,310,{fill:P.ink,alpha:.10*a});d.rect(80,60,590,8,{fill:P.cobalt,alpha:.25*a});});
  d.save(()=>{d.g.translate(1530,-100);d.g.rotate(.08);d.rect(0,0,470,310,{fill:P.gold,alpha:(.05+.025*k)*a});});
}
function artShadow(art,d,dst,{crop='full',alpha=.18,spread=14}={}){
  art.plate(d.g,{x:dst.x-spread,y:dst.y+spread*.55,w:dst.w,h:dst.h},{crop,color:P.ink,alpha});
  art.plate(d.g,{x:dst.x+spread*.7,y:dst.y-spread*.45,w:dst.w,h:dst.h},{crop,color:P.cobalt,alpha:alpha*.65});
  art.draw(d.g,dst,{crop,alpha:1});
}
function cropMarks(d,a=.34){const m=44,l=38;for(const [x,y,sx,sy] of [[m,m,1,1],[1876,m,-1,1],[m,1036,1,-1],[1876,1036,-1,-1]]){d.line(x,y,x+sx*l,y,{color:P.ink2,width:2,alpha:a});d.line(x,y,x,y+sy*l,{color:P.ink2,width:2,alpha:a});}}

function shotBuild(d,t,art){
  base(d,t,{blue:.08,warm:.08,dark:.11});inkForeground(d,t,.7);cropMarks(d,.25);
  const pulse=beatPulse(t,BPM,OFF);
  // Four physical rails arrive from four edges. They are the eventual window frame, not decorative lines.
  const rails=[
    [70,260,470,260,470,260,1530,260,P.cobalt],
    [1780,820,1450,820,1450,820,470,820,P.gold],
    [340,1010,340,800,340,800,340,260,P.ink2],
    [1630,80,1630,280,1630,280,1630,820,P.cobalt2],
  ];
  rails.forEach((r,i)=>{const k=easeOut(prog(t,.20+i*.13,1.0+i*.13));if(k<=0)return;const [x0,y0,x1,y1,x2,y2,x3,y3,c]=r;const m=k<.55?k/.55:1,n=k<.55?0:(k-.55)/.45;const ax=lerp(x0,x1,m),ay=lerp(y0,y1,m),bx=lerp(x2,x3,n),by=lerp(y2,y3,n);d.line(x0,y0,ax,ay,{color:c,width:3+1.8*pulse,alpha:.78});if(n>0)d.line(x2,y2,bx,by,{color:c,width:3,alpha:.78});});

  // Character is discovered behind the frame rather than popping in on the cut.
  const char=easeOut(prog(t,1.0,2.25));
  if(char>0){
    d.save(()=>{d.g.beginPath();d.g.roundRect(470,260,1160,560,28);d.g.clip();
      d.glow(1210,455,430,P.cobalt,.10*char);
      art.plate(d.g,{x:930,y:150,w:680,h:760},{crop:'bust',color:P.ink,alpha:.12*char});
      art.draw(d.g,{x:914,y:138,w:680,h:760},{crop:'bust',alpha:char});
    });
  }
  // Interface pieces land in front of her, one per half-beat.
  const pieces=[
    {x:500,y:294,w:270,h:132,rot:-.025,label:'context',accent:P.cobalt},
    {x:792,y:294,w:250,h:132,rot:.018,label:'memory',accent:P.ink2},
    {x:1060,y:294,w:245,h:132,rot:-.018,label:'tools',accent:P.gold},
    {x:1320,y:294,w:275,h:132,rot:.026,label:'style',accent:P.cobalt2},
  ];
  pieces.forEach((p,i)=>{const a=easeOut(prog(t,1.55+i*.18,2.05+i*.18));if(a>0)card(d,{...p,y:p.y-(1-a)*170,alpha:a});});
  const lock=easeOut(prog(t,C1-.48,C1-.06));
  if(lock>0){d.rrect(470,260,1160,560,28,{fill:null,stroke:P.ink2,width:lerp(5,1.5,lock),alpha:.45+.35*lock});for(const [x,y] of [[470,260],[1630,260],[470,820],[1630,820]])d.circle(x,y,28*(1-lock)+5,{fill:null,stroke:P.cobalt,width:3,alpha:.65*(1-lock)});}
  d.text('something coherent has to emerge.',88,958,{size:31,font:'serif',italic:true,color:P.ink2,alpha:.52*(1-smooth(prog(t,C1-.7,C1)))});
}

function shotContext(d,t,art){
  const u=prog(t,C1,C2),pack=easeInOut(prog(t,C2-.88,C2));
  base(d,t,{blue:.12,warm:.13,dark:.16});cropMarks(d,.20);inkForeground(d,t,.85);
  // Change photographic scale immediately: character is now a cropped foreground subject, not an icon inside a window.
  camera(d,{zoom:lerp(1.02,1.09,easeInOut(u)),x:lerp(30,-20,u),rot:lerp(-.006,.005,u)},()=>{
    art.plate(d.g,{x:-180,y:30,w:1080,h:1000},{crop:'bust',color:P.ink,alpha:.16});
    art.draw(d.g,{x:-200,y:10,w:1080,h:1000},{crop:'bust',alpha:1});
    d.glow(530,420,520,P.cobalt,.075);
    const defs=[
      {x:1010,y:120,w:330,h:180,r:-.055,l:'context',a:P.cobalt},
      {x:1390,y:230,w:310,h:170,r:.060,l:'tools',a:P.gold},
      {x:1090,y:600,w:345,h:185,r:.045,l:'memory',a:P.ink2},
      {x:1450,y:695,w:320,h:175,r:-.048,l:'style',a:P.cobalt2},
    ];
    defs.forEach((c,i)=>{
      const q=easeInOut(prog(t,C1+.10+i*.10,C2-1.05+i*.04));
      let x=lerp(c.x,c.x+(i%2?-120:105),q),y=c.y+Math.sin(q*Math.PI)*(i<2?150:-135),rot=lerp(c.r,-c.r*.38,q),w=c.w,h=c.h;
      if(pack>0){const slots=[0,.26,.52,.76];x=lerp(x,400+slots[i]*1110,pack);y=lerp(y,545,pack);w=lerp(w,245,pack);h=lerp(h,76,pack);rot=lerp(rot,0,pack);}
      if(q>0&&q<1&&!pack)for(let j=2;j>=1;j--)card(d,{x:x-j*19,y:y+j*(i%2?8:-8),w,h,rot,accent:c.a,alpha:.045});
      card(d,{x,y,w,h,rot,accent:c.a,label:pack>.25?'':c.l,alpha:.94,ink:.08});
    });
    // A paper sheet crosses close to lens. This gives the shot a real foreground plane.
    const fg=prog(t,C1+.45,C1+1.75);if(fg>0&&fg<1){d.save(()=>{d.g.translate(lerp(1960,-480,easeInOut(fg)),860);d.g.rotate(-.11);d.rrect(0,0,620,240,18,{fill:P.white,stroke:P.line,width:2,alpha:.98,shadow:.55});d.line(45,56,480,56,{color:P.gold,width:8,alpha:.65});});}
    if(pack>0){d.rrect(360,510,1250,160,32,{fill:'rgba(255,253,248,.96)',stroke:'rgba(53,65,92,.20)',width:2,shadow:.55,alpha:pack});d.circle(1510,590,30,{fill:P.cobalt,alpha:.85*pack});}
  });
  const a=easeOut(prog(t,C1+1.1,C2-1.0))*(1-pack);d.text('context is not the answer.',1220,948,{size:34,font:'serif',italic:true,align:'center',color:P.ink,alpha:.62*a});
}

function typing(t){
  const a='make it impressive.',b='make it worth watching.',q=(t-C2)/PB;let s='',del=false;
  if(q<1.65)s=a.slice(0,Math.floor(prog(q,0,1.48)*a.length));
  else if(q<2.25)s=a;
  else if(q<3.25){s=a.slice(0,Math.ceil((1-prog(q,2.25,3.25))*a.length));del=true;}
  else if(q<3.72)s='';
  else s=b.slice(0,Math.floor(prog(q,3.72,6.35)*b.length));
  return{s,del,done:s===b,final:b};
}

function shotPrompt(d,t,art){
  const u=prog(t,C2,C3),typed=typing(t),send=easeOut(prog(t,C3-.48,C3));
  base(d,t,{blue:.075,warm:.08,dark:.11});
  // The character is now only an edge-of-frame witness; the action belongs to the user's typing.
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,490,1080);d.g.clip();art.draw(d.g,{x:-420,y:150,w:980,h:880},{crop:'bust',alpha:.82});});
  d.rect(0,0,500,1080,{fill:P.cobalt,alpha:.035});
  camera(d,{zoom:lerp(1,1.07,easeInOut(u)),x:lerp(0,-30,u)},()=>{
    const x=390,y=390,w=1290,h=280;
    d.rrect(x+18,y+24,w,h,38,{fill:P.ink,alpha:.055});
    d.rrect(x,y,w,h,38,{fill:'rgba(255,253,248,.985)',stroke:'rgba(53,65,92,.18)',width:2,shadow:.58});
    d.circle(x+60,y+58,16,{fill:P.gold,alpha:.92});d.text('you',x+92,y+67,{size:24,weight:700,color:P.ink2,alpha:.58});
    d.text(typed.s,x+58,y+168,{size:50,color:P.ink,weight:450});
    const tw=d.measure(typed.s,{size:50});if(Math.floor(t*3.2)%2===0&&!send)d.rect(x+62+tw,y+118,4,62,{fill:typed.del?P.coral:P.cobalt,alpha:.82});
    d.circle(x+w-76,y+h-64,30,{fill:typed.done?P.cobalt:P.line,alpha:.90});
    if(typed.done){d.line(x+w-87,y+h-64,x+w-66,y+h-64,{color:P.white,width:4});d.line(x+w-67,y+h-64,x+w-76,y+h-73,{color:P.white,width:4});}
    const key=Math.floor((t-C2)*12);for(let i=0;i<11;i++){const age=((key-i)+100)%11/11,a=.22*(1-age)*(1-send);d.rrect(x+105+(i*107)%1040,y+h-22+age*70,26+(i%3)*16,4,2,{fill:typed.del?P.coral:P.gold,alpha:a});}
  });
  const cx=lerp(1820,1588,easeInOut(prog(t,C2+.08,C2+.9))),cy=lerp(790,606,easeInOut(prog(t,C2+.08,C2+.9)));cursor(d,cx,cy,{alpha:(1-send)*easeOut(prog(t,C2+.05,C2+.35)),click:prog(t,C3-.30,C3-.05)});
  // Send is not a fade: the composer breaks into nine physical strips whose positions continue in shot 4.
  if(send>0)for(let i=0;i<9;i++){const k=easeOut(prog(send,i*.045,.45+i*.04));const sx=560+i*112,sy=558+(i%3)*22,ex=500+i*138,ey=430+(i%2?88:-68);d.save(()=>{d.g.translate(lerp(sx,ex,k),lerp(sy,ey,k));d.g.rotate(lerp(0,(i-4)*.025,k));d.rrect(-92,-24,184,48,12,{fill:i%3===0?P.gold2:P.white,stroke:P.line,width:1.3,shadow:.18,alpha:k});});}
}

function shotWorld(d,t,art){
  const u=prog(t,C3,END),open=easeOut(prog(t,C3,C3+.72));
  // Start from the nine strips shot 3 ended with, then make them architecture.
  d.rect(0,0,1920,1080,{fill:P.ink});
  d.glow(1450,250,760,P.gold,.17*open);d.glow(560,690,760,P.cobalt,.20*open);
  // horizon + perspective rails, all grown from the send geometry.
  d.line(0,620,1920,620,{color:P.gold2,width:3,alpha:.38*open});
  for(let i=0;i<9;i++){
    const a=easeOut(prog(t,C3+i*.055,C3+.58+i*.055));if(a<=0)continue;
    const sx=500+i*138,sy=430+(i%2?88:-68),bx=250+i*180,bh=lerp(70,250+(i%4)*45,a),bw=120+(i%3)*34;
    d.save(()=>{d.g.translate(lerp(sx,bx,a),lerp(sy,620-bh,a));d.g.rotate(lerp((i-4)*.025,0,a));d.rrect(-bw/2,0,bw,bh,8,{fill:i%3===0?P.gold2:P.paper2,stroke:i%2?P.cobalt2:P.line,width:1.5,alpha:.92,shadow:.25});for(let j=0;j<4;j++)d.rrect(-bw*.28,34+j*38,bw*.56-(j%2)*18,7,3,{fill:P.ink2,alpha:.18*a});});
  }
  for(let i=0;i<6;i++){const k=easeOut(prog(t,C3+.25+i*.06,C3+.72+i*.06));d.line(960,620,lerp(960,120+i*340,k),1080,{color:i%2?P.gold:P.cobalt2,width:2.5,alpha:.22*k});}

  // First time the reaching pose owns the frame. She is no longer a sticker in an interface.
  const enter=easeOut(prog(t,C3+.24,C3+1.05)),breath=Math.sin(t*1.4)*5;
  if(enter>0){
    art.plate(d.g,{x:760-22*(1-enter),y:88+breath,w:1050,h:970},{crop:'full',color:P.ink,alpha:.20*enter});
    art.draw(d.g,{x:742-22*(1-enter),y:72+breath,w:1050,h:970},{crop:'full',alpha:enter});
  }
  // User is a single gold point at the end of her gesture, not another body.
  const user=easeOut(prog(t,C3+.8,C3+1.35));if(user>0){d.glow(460,810,130,P.gold,.32*user);d.circle(460,810,11,{fill:P.gold,alpha:user});d.circle(460,810,34,{fill:null,stroke:P.gold2,width:2,alpha:.42*user});}
  const title=easeOut(prog(t,C3+1.15,C3+2.1));if(title>0){d.text('WORTH WATCHING',118,170,{size:78,font:'serif',weight:700,color:P.white,alpha:.92*title});d.line(122,198,690,198,{color:P.cobalt2,width:6,alpha:.72*title});}
  // Foreground papers pass between camera and subject for depth.
  for(let i=0;i<3;i++){const q=prog(t,C3+.45+i*.18,END-.25+i*.08);if(q>0&&q<1){d.save(()=>{d.g.translate(lerp(-340,2100,easeInOut(q)),840-i*170);d.g.rotate(-.16+i*.08);d.rrect(0,0,360,150,12,{fill:P.white,stroke:P.line,width:1.2,alpha:.88,shadow:.35});d.line(34,42,280,42,{color:i===1?P.gold:P.cobalt,width:7,alpha:.55});});}}
}

export function renderOpeningV4(d,t,art){
  if(t<C1)return shotBuild(d,t,art);
  if(t<C2)return shotContext(d,t,art);
  if(t<C3)return shotPrompt(d,t,art);
  return shotWorld(d,t,art);
}

export const OPENING_V4_CUTS=[0,C1,C2,C3,END];
