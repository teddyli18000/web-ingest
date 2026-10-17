import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,prog,pulse} from '../engine/timing.js';
import {buildPieces,drawWindow,L} from '../components/chat.js';
import {drawGPT,characterReveal} from '../components/gpt.js';

export function renderBoot(d,t){
  d.paper(t);
  // Layer 1: a quiet warm room exists before the interface.
  d.glow(1320,330,560,P.gold,.16);
  d.gradRect(0,720,1920,360,[
    [0,'rgba(47,102,213,0)'],[.5,'rgba(47,102,213,.06)'],[1,'rgba(23,32,51,.10)']
  ],true);

  // 0.35 s: the first cobalt rule is the seed of the client.
  const seed=easeOut(prog(t,.35,1.05));
  if(seed>0){
    const cx=960,half=740*seed,hot=pulse(t-.35,.16);
    d.line(cx-half,540,cx+half,540,{color:P.cobalt,width:3+5*hot,alpha:.75+.25*seed});
    if(seed<1)d.glow(cx+half,540,80,P.cobalt,.42*hot);
  }

  // The line unfolds into independently arriving interface pieces.
  if(t>.85) buildPieces(d,t,1.0);
  const open=easeInOut(prog(t,2.10,3.20));
  if(open>0) drawWindow(d,t,{open,glass:.80,thread:0});

  // Character is not a finished image: the ink plates arrive separately and register.
  if(t>3.0){
    const r=characterReveal(t,3.0,6.0);
    const breathe=Math.sin(t*1.25)*5;
    d.clipRect(L.x+L.side+18,L.y+L.head+8,L.w-L.side-36,L.h-L.head-L.compose-26,18,()=>{
      d.glow(1260,475,380,P.cobalt,.10*r.alpha);
      drawGPT(d,1015,135+breathe,.70,{...r,pose:t>5.6?'listen':'think',look:-.15});
    });
  }

  // Interface finishes drawing over the room after the figure is present.
  if(t>4.1){
    const ui=easeOut(prog(t,4.1,5.1));
    drawWindow(d,t,{open:1,glass:.58,thread:ui*.22});
  }

  // A small status label is part of the world, not an explanatory title card.
  const ready=easeOut(prog(t,5.65,6.55));
  if(ready>0){
    d.rrect(294,164,190,44,16,{fill:'rgba(47,102,213,.09)',stroke:'rgba(47,102,213,.25)',alpha:ready});
    d.circle(320,186,6,{fill:P.cobalt,alpha:ready});
    d.text('ready for you',338,193,{size:22,color:P.ink2,alpha:ready});
  }
}
