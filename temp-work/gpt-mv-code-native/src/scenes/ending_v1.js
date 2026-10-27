import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderConstructV5} from './construct_v5.js';

const T0=45,T1=48.10,T2=52.10,T3=56.20,END=60;
const PAPER='#f3efe4',PAPER2='#fffaf0',INK='#232426',INK2='#5d6064',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f',WARM='#c99a62',DESK='#7b614d';

function poly(d,pts,{fill=PAPER2,stroke=null,width=1,alpha=1,shadow=0}={}){const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(35,29,24,${.22*shadow})`;g.shadowBlur=30*shadow;g.shadowOffsetY=14*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});}
function curve(d,pts,{color=BLUE,width=5,alpha=1,dash=[]}={}){const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.setLineDash(dash);g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],mx=(p[0]+n[0])/2,my=(p[1]+n[1])/2;g.quadraticCurveTo(p[0],p[1],mx,my);}const z=pts.at(-1);g.lineTo(z[0],z[1]);g.stroke();});}
function mark(d,x,y,color,a=1,r=8){d.glow(x,y,105,color,.14*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,r*3,{fill:null,stroke:color,width:2,alpha:.28*a});}

function warmRoom(d,t){
  d.paper(t*.20);
  d.glow(1580,210,760,GOLD,.16);d.glow(270,740,620,BLUE,.055);
  d.gradRect(0,0,1920,600,[[0,'rgba(255,247,229,.12)'],[1,'rgba(207,151,82,.13)']],true);
  poly(d,[[-80,760],[2000,680],[2000,1160],[-80,1160]],{fill:DESK,alpha:.24});
  d.line(0,790,1920,706,{color:'#5d4636',width:3,alpha:.10});
}
function pagePose(d,fn,{cx=980,cy=565,w=1370,h=770,rot=-.022,scale=1}={}){d.save(()=>{d.g.translate(cx,cy);d.g.rotate(rot);d.g.scale(scale,scale);d.g.translate(-w/2,-h/2);fn(w,h);});}
function pageBase(d,w,h,{alpha=1,accent=GOLD}={}){d.rrect(22,24,w,h,22,{fill:'#4e3a2e',alpha:.07*alpha});d.rrect(0,0,w,h,22,{fill:PAPER2,stroke:'rgba(76,65,54,.20)',width:1.5,alpha,shadow:.38});d.line(46,48,w-54,48,{color:accent,width:6,alpha:.36*alpha});}
function cropMarks(d,w,h,a=.18){for(const [x,y,sx,sy] of [[0,0,1,1],[w,0,-1,1],[0,h,1,-1],[w,h,-1,-1]]){d.line(x-sx*13,y,x+sx*27,y,{color:INK2,width:1.4,alpha:a});d.line(x,y-sy*13,x,y+sy*27,{color:INK2,width:1.4,alpha:a});}}
function plan(d,w,h,{a=1,detail=1,unfinished=0}={}){
  d.text('SHARED DRAFT / OPEN',50,94,{size:20,font:'mono',weight:700,color:INK2,alpha:.34*a});
  d.text('what we built together',50,135,{size:31,font:'serif',italic:true,color:INK,alpha:.58*a});
  const blue=[[92,555],[235,480],[410,515],[570,400],[745,432],[930,322]],gold=[[1020,585],[895,510],[760,535],[635,474],[520,386],[405,332]];
  curve(d,blue,{color:BLUE,width:6,alpha:.62*a});curve(d,gold,{color:GOLD,width:6,alpha:.52*a});
  for(const p of blue)d.circle(p[0],p[1],6,{fill:BLUE,alpha:.66*a});for(const p of gold)d.circle(p[0],p[1],6,{fill:GOLD,alpha:.60*a});
  if(detail>0){
    const boxes=[[190,250,125,90],[375,210,150,118],[585,260,130,145],[810,195,170,112],[1000,260,120,155]];
    boxes.forEach((b,i)=>{const q=easeOut(prog(detail,i*.08,.52+i*.08));if(q<=0)return;d.rrect(b[0],b[1]+(1-q)*35,b[2],b[3]*q,8,{fill:i%2?'#eef2fb':'#f7e8b2',stroke:'rgba(53,65,92,.16)',width:1,alpha:.68*q});d.line(b[0]+18,b[1]+24,b[0]+b[2]*.70,b[1]+24,{color:i%2?BLUE:GOLD,width:4,alpha:.22*q});});
  }
  // Unfinished lower-right corner: intentionally blank with one open registration bracket.
  const u=unfinished;d.line(w-290,h-172,w-125,h-172,{color:BLUE,width:3,alpha:.36*u});d.line(w-125,h-172,w-125,h-82,{color:BLUE,width:3,alpha:.36*u});d.line(w-290,h-172,w-290,h-126,{color:GOLD,width:3,alpha:.32*u});
  cropMarks(d,w,h,.15*a);
}
function tape(d,x,y,w,h,rot,a=1){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(-w/2,-h/2,w,h,4,{fill:'#f3dca1',stroke:'rgba(95,74,42,.10)',width:1,alpha:.54*a,shadow:.06});});}
function pencil(d,x,y,len,rot,a=1){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(0,-8,len,16,5,{fill:'#d9bf72',stroke:'rgba(70,54,33,.18)',width:1,alpha:a,shadow:.18});d.rrect(len-72,-8,54,16,4,{fill:'#3157d5',alpha:.68*a});poly(d,[[len,0],[len+30,-8],[len+30,8]],{fill:'#d8c9b0',stroke:'rgba(70,54,33,.18)',alpha:a});});}

function finalDesk(d,t,{detail=1,unfinished=1}={}){
  warmRoom(d,t);
  pagePose(d,(w,h)=>{pageBase(d,w,h,{accent:GOLD});plan(d,w,h,{a:1,detail,unfinished});tape(d,180,35,130,42,-.08,.80);tape(d,w-160,42,145,42,.06,.72);});
  pencil(d,1280,930,440,-.13,.86);
  d.rrect(60,905,520,118,16,{fill:'#fffaf0',stroke:'rgba(76,65,54,.15)',width:1,alpha:.74,shadow:.18});d.line(95,940,430,940,{color:BLUE,width:5,alpha:.20});d.line(95,976,325,976,{color:GOLD,width:4,alpha:.17});
}

function foldBack(d,t,model,poses){
  finalDesk(d,t,{detail:.55,unfinished:0});
  const q=easeInOut(prog(t,T0+.12,T1-.08));
  if(q>=1)return;
  // Keep the accepted world above a physical near-lens working sheet; reveal the desk below it.
  const edge=lerp(1160,-180,q);
  d.save(()=>{const g=d.g;g.beginPath();g.rect(0,0,1920,Math.max(0,edge));g.clip();renderConstructV5(d,44.999,model,poses);});
  d.save(()=>{d.g.translate(960,edge+10);d.g.rotate(.015);d.rrect(-1080,-64,2160,128,8,{fill:PAPER2,stroke:'rgba(76,65,54,.18)',width:1.2,alpha:.98,shadow:.44});d.line(-870,-10,760,-10,{color:BLUE,width:8,alpha:.32});d.line(-370,22,420,22,{color:GOLD,width:5,alpha:.24});});
}
function settle(d,t){
  warmRoom(d,t);
  const settle=easeOut(prog(t,T1,T1+1.05));
  const spread=easeInOut(prog(t,T1+.52,T2-.20));
  // Three proof layers register into one page rather than fading away.
  for(let i=2;i>=0;i--){const k=1-spread,off=(i-1)*34*k,rot=(-.035+(i*.026))*k,accent=i===1?BLUE:(i===2?GOLD:INK2);pagePose(d,(w,h)=>{pageBase(d,w,h,{alpha:.92,accent});plan(d,w,h,{a:i===0?1:.20,detail:settle,unfinished:0});},{cx:980+off,cy:565+Math.abs(i-1)*12*k,rot:-.022+rot,scale:1-i*.012*k});}
  pencil(d,1280,930,440,-.13,.84);
}
function collaborate(d,t){
  finalDesk(d,t,{detail:1,unfinished:easeOut(prog(t,T2+.10,T2+.90))});
  const gold=easeOut(prog(t,T2+.38,T2+1.36)),blue=easeOut(prog(t,T2+.76,T2+1.72));
  // User and GPT marks enter from opposite edges and stop at the same unfinished corner.
  curve(d,[[55,810],[310,780],[620,755],[955,720],[1240,692]],{color:GOLD,width:6,alpha:.46*gold});
  curve(d,[[1860,625],[1640,648],[1450,670],[1320,690],[1240,704]],{color:BLUE,width:6,alpha:.50*blue});
  mark(d,70,808,GOLD,gold,8);mark(d,1848,626,BLUE,blue,8);
  const meet=easeOut(prog(t,T2+1.48,T3-.28));if(meet>0){mark(d,1240,700,GOLD,.55*meet,6);mark(d,1240,700,BLUE,.48*meet,4);}
}
function hold(d,t){
  finalDesk(d,t,{detail:1,unfinished:1});
  const a=easeOut(prog(t,T3,T3+.75));
  // Only two live marks remain. No goodbye card, no fade to black.
  mark(d,1240,700,GOLD,.72*a,6);mark(d,1270,682,BLUE,.66*a,5);
  d.text('from here.',365,230,{size:43,font:'serif',italic:true,color:INK,alpha:.52*a});
  d.text('SHARED DRAFT / STILL OPEN',368,270,{size:18,font:'mono',weight:700,color:INK2,alpha:.28*a});
  const breathe=(Math.sin((t-T3)*1.05)+1)/2;d.glow(1480,250,620,GOLD,.035+.025*breathe);
}

export function renderEndingV1(d,t,model,poses){if(t<T1)return foldBack(d,t,model,poses);if(t<T2)return settle(d,t);if(t<T3)return collaborate(d,t);return hold(d,t);}
export const ENDING_V1_CUTS=[45,T1,T2,T3,60];
