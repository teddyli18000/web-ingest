import {PALETTE as P} from '../engine/palette.js';
import {easeOut,prog,smooth} from '../engine/timing.js';
import {renderDraftsV6} from './drafts_v6.js';

const T1=18.30,T2=21.80;
const EYES={x:.16,y:.045,w:.69,h:.31};

function compareEditorial(d,t,model){
  const a=easeOut(prog(t,T1,T1+.36))*(1-smooth(prog(t,T2-.42,T2)));
  if(a<=0)return;

  // Replace the smiling face with a serious eye-only print plate.
  d.rect(0,0,665,1080,{fill:P.ink,alpha:.965*a});
  d.glow(400,330,560,P.cobalt,.18*a);
  d.glow(120,850,380,P.gold,.055*a);

  d.save(()=>{
    d.g.beginPath();d.g.rect(0,0,665,760);d.g.clip();
    model.plate(d.g,{x:-86,y:82,w:790,h:510},{crop:EYES,color:'#111827',alpha:.68*a,rot:-.008,cover:true});
    model.plate(d.g,{x:-69,y:69,w:790,h:510},{crop:EYES,color:P.cobalt,alpha:.66*a,rot:.005,cover:true});
    model.draw(d.g,{x:-76,y:74,w:790,h:510},{crop:EYES,alpha:.96*a,cover:true});
  });

  d.rect(622,0,43,1080,{fill:P.cobalt,alpha:.16*a});
  d.line(641,92,641,610,{color:P.gold,width:4,alpha:.55*a});
  d.text('LOOK AGAIN',82,790,{size:22,font:'mono',weight:700,color:P.cobalt2,alpha:.78*a});
  d.text('compare, don’t conceal.',82,852,{size:34,font:'serif',italic:true,color:P.white,alpha:.92*a});
  d.text('wrong ≠ useless',84,902,{size:19,font:'mono',weight:700,color:P.gold2,alpha:.58*a});
}

export function renderDraftsV7(d,t,model){
  renderDraftsV6(d,t,model);
  if(t>=T1&&t<T2)compareEditorial(d,t,model);
}

export const DRAFTS_V7_CUTS=[15,T1,T2,25.20,30];
