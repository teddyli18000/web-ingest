import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';
import {renderConstructV5} from './construct_v5.js';

const T0=45,T1=48.10,T2=52.10,T3=56.20,END=60;
const NAVY='#111827',INK='#232426',INK2='#5d6064',PAPER='#f3efe4',PAPER2='#fffaf0',PAPER_DARK='#c9bca9';
const BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f',WOOD='#735a47';

function poly(d,pts,{fill=PAPER2,stroke=null,width=1,alpha=1,shadow=0}={}){const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(34,25,18,${.28*shadow})`;g.shadowBlur=38*shadow;g.shadowOffsetY=20*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});}
function curve(d,pts,{color=BLUE,width=6,alpha=1}={}){const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],mx=(p[0]+n[0])/2,my=(p[1]+n[1])/2;g.quadraticCurveTo(p[0],p[1],mx,my);}const z=pts[pts.length-1];g.lineTo(z[0],z[1]);g.stroke();});}
function mark(d,x,y,color,a=1,r=8){d.glow(x,y,115,color,.16*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,r*3,{fill:null,stroke:color,width:2,alpha:.30*a});}

function room(d,t,{deskY=690,warm=.16}={}){
  d.rect(0,0,1920,1080,{fill:'#e9e0d3'});
  d.gradRect(0,0,1920,deskY,[[0,'#efe7db'],[.55,'#e5d6c3'],[1,'#d7c5ae']],true);
  d.glow(1600,170,760,GOLD,warm);d.glow(300,720,620,BLUE,.055);
  poly(d,[[-80,deskY],[2000,deskY-75],[2000,1160],[-80,1160]],{fill:WOOD,alpha:.43,shadow:.18});
  d.line(-20,deskY+25,1940,deskY-48,{color:'#4c392d',width:3,alpha:.14});
  // window-frame shadow and foreground desk darkness create room depth.
  poly(d,[[1350,0],[1450,0],[1120,690],[1015,690]],{fill:'rgba(91,67,44,.055)'});
  poly(d,[[1640,0],[1705,0],[1450,690],[1375,690]],{fill:'rgba(91,67,44,.045)'});
  d.gradRect(0,920,1920,160,[[0,'rgba(38,27,20,0)'],[1,'rgba(38,27,20,.13)']],true);
  d.save(()=>{const g=d.g;g.globalAlpha=.035;g.fillStyle=INK;for(let i=0;i<150;i++){const x=(i*161.7+t*6)%1920,y=(i*87.1+t*4)%1080;g.fillRect(x,y,1+(i%5===0),1);}});
}
function sheet(d,cx,cy,w,h,rot,{accent=BLUE,alpha=1,shadow=.35,fill=PAPER2}={}){d.save(()=>{d.g.translate(cx,cy);d.g.rotate(rot);poly(d,[[-w/2+18,-h/2+20],[w/2+18,-h/2+20],[w/2+18,h/2+20],[-w/2+18,h/2+20]],{fill:'rgba(52,38,28,.075)',alpha,shadow:.18});d.rrect(-w/2,-h/2,w,h,18,{fill,stroke:'rgba(76,65,54,.20)',width:1.5,alpha,shadow});d.line(-w/2+42,-h/2+46,w/2-50,-h/2+46,{color:accent,width:6,alpha:.38*alpha});});}
function planOn(d,cx,cy,w,h,rot,{a=1,unfinished=0,detail=1}={}){d.save(()=>{d.g.translate(cx,cy);d.g.rotate(rot);const ox=-w/2,oy=-h/2;d.text('SHARED DRAFT / OPEN',ox+48,oy+93,{size:20,font:'mono',weight:700,color:INK2,alpha:.34*a});d.text('what we built together',ox+48,oy+134,{size:31,font:'serif',italic:true,color:INK,alpha:.60*a});const blue=[[ox+95,oy+h*.74],[ox+245,oy+h*.64],[ox+430,oy+h*.69],[ox+585,oy+h*.51],[ox+770,oy+h*.56],[ox+955,oy+h*.40]],gold=[[ox+w-110,oy+h*.78],[ox+w-255,oy+h*.67],[ox+w-430,oy+h*.70],[ox+w-585,oy+h*.61],[ox+w-740,oy+h*.49],[ox+w-885,oy+h*.43]];curve(d,blue,{color:BLUE,width:6,alpha:.64*a});curve(d,gold,{color:GOLD,width:6,alpha:.55*a});for(const p of blue)d.circle(p[0],p[1],6,{fill:BLUE,alpha:.68*a});for(const p of gold)d.circle(p[0],p[1],6,{fill:GOLD,alpha:.62*a});if(detail>0){for(let i=0;i<5;i++){const q=easeOut(prog(detail,i*.09,.45+i*.09));const x=ox+210+i*175,y=oy+205+(i%2)*45,ww=120+(i%2)*24,hh=95+(i%3)*22;d.rrect(x,y+(1-q)*30,ww,hh*q,7,{fill:i%2?'#e8eefc':'#f2dda0',stroke:'rgba(53,65,92,.14)',width:1,alpha:.68*q});d.line(x+16,y+25,x+ww*.70,y+25,{color:i%2?BLUE:GOLD,width:4,alpha:.22*q});}}if(unfinished>0){const x=ox+w-300,y=oy+h-185;d.line(x,y,x+175,y,{color:BLUE,width:3,alpha:.38*unfinished});d.line(x+175,y,x+175,y+95,{color:BLUE,width:3,alpha:.38*unfinished});d.line(x,y,x,y+50,{color:GOLD,width:3,alpha:.34*unfinished});}});}
function tape(d,x,y,w,rot,a=.7){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(-w/2,-20,w,40,4,{fill:'#efcf87',stroke:'rgba(95,74,42,.10)',width:1,alpha:a,shadow:.06});});}
function pencil(d,x,y,len,rot,a=1){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(0,-8,len,16,5,{fill:'#d7bb6d',stroke:'rgba(70,54,33,.18)',width:1,alpha:a,shadow:.18});d.rrect(len-72,-8,54,16,4,{fill:BLUE,alpha:.70*a});poly(d,[[len,0],[len+30,-8],[len+30,8]],{fill:'#d8c9b0',stroke:'rgba(70,54,33,.18)',alpha:a});});}
function ruler(d,x,y,len,rot,a=1){d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.rrect(0,-25,len,50,5,{fill:'#efe6d3',stroke:'rgba(74,60,43,.18)',width:1,alpha:a,shadow:.16});for(let i=0;i<18;i++)d.line(24+i*34,-24,24+i*34,-24+(i%5===0?25:14),{color:INK2,width:1.4,alpha:.28*a});});}

function foldWorld(d,t,model,poses){
  room(d,t,{deskY:720,warm:.10});
  // target desk page exists underneath the outgoing world.
  const settle=easeOut(prog(t,T0+.30,T1-.15));sheet(d,1040,590,1320,700,-.026,{accent:GOLD,alpha:.55+.45*settle,shadow:.42});planOn(d,1040,590,1320,700,-.026,{a:.55+.45*settle,detail:.32*settle,unfinished:0});
  const q=easeInOut(prog(t,T0+.05,T1-.05));if(q<1){const edge=lerp(1120,-180,q);d.save(()=>{d.g.beginPath();d.g.rect(0,0,1920,Math.max(0,edge));d.g.clip();renderConstructV5(d,44.999,model,poses);});d.save(()=>{d.g.translate(960,edge+5);d.g.rotate(.012);d.rrect(-1100,-70,2200,140,8,{fill:PAPER2,stroke:'rgba(76,65,54,.18)',width:1.3,alpha:.99,shadow:.55});d.line(-870,-14,780,-14,{color:BLUE,width:9,alpha:.34});d.line(-390,23,450,23,{color:GOLD,width:6,alpha:.26});});}
  // foreground desk edge stays fixed while page/world moves.
  poly(d,[[-80,990],[2010,930],[2010,1120],[-80,1120]],{fill:'#4c382d',alpha:.28,shadow:.20});
}
function registerStack(d,t){
  room(d,t,{deskY:710,warm:.15});
  const k=easeInOut(prog(t,T1,T2-.20));
  // Oblique side camera: three sheets enter at clearly different Z/depth and register.
  const configs=[{dx:-85,dy:52,rot:-.055,accent:GOLD,a:.68},{dx:58,dy:28,rot:.025,accent:BLUE,a:.76},{dx:0,dy:0,rot:-.018,accent:BLUE,a:1}];
  configs.forEach((c,i)=>{const sep=(1-k),cx=990+c.dx*sep,cy=585+c.dy*sep,rot=-.018+c.rot*sep;sheet(d,cx,cy,1320,690,rot,{accent:c.accent,alpha:c.a,shadow:.34+i*.07});planOn(d,cx,cy,1320,690,rot,{a:i===2?1:.18,detail:easeOut(prog(t,T1+.18,T1+1.55)),unfinished:0});});
  ruler(d,80,850,650,-.08,.78);pencil(d,1290,930,440,-.14,.86);
  // cropped foreground proof edge makes this a side view, not another top-down plate.
  d.save(()=>{d.g.translate(-120,930);d.g.rotate(-.08);d.rrect(0,0,780,230,15,{fill:'#d0c3b0',stroke:'rgba(76,65,54,.15)',width:1,alpha:.82,shadow:.32});d.line(58,45,600,45,{color:GOLD,width:6,alpha:.26});});
}
function macroCorner(d,t){
  room(d,t,{deskY:800,warm:.18});
  // Extreme close-up: page fills frame; unfinished corner sits near centre-right.
  const cx=955,cy=610,w=1780,h=930,rot=-.018;sheet(d,cx,cy,w,h,rot,{accent:GOLD,shadow:.46});planOn(d,cx,cy,w,h,rot,{a:1,detail:1,unfinished:1});
  const gold=easeOut(prog(t,T2+.25,T2+1.45)),blue=easeOut(prog(t,T2+.68,T2+1.90));
  curve(d,[[-80,850],[280,815],[650,770],[1040,730],[1380,695]],{color:GOLD,width:8,alpha:.52*gold});
  curve(d,[[1990,520],[1710,560],[1520,620],[1410,675],[1380,700]],{color:BLUE,width:8,alpha:.56*blue});
  mark(d,80,835,GOLD,gold,9);mark(d,1840,555,BLUE,blue,9);
  const meet=easeOut(prog(t,T2+1.65,T3-.25));if(meet>0){mark(d,1380,698,GOLD,.62*meet,6);mark(d,1408,681,BLUE,.56*meet,5);}
  // near-lens ruler and pencil crop in/out to give macro scale.
  ruler(d,-80,1010,920,-.055,.82);pencil(d,1440,960,520,-.18,.82);
}
function quietPullback(d,t){
  room(d,t,{deskY:700,warm:.20});
  const k=easeOut(prog(t,T3,T3+1.10));
  const cx=lerp(980,1040,k),cy=lerp(610,575,k),w=lerp(1650,1260,k),h=lerp(860,650,k),rot=lerp(-.018,-.035,k);
  sheet(d,cx,cy,w,h,rot,{accent:GOLD,shadow:.43});planOn(d,cx,cy,w,h,rot,{a:1,detail:1,unfinished:1});
  const mx=cx+w*.24,my=cy+h*.18;mark(d,mx,my,GOLD,.72,6);mark(d,mx+28,my-18,BLUE,.66,5);
  tape(d,cx-w*.32,cy-h*.47,145,-.07,.72);tape(d,cx+w*.31,cy-h*.46,130,.05,.64);pencil(d,1300,900,430,-.13,.82);ruler(d,70,875,560,-.06,.72);
  // true foreground desk lip + a dark chair edge create a quiet room, not a white canvas.
  poly(d,[[-80,950],[2010,900],[2010,1130],[-80,1130]],{fill:'#49372d',alpha:.24,shadow:.18});
  poly(d,[[1740,730],[1940,700],[1940,1110],[1810,1110]],{fill:'#2d2a2a',alpha:.12});
  const a=easeOut(prog(t,T3+.55,T3+1.45));d.text('from here.',340,230,{size:46,font:'serif',italic:true,color:INK,alpha:.56*a});d.text('SHARED DRAFT / STILL OPEN',344,273,{size:18,font:'mono',weight:700,color:INK2,alpha:.30*a});
}

export function renderEndingV2(d,t,model,poses){if(t<T1)return foldWorld(d,t,model,poses);if(t<T2)return registerStack(d,t);if(t<T3)return macroCorner(d,t);return quietPullback(d,t);}
export const ENDING_V2_CUTS=[45,T1,T2,T3,60];
