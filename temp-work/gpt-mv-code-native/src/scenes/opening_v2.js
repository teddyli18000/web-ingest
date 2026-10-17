import {PALETTE as P} from '../engine/palette.js';
import {back,easeInOut,easeOut,lerp,prog,smooth,pulse,beatPulse} from '../engine/timing.js';
import {drawGPT} from '../components/gpt.js';
import {cursor,L} from '../components/chat.js';

const BPM=116, OFF=.28, PBEAT=60/BPM;
const B=n=>OFF+n*PBEAT;
const CUT1=B(6), CUT2=B(13), CUT3=B(20), END=15;

function camera(d,{zoom=1,x=0,y=0,rot=0}={},fn){
  const g=d.g;
  d.save(()=>{g.translate(960,540);g.scale(zoom,zoom);g.rotate(rot);g.translate(-960+x,-540+y);fn();});
}

function room(d,t,{warm=.12,blue=.07,grain=1}={}){
  d.paper(t*grain);
  d.glow(1450,250,520,P.gold,warm);
  d.glow(480,710,600,P.cobalt,blue);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[.6,'rgba(23,32,51,.04)'],[1,'rgba(23,32,51,.10)']],true);
}

function cropMarks(d,a=1){
  const m=46,l=42;
  for(const [x,y,sx,sy] of [[m,m,1,1],[1920-m,m,-1,1],[m,1080-m,1,-1],[1920-m,1080-m,-1,-1]]){
    d.line(x,y,x+sx*l,y,{color:P.ink2,width:2,alpha:.26*a});
    d.line(x,y,x,y+sy*l,{color:P.ink2,width:2,alpha:.26*a});
  }
}

function paperCard(d,{x,y,w,h,rot=0,alpha=1,accent=P.cobalt,fill='rgba(255,253,248,.94)',shadow=.22,label='',lines=3}){
  d.save(()=>{
    d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));
    d.rrect(x,y,w,h,18,{fill,stroke:'rgba(53,65,92,.16)',width:1.5,alpha,shadow});
    d.line(x+22,y+32,x+w-24,y+32,{color:accent,width:4,alpha:.48*alpha});
    if(label)d.text(label,x+24,y+70,{size:22,font:'mono',color:P.ink2,alpha:.68*alpha});
    for(let i=0;i<lines;i++)d.rrect(x+24,y+94+i*27,Math.max(28,w-48-(i%2)*34),7,4,{fill:P.line,alpha:.28*alpha});
  });
}

function thread(d,x1,y1,x2,y2,t0,t,{color=P.cobalt,width=4,delay=0}){
  const k=easeOut(prog(t,t0+delay,t0+delay+.42));
  if(k<=0)return;
  const mx=lerp(x1,x2,k),my=lerp(y1,y2,k);
  d.line(x1,y1,mx,my,{color,width,alpha:.70});
  d.glow(mx,my,36,color,.18*(1-k));
}

function frameFromThreads(d,t){
  const q=easeInOut(prog(t,B(3),CUT1-.12));
  const x=lerp(420,L.x,q),y=lerp(260,L.y,q),w=lerp(1080,L.w,q),h=lerp(560,L.h,q),r=lerp(54,L.r,q);
  d.rrect(x,y,w,h,r,{fill:'rgba(255,255,255,.45)',stroke:'rgba(47,102,213,.28)',width:2.5,alpha:.92,shadow:.42*q});
  if(q>.15){
    const a=smooth(prog(q,.15,.72));
    d.line(lerp(960,x+L.side,q),y+24,lerp(960,x+L.side,q),y+h-24,{color:P.line,width:2,alpha:.62*a});
    d.line(x+L.side,y+lerp(280,L.head,q),x+w-22,y+lerp(280,L.head,q),{color:P.line,width:2,alpha:.55*a});
  }
}

function shotThreads(d,t){
  room(d,t,{warm:.10,blue:.045});cropMarks(d,easeOut(prog(t,.1,.8)));
  const k=easeOut(prog(t,.18,.9)),bp=beatPulse(t,BPM,OFF);
  d.text('a conversation starts before either side speaks.',960,904,{size:26,font:'serif',italic:true,align:'center',color:P.ink2,alpha:.40*k});

  const starts=[
    [120,270,790,470,P.cobalt,0],
    [1800,235,1120,455,P.gold,.12],
    [250,900,790,610,P.ink2,.24],
    [1720,890,1145,615,P.cobalt2,.36]
  ];
  for(const [x1,y1,x2,y2,c,delay] of starts)thread(d,x1,y1,x2,y2,B(0),t,{color:c,width:3+bp*1.5,delay});

  const cross=easeOut(prog(t,B(1),B(2.6)));
  if(cross>0){
    const pts=[[790,470],[1120,455],[790,610],[1145,615]];
    for(let i=0;i<pts.length;i++){
      const [x,y]=pts[i],r=10+6*Math.sin((t-B(1))*5+i);
      d.circle(x,y,r,{fill:i%2?P.gold:P.cobalt,alpha:.75*cross});
      d.circle(x,y,r+13,{fill:null,stroke:P.line,width:2,alpha:.28*cross});
    }
  }

  const cardIn=easeOut(prog(t,B(2),B(4.4)));
  if(cardIn>0){
    const cards=[
      {x:310,y:160,w:270,h:150,rot:-.08,label:'context',accent:P.cobalt},
      {x:1340,y:190,w:270,h:150,rot:.07,label:'tools',accent:P.gold},
      {x:330,y:740,w:290,h:160,rot:.055,label:'memory',accent:P.ink2},
      {x:1320,y:735,w:300,h:165,rot:-.05,label:'style',accent:P.cobalt2}
    ];
    cards.forEach((c,i)=>{
      const a=easeOut(prog(t,B(2)+i*.11,B(2)+.42+i*.11));
      const fly=(1-a)*(i<2?-160:180);
      paperCard(d,{...c,y:c.y+fly,alpha:a*cardIn,shadow:.26});
    });
  }

  frameFromThreads(d,t);
  const snap=easeOut(prog(t,CUT1-.36,CUT1));
  if(snap>0){
    for(const [x,y] of [[L.x,L.y],[L.x+L.w,L.y],[L.x,L.y+L.h],[L.x+L.w,L.y+L.h]]){
      d.circle(x,y,24*(1-snap)+4,{fill:null,stroke:P.cobalt,width:3,alpha:.6*(1-snap)});
    }
  }
}

function contextOrbit(d,t){
  const u=prog(t,CUT1,CUT2),settle=easeOut(prog(t,CUT1,CUT1+.65));
  room(d,t,{warm:.14,blue:.06});cropMarks(d,.7);
  const zoom=lerp(1.06,.96,easeInOut(u)),rot=lerp(-.014,.008,easeInOut(u));
  camera(d,{zoom,rot,y:lerp(18,-8,u)},()=>{
    d.rrect(L.x,L.y,L.w,L.h,L.r,{fill:'rgba(255,255,255,.50)',stroke:'rgba(47,102,213,.24)',width:2,alpha:.95,shadow:.5});
    d.line(L.x+L.side,L.y+26,L.x+L.side,L.y+L.h-26,{color:P.line,width:2,alpha:.55});
    d.line(L.x+L.side,L.y+L.head,L.x+L.w-28,L.y+L.head,{color:P.line,width:2,alpha:.55});

    const gx=810,gy=115+Math.sin(t*1.2)*3;
    d.glow(1110,470,470,P.cobalt,.10);
    drawGPT(d,gx,gy,.77,{assemble:1,alpha:settle,pose:u>.55?'listen':'think',look:lerp(-.14,.05,easeInOut(u))});

    const orbit=[
      {sx:270,sy:155,ex:1180,ey:205,w:285,h:165,r0:-.10,r1:.035,label:'context',accent:P.cobalt},
      {sx:1370,sy:165,ex:1335,ey:420,w:275,h:160,r0:.09,r1:-.045,label:'tools',accent:P.gold},
      {sx:300,sy:730,ex:1175,ey:690,w:300,h:170,r0:.07,r1:.025,label:'memory',accent:P.ink2},
      {sx:1385,sy:720,ex:760,ey:725,w:310,h:174,r0:-.07,r1:-.035,label:'style',accent:P.cobalt2}
    ];
    orbit.forEach((c,i)=>{
      const q=easeInOut(prog(t,CUT1+.25+i*.09,CUT2-1.05+i*.05));
      const arc=Math.sin(q*Math.PI)*(i%2? -120:120);
      const x=lerp(c.sx,c.ex,q),y=lerp(c.sy,c.ey,q)+arc,rot=lerp(c.r0,c.r1,q);
      // two ghost exposures act as motion blur, not duplicate props.
      if(q>0&&q<1){
        for(let g=2;g>=1;g--)paperCard(d,{x:x-g*18,y:y+(i%2?g*7:-g*7),w:c.w,h:c.h,rot,alpha:.055,accent:c.accent,label:'',shadow:0});
      }
      paperCard(d,{x,y,w:c.w,h:c.h,rot,alpha:.90,accent:c.accent,label:c.label,shadow:.25});
    });

    const spine=easeOut(prog(t,CUT1+1.3,CUT2-.55));
    if(spine>0){
      d.line(1070,220,1070,810,{color:P.cobalt,width:5,alpha:.18*spine});
      for(let i=0;i<7;i++){
        const a=easeOut(prog(t,CUT1+1.5+i*.10,CUT1+1.86+i*.10));
        d.circle(1070,285+i*70,7,{fill:i%2?P.gold:P.cobalt,alpha:.52*a});
        d.line(1090,285+i*70,1090+lerp(0,115,a),285+i*70,{color:P.line,width:7,alpha:.30*a});
      }
    }
  });

  const prompt=easeOut(prog(t,CUT2-.72,CUT2-.15));
  if(prompt>0)d.text('what should this become?',960,940,{size:34,font:'serif',italic:true,align:'center',color:P.ink,alpha:.78*prompt});
}

function composerPanel(d,t){
  const u=prog(t,CUT2,CUT3),push=easeInOut(u);
  room(d,t,{warm:.08,blue:.045});
  const box={x:330,y:385,w:1260,h:240};
  const zoom=lerp(1.02,1.12,push),pan=lerp(0,-35,push);
  camera(d,{zoom,y:pan},()=>{
    d.rrect(box.x,box.y,box.w,box.h,36,{fill:'rgba(255,255,255,.82)',stroke:'rgba(53,65,92,.16)',width:2,shadow:.65});
    d.circle(box.x+58,box.y+58,16,{fill:P.gold,alpha:.85});
    d.text('you',box.x+92,box.y+68,{size:24,weight:650,color:P.ink2,alpha:.55});

    const falseText='make it impressive.';
    const realText='make it worth watching.';
    const b=(t-CUT2)/PBEAT;
    let shown='',deleting=false;
    if(b<2.0)shown=falseText.slice(0,Math.floor(prog(b,0,1.75)*falseText.length));
    else if(b<2.65)shown=falseText;
    else if(b<3.75){shown=falseText.slice(0,Math.ceil((1-prog(b,2.65,3.75))*falseText.length));deleting=true;}
    else if(b<4.25)shown='';
    else shown=realText.slice(0,Math.floor(prog(b,4.25,6.75)*realText.length));

    d.text(shown,box.x+58,box.y+148,{size:48,font:'sans',color:P.ink,alpha:.94});
    const tw=d.measure(shown,{size:48});
    if(Math.floor(t*3.2)%2===0)d.rect(box.x+62+tw,box.y+106,4,58,{fill:deleting?P.coral:P.cobalt,alpha:.72});

    // typing leaves physical ticks that slide down like paper shavings.
    const rate=Math.floor((t-CUT2)*11);
    for(let i=0;i<9;i++){
      const age=((rate-i)+100)%9/9,a=.22*(1-age),xx=box.x+100+(i*123)%1020;
      d.rrect(xx,box.y+198+age*46,30+(i%3)*15,4,2,{fill:deleting?P.coral:P.gold,alpha:a});
    }

    const ready=shown===realText;
    d.circle(box.x+box.w-70,box.y+box.h-62,26,{fill:ready?P.cobalt:P.line,alpha:.85});
    d.line(box.x+box.w-78,box.y+box.h-61,box.x+box.w-60,box.y+box.h-61,{color:P.white,width:3,alpha:ready?1:.45});
    d.line(box.x+box.w-61,box.y+box.h-61,box.x+box.w-68,box.y+box.h-68,{color:P.white,width:3,alpha:ready?1:.45});
  });

  const face=easeOut(prog(t,CUT2+.25,CUT2+.75))*(1-smooth(prog(t,CUT3-.7,CUT3)));
  if(face>0){
    d.save(()=>{
      d.g.translate(50,40);d.g.scale(.52,.52);
      drawGPT(d,40,40,1,{assemble:1,alpha:.78*face,pose:u>.55?'listen':'think',look:lerp(.10,-.08,u)});
    });
  }

  const cx=lerp(1710,1518,easeInOut(prog(t,CUT2+.2,CUT2+1.15))),cy=lerp(760,562,easeInOut(prog(t,CUT2+.2,CUT2+1.15)));
  cursor(d,cx,cy,{alpha:easeOut(prog(t,CUT2+.1,CUT2+.45))*(1-smooth(prog(t,CUT3-.4,CUT3))),click:prog(t,CUT3-.34,CUT3-.04)});
}

function tokenStrip(d,{x,y,w=180,h=54,rot=0,alpha=1,label='',accent=P.cobalt}){
  d.save(()=>{
    d.g.translate(x,y);d.g.rotate(rot);
    d.rrect(-w/2,-h/2,w,h,14,{fill:'rgba(255,253,248,.95)',stroke:'rgba(53,65,92,.14)',width:1.2,alpha,shadow:.18});
    d.rrect(-w/2+14,-5,38,10,5,{fill:accent,alpha:.48*alpha});
    if(label)d.text(label,-w/2+62,8,{size:20,font:'serif',italic:true,color:P.ink2,alpha:.72*alpha});
  });
}

function sentIntoSpace(d,t){
  const u=prog(t,CUT3,END),lift=easeOut(u);
  room(d,t,{warm:.16,blue:.085});
  const cam=easeInOut(prog(t,CUT3+.7,END));
  camera(d,{zoom:lerp(1,1.18,cam),x:lerp(0,-120,cam),y:lerp(0,26,cam),rot:lerp(0,.012,cam)},()=>{
    const gx=lerp(690,430,cam),gy=lerp(120,180,cam),gs=lerp(.78,.72,cam);
    drawGPT(d,gx,gy+Math.sin(t*1.15)*3,gs,{assemble:1,alpha:1,pose:'reply',look:.12});

    const words=['make','it','worth','watching','show','the','work','between','us'];
    words.forEach((word,i)=>{
      const start=CUT3+.10+i*.12,q=easeInOut(prog(t,start,start+2.45));
      if(q<=0)return;
      const sx=1230+i*34,sy=590+(i%3)*48;
      const ex=720+(i%5)*230,ey=190+Math.floor(i/5)*420+(i%2)*45;
      const arc=-260*Math.sin(q*Math.PI)+(i%2?40:-30);
      const x=lerp(sx,ex,q),y=lerp(sy,ey,q)+arc,rot=lerp(.16-.04*i,(i%2?-.08:.06),q);
      if(q>.08&&q<.92){
        tokenStrip(d,{x:x-34,y:y+18,w:145+word.length*10,h:50,rot,alpha:.05,label:'',accent:i%3?P.cobalt:P.gold});
        tokenStrip(d,{x:x-18,y:y+9,w:145+word.length*10,h:50,rot,alpha:.08,label:'',accent:i%3?P.cobalt:P.gold});
      }
      tokenStrip(d,{x,y,w:145+word.length*10,h:50,rot,alpha:.94,label:word,accent:i%3?P.cobalt:P.gold});
    });

    // strips lock into three large planes; the answer becomes architecture, not a subtitle.
    const build=easeOut(prog(t,CUT3+2.2,END-.28));
    if(build>0){
      const planes=[
        {x:740,y:165,w:480,h:245,r:-.035,a:P.cobalt},
        {x:1240,y:260,w:430,h:300,r:.055,a:P.gold},
        {x:865,y:650,w:650,h:250,r:.018,a:P.ink2}
      ];
      planes.forEach((p,i)=>{
        const a=easeOut(prog(t,CUT3+2.15+i*.16,CUT3+2.72+i*.16));
        paperCard(d,{x:p.x,y:p.y+(1-a)*120,w:p.w,h:p.h,rot:p.r,alpha:.86*a,accent:p.a,label:i===0?'question':i===1?'draft':'answer',lines:4,shadow:.32});
      });
      for(let i=0;i<5;i++){
        const a=easeOut(prog(t,CUT3+2.8+i*.08,END-.1));
        d.line(520+i*120,930,800+i*125,790,{color:i%2?P.gold:P.cobalt,width:2.5,alpha:.20*a});
      }
    }
  });

  const final=easeOut(prog(t,END-.75,END-.06));
  if(final>0){
    d.line(300,948,1620,948,{color:P.line,width:1.5,alpha:.25*final});
    d.text('the reply is built in front of you.',960,982,{size:30,font:'serif',italic:true,align:'center',color:P.ink2,alpha:.62*final});
  }
}

export function renderOpeningV2(d,t){
  if(t<CUT1)shotThreads(d,t);
  else if(t<CUT2)contextOrbit(d,t);
  else if(t<CUT3)composerPanel(d,t);
  else sentIntoSpace(d,t);
}

export const OPENING_V2={bpm:BPM,offset:OFF,cuts:[0,CUT1,CUT2,CUT3,END]};
