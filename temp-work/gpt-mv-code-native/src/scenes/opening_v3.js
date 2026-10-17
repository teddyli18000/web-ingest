import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth,beatPulse} from '../engine/timing.js';
import {drawGPT} from '../components/gpt.js';
import {cursor,L} from '../components/chat.js';

const BPM=116, OFF=.28, PB=60/BPM;
const B=n=>OFF+n*PB;
const C1=B(6), C2=B(13), C3=B(20), END=15;
const COMPOSER={x:330,y:388,w:1260,h:236};

function camera(d,{zoom=1,x=0,y=0,rot=0}={},fn){d.save(()=>{const g=d.g;g.translate(960,540);g.scale(zoom,zoom);g.rotate(rot);g.translate(-960+x,-540+y);fn();});}
function base(d,t,{warm=.14,blue=.08,ink=.04}={}){
  d.paper(t);
  d.glow(1480,220,600,P.gold,warm);
  d.glow(430,720,620,P.cobalt,blue);
  d.gradRect(0,800,1920,280,[[0,'rgba(23,32,51,0)'],[.62,`rgba(23,32,51,${ink})`],[1,`rgba(23,32,51,${ink*2.1})`]],true);
}
function registerGPT(d,x,y,s,opts={}){
  drawGPT(d,x-14,y+8,s,{...opts,alpha:(opts.alpha??1)*.06,look:(opts.look??0)-.03});
  drawGPT(d,x+10,y-5,s,{...opts,alpha:(opts.alpha??1)*.045,look:(opts.look??0)+.03});
  drawGPT(d,x,y,s,opts);
}
function card(d,{x,y,w,h,rot=0,alpha=1,label='',accent=P.cobalt,heavy=0}){
  d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));
    if(heavy)d.rect(x-8,y+h*.64,w+16,h*.40,{fill:P.ink,alpha:.035*heavy});
    d.rrect(x,y,w,h,18,{fill:'rgba(255,253,248,.95)',stroke:'rgba(53,65,92,.18)',width:1.5,alpha,shadow:.28});
    d.line(x+20,y+30,x+w-22,y+30,{color:accent,width:4,alpha:.56*alpha});
    if(label)d.text(label,x+22,y+68,{size:22,font:'mono',color:P.ink2,alpha:.72*alpha});
    for(let i=0;i<3;i++)d.rrect(x+22,y+92+i*26,Math.max(36,w-44-(i%2)*32),7,4,{fill:P.line,alpha:.30*alpha});
  });
}
function crop(d,a=.35){const m=42,l=45;for(const [x,y,sx,sy] of [[m,m,1,1],[1878,m,-1,1],[m,1038,1,-1],[1878,1038,-1,-1]]){d.line(x,y,x+sx*l,y,{color:P.ink2,width:2,alpha:a});d.line(x,y,x,y+sy*l,{color:P.ink2,width:2,alpha:a});}}

function drawComposer(d,t,{alpha=1,text='',deleting=false,ready=false,fold=0}={}){
  const q=easeInOut(fold),x=lerp(COMPOSER.x,470,q),y=lerp(COMPOSER.y,548,q),w=lerp(COMPOSER.w,980,q),h=lerp(COMPOSER.h,148,q);
  d.rrect(x,y,w,h,lerp(36,18,q),{fill:'rgba(255,255,255,.88)',stroke:'rgba(53,65,92,.18)',width:2,alpha,shadow:.66});
  d.circle(x+54,y+54,15,{fill:P.gold,alpha:.86*alpha});
  if(q<.55)d.text('you',x+84,y+64,{size:23,weight:650,color:P.ink2,alpha:.52*alpha*(1-q)});
  if(text)d.text(text,x+54,y+lerp(146,88,q),{size:lerp(48,38,q),color:P.ink,alpha:.95*alpha});
  const tw=d.measure(text,{size:lerp(48,38,q)});
  if(q<.45&&Math.floor(t*3.2)%2===0)d.rect(x+58+tw,y+104,4,58,{fill:deleting?P.coral:P.cobalt,alpha:.74*alpha*(1-q)});
  d.circle(x+w-66,y+h-58,25,{fill:ready?P.cobalt:P.line,alpha:.86*alpha});
  if(ready){d.line(x+w-75,y+h-58,x+w-57,y+h-58,{color:P.white,width:3,alpha});d.line(x+w-58,y+h-58,x+w-66,y+h-66,{color:P.white,width:3,alpha});}
  return{x,y,w,h};
}

function shot1(d,t){
  base(d,t,{warm:.12,blue:.055,ink:.05});crop(d,.28);
  const pulse=beatPulse(t,BPM,OFF),fadeText=1-smooth(prog(t,C1-.9,C1));
  const frame=easeInOut(prog(t,B(2.2),C1-.1));
  const fx=lerp(430,L.x,frame),fy=lerp(250,L.y,frame),fw=lerp(1060,L.w,frame),fh=lerp(570,L.h,frame);

  // Four incoming strands occupy different depth planes.
  const strands=[[80,230,760,455,P.cobalt,0],[1840,210,1160,450,P.gold,.12],[180,925,760,635,P.ink2,.24],[1760,900,1160,630,P.cobalt2,.36]];
  strands.forEach(([x1,y1,x2,y2,c,dl],i)=>{
    const k=easeOut(prog(t,B(0)+dl,B(0)+.55+dl));if(k<=0)return;
    const x=lerp(x1,x2,k),y=lerp(y1,y2,k);
    d.line(x1,y1,x,y,{color:c,width:3+pulse*1.4,alpha:.72});
    d.circle(x,y,5+pulse*2,{fill:c,alpha:.75});
    if(i<2)d.line(x,y,960,540,{color:c,width:1.2,alpha:.11*k});
  });

  // Cards arrive on alternating beats, then become part of the next shot's orbit.
  const defs=[
    {x:250,y:150,w:280,h:158,r:-.085,l:'context',a:P.cobalt},
    {x:1390,y:165,w:278,h:158,r:.075,l:'tools',a:P.gold},
    {x:285,y:760,w:300,h:166,r:.058,l:'memory',a:P.ink2},
    {x:1360,y:745,w:310,h:172,r:-.052,l:'style',a:P.cobalt2}
  ];
  defs.forEach((c,i)=>{const a=easeOut(prog(t,B(1.7)+i*.12,B(1.7)+.46+i*.12));if(a>0)card(d,{x:c.x,y:c.y+(1-a)*(i<2?-190:190),w:c.w,h:c.h,rot:c.r,alpha:a,label:c.l,accent:c.a});});

  d.rrect(fx,fy,fw,fh,lerp(56,L.r,frame),{fill:'rgba(255,255,255,.46)',stroke:'rgba(47,102,213,.27)',width:2.5,alpha:.94,shadow:.45*frame});
  if(frame>.2){const a=smooth(prog(frame,.2,.8));d.line(fx+lerp(0,L.side,frame),fy+26,fx+lerp(0,L.side,frame),fy+fh-26,{color:P.line,width:2,alpha:.55*a});}

  // Crucial continuity: GPT begins printing before the first cut.
  const char=easeOut(prog(t,C1-.75,C1-.08));
  if(char>0){
    d.clipRect(L.x+L.side+10,L.y+16,L.w-L.side-24,L.h-32,22,()=>{
      d.glow(1080,470,420,P.cobalt,.10*char);
      registerGPT(d,780,120,.76,{assemble:char,alpha:char,pose:'think',look:-.10});
    });
  }
  d.text('four things enter. one reply has to hold them together.',960,958,{size:28,font:'serif',italic:true,align:'center',color:P.ink2,alpha:.46*fadeText});
}

function shot2(d,t){
  const u=prog(t,C1,C2),toComp=easeInOut(prog(t,C2-.78,C2));
  base(d,t,{warm:.16,blue:.075,ink:.065});crop(d,.24*(1-toComp));
  camera(d,{zoom:lerp(1.02,.96,easeInOut(u)),rot:lerp(-.01,.006,u),y:lerp(10,-10,u)},()=>{
    // same frame as shot 1 at entry; it opens into a working surface.
    d.rrect(L.x,L.y,L.w,L.h,L.r,{fill:'rgba(255,255,255,.52)',stroke:'rgba(47,102,213,.25)',width:2,alpha:.96*(1-.55*toComp),shadow:.52});
    d.rect(L.x+L.side,L.y+L.head,L.w-L.side,L.h-L.head,{fill:P.cobalt,alpha:.018*(1-toComp)});

    const gx=lerp(780,300,toComp),gy=lerp(120,214,toComp),gs=lerp(.76,.55,toComp);
    registerGPT(d,gx,gy+Math.sin(t*1.2)*3,gs,{assemble:1,alpha:1,pose:u>.52?'listen':'think',look:lerp(-.10,.08,u)});

    const defs=[
      {sx:250,sy:150,ex:1185,ey:180,w:280,h:158,r0:-.085,r1:.03,l:'context',a:P.cobalt},
      {sx:1390,sy:165,ex:1360,ey:420,w:278,h:158,r0:.075,r1:-.05,l:'tools',a:P.gold},
      {sx:285,sy:760,ex:1175,ey:700,w:300,h:166,r0:.058,r1:.025,l:'memory',a:P.ink2},
      {sx:1360,sy:745,ex:735,ey:720,w:310,h:172,r0:-.052,r1:-.03,l:'style',a:P.cobalt2}
    ];
    defs.forEach((c,i)=>{
      const q=easeInOut(prog(t,C1+.12+i*.09,C2-1.05+i*.04));
      let x=lerp(c.sx,c.ex,q),y=lerp(c.sy,c.ey,q)+Math.sin(q*Math.PI)*(i%2?-125:125),w=c.w,h=c.h,rot=lerp(c.r0,c.r1,q);
      if(toComp>0){
        const slots=[0,.27,.53,.76],slot=slots[i];
        x=lerp(x,COMPOSER.x+60+slot*(COMPOSER.w-340),toComp);y=lerp(y,COMPOSER.y+36,toComp);
        w=lerp(w,250,toComp);h=lerp(h,72,toComp);rot=lerp(rot,0,toComp);
      }
      if(q>0&&q<1&&!toComp)for(let g=2;g>=1;g--)card(d,{x:x-g*20,y:y+(i%2?g*8:-g*8),w,h,rot,alpha:.045,label:'',accent:c.a});
      card(d,{x,y,w,h,rot,alpha:.92,label:toComp>.35?'':c.l,accent:c.a});
    });

    const spine=easeOut(prog(t,C1+1.15,C2-.72))*(1-toComp);
    if(spine>0){d.line(1080,190,1080,845,{color:P.cobalt,width:5,alpha:.19*spine});for(let i=0;i<8;i++){const a=easeOut(prog(t,C1+1.25+i*.09,C1+1.65+i*.09));d.circle(1080,265+i*68,6,{fill:i%2?P.gold:P.cobalt,alpha:.55*a*spine});d.line(1100,265+i*68,1100+135*a,265+i*68,{color:P.line,width:7,alpha:.30*a*spine});}}

    // The cards don't vanish: a composer grows around their final positions.
    if(toComp>0)drawComposer(d,t,{alpha:toComp,text:'',ready:false});
  });
  const a=easeOut(prog(t,C2-.9,C2-.28))*(1-toComp);
  if(a>0)d.text('what should this become?',960,956,{size:35,font:'serif',italic:true,align:'center',color:P.ink,alpha:.72*a});
}

function typedText(t){
  const falseText='make it impressive.',realText='make it worth watching.',b=(t-C2)/PB;let text='',del=false;
  if(b<1.7)text=falseText.slice(0,Math.floor(prog(b,0,1.55)*falseText.length));
  else if(b<2.25)text=falseText;
  else if(b<3.25){text=falseText.slice(0,Math.ceil((1-prog(b,2.25,3.25))*falseText.length));del=true;}
  else if(b<3.65)text='';
  else text=realText.slice(0,Math.floor(prog(b,3.65,6.4)*realText.length));
  return{text,del,realText};
}

function shot3(d,t){
  const u=prog(t,C2,C3),send=easeOut(prog(t,C3-.52,C3)),typed=typedText(t),ready=typed.text===typed.realText;
  base(d,t,{warm:.11,blue:.06,ink:.055});

  // Character stays where shot 2 placed it, then grows toward the next shot.
  const gx=lerp(300,380,send),gy=lerp(214,175,send),gs=lerp(.55,.68,send);
  d.save(()=>{d.clipRect(0,0,690,1080,0,()=>{registerGPT(d,gx,gy,gs,{assemble:1,alpha:.95,pose:send>.35?'reply':'listen',look:lerp(.08,.12,send)});});});

  camera(d,{zoom:lerp(1.0,1.08,easeInOut(u)),x:lerp(0,-35,u)},()=>{
    const fold=send;
    const box=drawComposer(d,t,{alpha:1-fold*.18,text:typed.text,deleting:typed.del,ready,fold});
    // physical type debris gives keystrokes weight.
    const n=Math.floor((t-C2)*12);for(let i=0;i<10;i++){const age=((n-i)+100)%10/10,a=.24*(1-age)*(1-send),xx=box.x+100+(i*113)%900;d.rrect(xx,box.y+box.h-28+age*55,25+(i%3)*14,4,2,{fill:typed.del?P.coral:P.gold,alpha:a});}
  });

  const cx=lerp(1760,1518,easeInOut(prog(t,C2+.1,C2+1.0))),cy=lerp(780,568,easeInOut(prog(t,C2+.1,C2+1.0)));
  cursor(d,cx,cy,{alpha:easeOut(prog(t,C2+.08,C2+.4))*(1-send),click:prog(t,C3-.35,C3-.06)});

  // Composer folds into the exact strips used by shot 4.
  if(send>0){
    for(let i=0;i<9;i++){
      const a=easeOut(prog(send,i*.045,.42+i*.045));
      const sx=620+i*88,sy=608+(i%3)*19;
      const ex=720+i*82,ey=560+(i%2?42:-30);
      const x=lerp(sx,ex,a),y=lerp(sy,ey,a),rot=lerp(0,(i-4)*.025,a);
      d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(-82,-24,164,48,12,{fill:'rgba(255,253,248,.96)',stroke:'rgba(53,65,92,.14)',alpha:a,shadow:.18});d.rrect(-65,-4,36,8,4,{fill:i%3?P.cobalt:P.gold,alpha:.44*a});});
    }
  }
}

function strip(d,x,y,w,h,rot,alpha,label,accent){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(-w/2,-h/2,w,h,13,{fill:'rgba(255,253,248,.96)',stroke:'rgba(53,65,92,.14)',alpha,shadow:.22});d.rrect(-w/2+14,-5,36,10,5,{fill:accent,alpha:.48*alpha});if(label)d.text(label,-w/2+58,8,{size:20,font:'serif',italic:true,color:P.ink2,alpha:.72*alpha});});}

function shot4(d,t){
  const u=prog(t,C3,END),cam=easeInOut(prog(t,C3+.45,END));
  base(d,t,{warm:.22,blue:.10,ink:.10});
  // Stronger depth masses: a cut-paper sun, an ink floor, and foreground rails.
  const sun=easeOut(prog(t,C3+.4,C3+1.1));d.circle(1570,170,lerp(40,165,sun),{fill:P.gold2,alpha:.36*sun});
  d.rect(0,875,1920,205,{fill:P.ink,alpha:.055+.045*cam});
  d.line(0,874,1920,874,{color:P.cobalt,width:3,alpha:.22});

  camera(d,{zoom:lerp(1.02,1.18,cam),x:lerp(0,-115,cam),y:lerp(0,24,cam),rot:lerp(0,.012,cam)},()=>{
    const gx=lerp(380,305,cam),gy=lerp(175,205,cam),gs=lerp(.68,.72,cam);
    registerGPT(d,gx,gy+Math.sin(t)*3,gs,{assemble:1,alpha:1,pose:'reply',look:.13});

    const words=['make','it','worth','watching','show','the','work','between','us'];
    words.forEach((w,i)=>{
      const start=C3+i*.10,q=easeInOut(prog(t,start,start+2.25));
      const sx=720+i*82,sy=560+(i%2?42:-30),ex=720+(i%5)*225,ey=170+Math.floor(i/5)*435+(i%2)*42;
      const x=lerp(sx,ex,q),y=lerp(sy,ey,q)-250*Math.sin(q*Math.PI),rot=lerp((i-4)*.025,i%2?-.07:.055,q);
      if(q>.08&&q<.94){strip(d,x-34,y+18,145+w.length*9,48,rot,.045,'',i%3?P.cobalt:P.gold);strip(d,x-17,y+9,145+w.length*9,48,rot,.075,'',i%3?P.cobalt:P.gold);}
      strip(d,x,y,145+w.length*9,48,rot,.96,w,i%3?P.cobalt:P.gold);
    });

    const build=easeOut(prog(t,C3+2.05,END-.30));
    if(build>0){
      const planes=[{x:705,y:150,w:490,h:250,r:-.04,l:'question',a:P.cobalt},{x:1230,y:255,w:440,h:305,r:.055,l:'draft',a:P.gold},{x:855,y:645,w:650,h:250,r:.016,l:'answer',a:P.ink2}];
      planes.forEach((p,i)=>{const a=easeOut(prog(t,C3+2.0+i*.16,C3+2.55+i*.16));card(d,{x:p.x,y:p.y+(1-a)*145,w:p.w,h:p.h,rot:p.r,alpha:.90*a,label:p.l,accent:p.a,heavy:1});});
      // foreground rails arrive toward camera independently.
      for(let i=0;i<6;i++){const a=easeOut(prog(t,C3+2.45+i*.07,END-.05));d.line(400+i*120,1030,790+i*125,785,{color:i%2?P.gold:P.cobalt,width:3,alpha:.20*a});}
    }
  });

  const end=easeOut(prog(t,END-.72,END-.08));
  if(end>0){d.rrect(650,948,620,58,24,{fill:'rgba(255,253,248,.72)',stroke:'rgba(53,65,92,.10)',alpha:.70*end});d.text('the reply is built in front of you.',960,987,{size:30,font:'serif',italic:true,align:'center',color:P.ink2,alpha:.68*end});}
}

export function renderOpeningV3(d,t){if(t<C1)shot1(d,t);else if(t<C2)shot2(d,t);else if(t<C3)shot3(d,t);else shot4(d,t);}
export const OPENING_V3={bpm:BPM,offset:OFF,cuts:[0,C1,C2,C3,END]};
