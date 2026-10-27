import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog} from '../engine/timing.js';
import {renderConstructV3} from './construct_v3.js';

const T3=40.55,END=45;
const SKY='#151c2c',FLOOR='#d9d0c0',FLOOR2='#ece4d5',INK='#172033',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f';

function poly(d,pts,{fill=FLOOR2,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(3,8,18,${.30*shadow})`;g.shadowBlur=34*shadow;g.shadowOffsetY=18*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function curve(d,pts,{color=BLUE,width=6,alpha=1}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],mx=(p[0]+n[0])/2,my=(p[1]+n[1])/2;g.quadraticCurveTo(p[0],p[1],mx,my);}const z=pts[pts.length-1];g.lineTo(z[0],z[1]);g.stroke();});
}
function mark(d,x,y,color,a=1,r=9){d.glow(x,y,115,color,.16*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,r*3,{fill:null,stroke:color,width:2,alpha:.32*a});}
function stage(d){
  const h=258;d.rect(0,0,1920,1080,{fill:SKY});d.glow(260,210,620,BLUE,.15);d.glow(1600,230,620,GOLD,.10);poly(d,[[0,h],[1920,h],[1920,1080],[0,1080]],{fill:FLOOR});
  const vp=[960,h-12];for(let i=0;i<=12;i++){const x=lerp(-250,2170,i/12);d.line(vp[0],vp[1],x,1080,{color:i%2?INK:BLUE,width:1.2,alpha:i%2?.07:.05});}
  for(let i=1;i<=9;i++){const u=i/10,y=lerp(h+18,1080,Math.pow(u,1.75));d.line(0,y,1920,y,{color:INK,width:1.2,alpha:.07});}
  d.line(0,665,1920,535,{color:INK,width:2,alpha:.09});d.line(560,h,840,1080,{color:INK,width:2,alpha:.08});
}
function arch(d,cx,base,w,h,{accent=BLUE,side='#aaa397'}={}){
  const top=base-h,g=d.g;poly(d,[[cx+w/2,base],[cx+w/2+46,base-18],[cx+w/2+46,top-18],[cx+w/2,top]],{fill:side,stroke:'rgba(23,32,51,.18)',shadow:.16});
  d.save(()=>{const path=new Path2D();path.moveTo(cx-w/2,base);path.lineTo(cx-w*.45,top+h*.22);path.quadraticCurveTo(cx,top-h*.035,cx+w*.45,top+h*.22);path.lineTo(cx+w/2,base);path.closePath();const hole=new Path2D(),hw=w*.21;hole.moveTo(cx-hw,base);hole.lineTo(cx-hw,top+h*.58);hole.quadraticCurveTo(cx,top+h*.33,cx+hw,top+h*.58);hole.lineTo(cx+hw,base);hole.closePath();path.addPath(hole);g.fillStyle='#e7dfd2';g.fill(path,'evenodd');g.strokeStyle='rgba(23,32,51,.20)';g.lineWidth=1.5;g.stroke(path);});d.line(cx-w*.29,top+h*.30,cx+w*.29,top+h*.30,{color:accent,width:6,alpha:.50});
}
function steps(d,x,base,w,h,{accent=GOLD}={}){
  for(let i=0;i<4;i++){const u=i/3,tw=w*(1-u*.13),th=h/4,ty=base-i*th,tx=x+i*w*.08;poly(d,[[tx,ty],[tx+tw,ty],[tx+tw+30,ty-14],[tx+30,ty-14]],{fill:i%2?FLOOR2:'#e7decf',stroke:'rgba(23,32,51,.16)',shadow:.12});poly(d,[[tx,ty],[tx+tw,ty],[tx+tw,ty-th],[tx,ty-th]],{fill:'#d1c8b8',stroke:'rgba(23,32,51,.15)'});d.line(tx+18,ty-th+18,tx+tw*.78,ty-th+18,{color:accent,width:4,alpha:.32});}
}
function canopy(d,cx,base,w,h){const top=base-h;poly(d,[[cx-w*.38,base],[cx-w*.30,base],[cx-w*.22,top+h*.26],[cx-w*.30,top+h*.26]],{fill:'#c8c0b2'});poly(d,[[cx+w*.24,base],[cx+w*.32,base],[cx+w*.25,top+h*.26],[cx+w*.17,top+h*.26]],{fill:'#c8c0b2'});poly(d,[[cx-w*.52,top+h*.29],[cx,top],[cx+w*.52,top+h*.29],[cx,top+h*.42]],{fill:FLOOR2,stroke:'rgba(23,32,51,.20)',shadow:.20});poly(d,[[cx-w*.52,top+h*.29],[cx,top+h*.42],[cx,top+h*.50],[cx-w*.49,top+h*.37]],{fill:'#b8b1a5'});d.line(cx-w*.32,top+h*.25,cx+w*.32,top+h*.25,{color:BLUE,width:5,alpha:.44});}
function beacon(d,cx,base,w,h){const top=base-h;poly(d,[[cx-w/2,base],[cx+w/2,base],[cx+w*.32,top],[cx-w*.32,top]],{fill:'#e2d9c9',stroke:'rgba(23,32,51,.18)',shadow:.14});poly(d,[[cx+w/2,base],[cx+w/2+26,base-14],[cx+w*.32+24,top-14],[cx+w*.32,top]],{fill:'#bdb5a8'});d.line(cx-w*.20,top+44,cx+w*.18,top+44,{color:GOLD,width:5,alpha:.46});}
function bridgePoint(u){const a=[385,895],b=[1535,585];return [lerp(a[0],b[0],u),lerp(a[1],b[1],u)-Math.sin(u*Math.PI)*145];}
function bridge(d,{final=0}={}){
  const N=19;for(let i=0;i<N;i++){const u=i/(N-1);if(u>.45&&u<.57)continue;const p=bridgePoint(u),n=bridgePoint(Math.min(1,u+.025)),ang=Math.atan2(n[1]-p[1],n[0]-p[0]),sc=lerp(1.28,.70,u),w=136*sc,h=44*sc;d.save(()=>{d.g.translate(p[0],p[1]);d.g.rotate(ang);d.rrect(-w/2,-h/2,w,h,5,{fill:i%3===0?GOLD2:FLOOR2,stroke:'rgba(23,32,51,.20)',shadow:.24});d.line(-w*.30,0,w*.30,0,{color:i%3===0?GOLD:BLUE,width:3,alpha:.20});});}
  const pts=[];for(let i=0;i<=16;i++)pts.push(bridgePoint(i/16));curve(d,pts,{color:BLUE,width:5,alpha:.26});
  if(final>0){const p=bridgePoint(.51),n=bridgePoint(.535),ang=Math.atan2(n[1]-p[1],n[0]-p[0]);d.save(()=>{d.g.translate(p[0],p[1]);d.g.rotate(ang+lerp(-.78,0,easeOut(final)));d.rrect(-72*final,-27,144*final,54,6,{fill:'#fff8e4',stroke:BLUE,width:2,alpha:final,shadow:.40});d.line(-48*final,0,48*final,0,{color:GOLD,width:6,alpha:.68*final});});}
}
function routes(d){curve(d,[[170,1030],[455,870],[760,765],[1050,670],[1320,555],[1660,430]],{color:BLUE,width:8,alpha:.62});curve(d,[[1760,1015],[1510,870],[1240,785],[1035,705],[835,605],[655,510]],{color:GOLD,width:7,alpha:.54});}
function gptFold(d,k){if(k<=0)return;const pts=[[1970,805],[1690,760],[1450,732],[1225,714],[1075,706]];for(let i=0;i<pts.length-1;i++){const q=easeOut(prog(k,i*.12,.56+i*.12));if(q<=0)continue;const a=pts[i],b=pts[i+1],x=lerp(a[0],b[0],q),y=lerp(a[1],b[1],q),ang=Math.atan2(b[1]-a[1],b[0]-a[0]);d.save(()=>{d.g.translate(x,y);d.g.rotate(ang);const w=lerp(320,180,i/(pts.length-2));poly(d,[[-w/2,-34],[w/2,-24],[w/2,26],[-w/2,36]],{fill:i%2?BLUE2:BLUE,stroke:'rgba(18,28,44,.25)',shadow:.22});d.line(-w*.34,0,w*.34,0,{color:'#eef3ff',width:3,alpha:.34});});}}
function userFold(d,k){if(k<=0)return;const pts=[[-80,900],[230,845],[490,792],[760,744],[960,714]];for(let i=0;i<pts.length-1;i++){const q=easeOut(prog(k,i*.12,.56+i*.12));if(q<=0)continue;const a=pts[i],b=pts[i+1],x=lerp(a[0],b[0],q),y=lerp(a[1],b[1],q),ang=Math.atan2(b[1]-a[1],b[0]-a[0]);d.save(()=>{d.g.translate(x,y);d.g.rotate(ang);const w=lerp(300,170,i/(pts.length-2));poly(d,[[-w/2,-30],[w/2,-22],[w/2,24],[-w/2,32]],{fill:i%2?GOLD2:GOLD,stroke:'rgba(18,28,44,.20)',shadow:.20});});}}
function finalWorld(d,t){stage(d);routes(d);beacon(d,1510,575,125,240);canopy(d,1205,704,320,360);steps(d,610,845,330,390,{accent:GOLD});arch(d,315,930,470,610,{accent:BLUE});arch(d,945,770,300,390,{accent:GOLD,side:'#afa89d'});bridge(d,{final:easeOut(prog(t,T3+1.28,T3+2.45))});const g=easeOut(prog(t,T3+.32,T3+1.40)),u=easeOut(prog(t,T3+.46,T3+1.52));gptFold(d,g);userFold(d,u);const lock=easeOut(prog(t,T3+1.65,T3+2.72));if(lock>0){mark(d,1035,705,BLUE,.65*lock,7);mark(d,1035,705,GOLD,.58*lock,5);}steps(d,1540,1050,430,520,{accent:BLUE});const p=bridgePoint(.06);d.save(()=>{d.g.translate(p[0]-170,p[1]+135);d.g.rotate(-.18);d.rrect(-250,-48,500,96,8,{fill:'#cfc6b7',stroke:'rgba(23,32,51,.18)',shadow:.44});d.line(-190,0,190,0,{color:BLUE,width:5,alpha:.18});});const cap=easeOut(prog(t,T3+2.05,T3+3.05));d.text('keep building from here.',116,156,{size:38,font:'serif',italic:true,color:'#f4eee3',alpha:.58*cap});}
function handoff(d,t,model,poses){
  finalWorld(d,t);
  const q=prog(t,T3,T3+.62);if(q<=0||q>=1)return;const k=easeInOut(q),x=lerp(-900,2200,k);d.save(()=>{d.g.translate(x,530);d.g.rotate(-.13);d.rrect(-580,-94,1160,188,10,{fill:FLOOR2,stroke:'rgba(23,32,51,.20)',shadow:.52});d.line(-470,-22,460,-22,{color:BLUE,width:9,alpha:.42});d.line(-230,28,300,28,{color:GOLD,width:5,alpha:.28});});
}

export function renderConstructV4(d,t,model,poses){if(t<T3)return renderConstructV3(d,t,model,poses);return handoff(d,t,model,poses);}
export const CONSTRUCT_V4_CUTS=[30,33.05,36.10,T3,45];
