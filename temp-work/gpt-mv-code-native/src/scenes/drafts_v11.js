import {renderDraftsV10} from './drafts_v10.js';
import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';

const T0=15,T1=18.30,T2=21.80,T3=25.20,T4=28.15,END=30;

function poly(d,pts,{fill=P.paper,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(7,12,22,${.30*shadow})`;g.shadowBlur=36*shadow;g.shadowOffsetY=20*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function grade(d){
  d.gradRect(0,0,310,1080,[[0,'rgba(17,24,39,.10)'],[1,'rgba(17,24,39,0)']],false);
  d.gradRect(1610,0,310,1080,[[0,'rgba(17,24,39,0)'],[1,'rgba(17,24,39,.10)']],false);
  d.gradRect(0,870,1920,210,[[0,'rgba(17,24,39,0)'],[1,'rgba(17,24,39,.11)']],true);
}
function deskLip(d,a=1,{blue=false}={}){
  d.save(()=>{d.g.translate(-120,988);d.g.rotate(-.028);poly(d,[[0,0],[2240,0],[2240,210],[0,210]],{fill:'#30394a',alpha:.70*a,shadow:.32});d.line(150,36,1810,36,{color:blue?P.cobalt:P.gold,width:6,alpha:.22*a});});
}
function binder(d,x,y,w,h,rot,{accent=P.cobalt,dark=false,alpha=1}={}){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(0,0,w,h,14,{fill:dark?'#2f394b':'#fffdfa',stroke:'rgba(53,65,92,.18)',width:1.3,alpha,shadow:.44});d.line(34,44,w-70,44,{color:accent,width:7,alpha:.40*alpha});for(let i=0;i<3;i++)d.rrect(36,82+i*25,w*(.50-i*.07),7,3,{fill:dark?'#aeb8ca':P.line,alpha:.18*alpha});});
}
function pins(d,x,y,a=1){d.glow(x,y,110,P.gold,.15*a);d.circle(x,y,8,{fill:P.gold,alpha:a});d.circle(x,y,26,{fill:null,stroke:P.gold2,width:2,alpha:.30*a});}
function phaseCatch(d,t){
  const a=easeOut(prog(t,T0+.35,T0+1.05));deskLip(d,.52*a);
  const q=prog(t,T0+.55,T0+1.45);if(q>0&&q<1)binder(d,lerp(1990,-520,easeInOut(q)),895,590,170,-.11,{accent:P.cobalt,alpha:.94});
  const s=easeOut(prog(t,T0+.80,T0+1.50));if(s>0)binder(d,1760,220,300,770,.03,{accent:P.gold,dark:true,alpha:.48*s});
}
function phaseCompare(d,t){
  const a=easeOut(prog(t,T1+.08,T1+.55));deskLip(d,.62*a,{blue:true});
  const left=easeOut(prog(t,T1+.20,T1+.90));if(left>0){d.save(()=>{d.g.translate(-180,250);d.g.rotate(-.03);poly(d,[[0,0],[300,0],[260,760],[-40,760]],{fill:'#3b4558',alpha:.48*left,shadow:.30});d.line(78,60,240,60,{color:P.cobalt,width:5,alpha:.26*left});});}
  const q=prog(t,T1+.30,T1+1.18);if(q>0&&q<1)binder(d,lerp(2040,-620,easeInOut(q)),910,650,175,-.09,{accent:'#d94b3d',alpha:.95});
}
function phasePeel(d,t){
  const a=easeOut(prog(t,T2+.05,T2+.48));deskLip(d,.58*a);
  // Near proof stack at frame right; the corrected sheet now sits in a layered desk, not empty paper space.
  const s=easeOut(prog(t,T2+.30,T2+1.10));if(s>0){for(let i=0;i<3;i++)binder(d,1710+i*36,690+i*28,410,360,.035+i*.012,{accent:i===2?P.cobalt:P.gold,alpha:(.40+i*.12)*s});}
  const q=prog(t,T2+.78,T2+1.52);if(q>0&&q<1)binder(d,lerp(-720,2070,easeInOut(q)),945,700,160,-.10,{accent:P.cobalt,dark:true,alpha:.94});
}
function phaseGive(d,t){
  const a=easeOut(prog(t,T3+.05,T3+.55));deskLip(d,.66*a,{blue:true});
  const side=easeOut(prog(t,T3+.25,T3+.92));if(side>0)binder(d,1740,250,330,740,.035,{accent:P.gold,dark:true,alpha:.46*side});
  const q=prog(t,T4-.58,T4+.25);if(q>0&&q<1)binder(d,lerp(-900,2100,easeInOut(q)),900,820,205,-.085,{accent:P.cobalt,alpha:.97});
  const user=easeOut(prog(t,T3+.70,T3+1.35));if(user>0)pins(d,242,808,.70*user);
}
function phaseHand(d,t){
  const a=easeOut(prog(t,T4+.04,T4+.48));deskLip(d,.52*a);
  d.save(()=>{const k=easeOut(prog(t,T4+.22,T4+.92));if(k<=0)return;d.g.translate(-170,858);d.g.rotate(-.055);poly(d,[[0,0],[640,0],[690,235],[40,250]],{fill:'#c8beae',alpha:.84*k,shadow:.40});d.line(70,42,520,42,{color:P.gold,width:6,alpha:.26*k});});
}

export function renderDraftsV11(d,t,model,poses){
  renderDraftsV10(d,t,model,poses);
  grade(d);
  if(t<T1)phaseCatch(d,t);
  else if(t<T2)phaseCompare(d,t);
  else if(t<T3)phasePeel(d,t);
  else if(t<T4)phaseGive(d,t);
  else phaseHand(d,t);
}

export const DRAFTS_V11_CUTS=[15,T1,T2,T3,T4,END];
