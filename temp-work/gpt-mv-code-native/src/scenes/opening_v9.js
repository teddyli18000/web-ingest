import {renderOpeningV8} from './opening_v8.js';
import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';

const C1=.28+6*(60/116),C2=.28+13*(60/116),C3=.28+20*(60/116),END=15;

function poly(d,pts,{fill=P.paper,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(7,12,22,${.28*shadow})`;g.shadowBlur=34*shadow;g.shadowOffsetY=18*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function edgeGrade(d){
  d.gradRect(0,0,340,1080,[[0,'rgba(17,24,39,.12)'],[1,'rgba(17,24,39,0)']],false);
  d.gradRect(1580,0,340,1080,[[0,'rgba(17,24,39,0)'],[1,'rgba(17,24,39,.11)']],false);
  d.gradRect(0,870,1920,210,[[0,'rgba(17,24,39,0)'],[1,'rgba(17,24,39,.09)']],true);
}
function lowShelf(d,a=1){
  d.save(()=>{d.g.translate(-120,940);d.g.rotate(-.035);poly(d,[[0,0],[2250,0],[2250,260],[0,260]],{fill:'#30394a',alpha:.62*a,shadow:.28});d.line(170,38,1770,38,{color:P.gold,width:5,alpha:.20*a});});
}
function nearPaper(d,x,y,w,h,rot,{accent=P.cobalt,alpha=1,dark=false}={}){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(0,0,w,h,16,{fill:dark?'#273249':'#fffdfa',stroke:'rgba(53,65,92,.18)',width:1.3,alpha,shadow:.44});d.line(42,46,w-90,46,{color:accent,width:7,alpha:.42*alpha});d.rrect(42,82,w*.52,8,4,{fill:dark?'#aeb8ca':P.line,alpha:.20*alpha});});
}
function shot0Depth(d,t){
  const a=easeOut(prog(t,.18,.70))*(1-easeInOut(prog(t,1.15,1.72)));
  if(a>0){lowShelf(d,.72*a);nearPaper(d,-150,840,700,230,-.10,{accent:P.cobalt,alpha:.92*a,dark:true});}
  const r=easeOut(prog(t,.55,1.15))*(1-easeInOut(prog(t,1.30,2.05)));
  if(r>0)nearPaper(d,1700,120,360,900,.045,{accent:P.gold,alpha:.72*r});
}
function shot1Depth(d,t){
  const a=easeOut(prog(t,C1+.10,C1+.70));
  lowShelf(d,.48*a);
  const q=prog(t,C1+.34,C1+1.24);if(q>0&&q<1){nearPaper(d,lerp(2050,-680,easeInOut(q)),900,640,185,-.09,{accent:P.gold,alpha:.94});}
  const side=easeOut(prog(t,C1+.28,C1+.92));if(side>0)nearPaper(d,1750,250,290,760,.028,{accent:P.cobalt,alpha:.54*side,dark:true});
}
function shot2Depth(d,t){
  const a=easeOut(prog(t,C2+.05,C2+.45));lowShelf(d,.56*a);
  // A near registration board clips the lower-right proof edge and makes the proof sit inside space.
  const k=easeOut(prog(t,C2+.18,C2+.85));if(k>0){d.save(()=>{d.g.translate(1690,815);d.g.rotate(.045);poly(d,[[0,0],[440,0],[440,360],[0,360]],{fill:'#d2c8b7',alpha:.82*k,shadow:.40});d.line(32,42,330,42,{color:P.gold,width:7,alpha:.32*k});});}
  const swipe=prog(t,C3-.82,C3-.10);if(swipe>0&&swipe<1)nearPaper(d,lerp(-760,2070,easeInOut(swipe)),930,720,180,-.08,{accent:P.cobalt,alpha:.96,dark:true});
}
function shot3Depth(d,t){
  const a=easeOut(prog(t,C3+.05,C3+.65));lowShelf(d,.34*a);
  // The emerging world gets a cropped near-lens slab so the character/buildings no longer share one plane.
  if(a>0){d.save(()=>{d.g.translate(-250,900);d.g.rotate(-.12);poly(d,[[0,0],[760,0],[800,180],[40,220]],{fill:'#c6bcad',alpha:.88*a,shadow:.36});d.line(70,42,600,42,{color:P.cobalt,width:6,alpha:.24*a});});}
  const right=easeOut(prog(t,C3+.35,C3+1.05));if(right>0){d.save(()=>{d.g.translate(1750,450);d.g.rotate(.035);poly(d,[[0,0],[360,0],[320,640],[-40,640]],{fill:'#33405a',alpha:.50*right,shadow:.28});d.line(38,54,260,54,{color:P.gold,width:5,alpha:.24*right});});}
}

export function renderOpeningV9(d,t,model){
  renderOpeningV8(d,t,model);
  edgeGrade(d);
  if(t<C1)shot0Depth(d,t);
  else if(t<C2)shot1Depth(d,t);
  else if(t<C3)shot2Depth(d,t);
  else shot3Depth(d,t);
}

export const OPENING_V9_CUTS=[0,C1,C2,C3,END];
