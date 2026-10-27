import {renderEndingV2} from './ending_v2.js';
import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';

const T2=52.10,T3=56.20,END=60;
const BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f',PAPER='#fffaf0',INK='#232426';
let buffer=null,bg=null;

function ensureBuffer(g){
  const c=g.canvas;
  if(!buffer||buffer.width!==c.width||buffer.height!==c.height){
    buffer=document.createElement('canvas');buffer.width=c.width;buffer.height=c.height;bg=buffer.getContext('2d');
  }
}
function cameraDrift(d,t){
  if(t<T2)return;
  const g=d.g,c=g.canvas;ensureBuffer(g);
  bg.setTransform(1,0,0,1,0,0);bg.clearRect(0,0,buffer.width,buffer.height);bg.drawImage(c,0,0);
  const local=t<T3?prog(t,T2,T3):prog(t,T3,END);
  // Very slow editorial camera creep: never stops, never exposes canvas edges.
  const z=t<T3?lerp(1.000,1.034,easeInOut(local)):lerp(1.018,1.052,easeInOut(local));
  const panX=t<T3?lerp(0,-20,local):lerp(-8,18,local),panY=t<T3?lerp(0,-12,local):lerp(-6,-20,local);
  g.setTransform(1,0,0,1,0,0);g.fillStyle='#e9e0d3';g.fillRect(0,0,c.width,c.height);
  g.translate(c.width/2+panX,c.height/2+panY);g.scale(z,z);g.translate(-c.width/2,-c.height/2);g.drawImage(buffer,0,0);g.setTransform(1,0,0,1,0,0);
}
function tab(d,x,y,w,h,rot,{fill=PAPER,accent=BLUE,a=1,shadow=.25}={}){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(-w/2,-h/2,w,h,7,{fill,stroke:'rgba(76,65,54,.17)',width:1,alpha:a,shadow});d.line(-w*.31,-h*.13,w*.27,-h*.13,{color:accent,width:4,alpha:.30*a});});
}
function livingMacro(d,t){
  if(t<T2||t>=T3)return;
  const q=prog(t,T2,T3),targets=[[1288,754,-.09,GOLD],[1370,720,.04,BLUE],[1450,748,-.03,GOLD],[1512,704,.08,BLUE]];
  targets.forEach((v,i)=>{const k=easeOut(prog(q,.10+i*.17,.46+i*.17));if(k<=0)return;const sx=i%2?-120:2050,sy=lerp(1010,560,i/3),x=lerp(sx,v[0],k),y=lerp(sy,v[1],k);tab(d,x,y,100-i*8,42-i*3,lerp(i%2?-.35:.28,v[2],k),{fill:i%2?'#edf2ff':'#fff0bd',accent:v[3],a:.88*k,shadow:.28});});
  const pulse=(Math.sin((t-T2)*3.0)+1)/2;d.glow(1400,710,180,BLUE,.025+.022*pulse);d.glow(1370,730,150,GOLD,.020+.018*(1-pulse));
  // Sun stripe drifts across the paper to keep the macro alive without UI noise.
  const x=lerp(1540,1310,q);d.save(()=>{d.g.translate(x,0);d.g.rotate(.34);d.rect(0,-180,105,1380,{fill:'#f6dba5',alpha:.035});});
}
function livingHold(d,t){
  if(t<T3)return;
  const q=prog(t,T3,END),pulse=(Math.sin((t-T3)*2.1)+1)/2;
  // Two live registration marks breathe rather than freezing as dots.
  d.glow(1298,690,145,GOLD,.030+.022*pulse);d.glow(1326,672,135,BLUE,.026+.020*(1-pulse));
  d.circle(1298,690,7+1.2*pulse,{fill:GOLD,alpha:.66});d.circle(1326,672,6+1.1*(1-pulse),{fill:BLUE,alpha:.62});
  // A near-lens tracing strip crosses only the lower edge over the whole hold.
  const x=lerp(-520,340,q);d.save(()=>{d.g.translate(x,1018);d.g.rotate(-.045);d.rrect(0,0,760,86,8,{fill:'#d7ccba',stroke:'rgba(76,65,54,.14)',width:1,alpha:.34,shadow:.18});d.line(54,28,600,28,{color:BLUE2,width:4,alpha:.18});d.line(145,55,530,55,{color:GOLD2,width:3,alpha:.15});});
}

export function renderEndingV3(d,t,model,poses){
  renderEndingV2(d,t,model,poses);
  if(t>=T2){livingMacro(d,t);livingHold(d,t);cameraDrift(d,t);}
}
export const ENDING_V3_CUTS=[45,48.10,T2,T3,END];
